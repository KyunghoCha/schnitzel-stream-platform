#!/usr/bin/env python3
# Docs: docs/roadmap/execution_roadmap.md, docs/progress/current_status.md, PROMPT.md, PROMPT_CORE.md, docs/roadmap/owner_split_playbook.md
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2
SCHEMA_VERSION = 1
DEFAULT_BASELINE = "configs/policy/ssot_sync_snapshot_v1.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SSOT step/status sync drift")
    parser.add_argument("--strict", action="store_true", help="Enable strict sync checks")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    return parser.parse_args(argv)


def _resolve_path(value: str, *, root: Path) -> Path:
    p = Path(str(value).strip())
    if p.is_absolute():
        return p
    return (root / p).resolve()


def _load_baseline_config(*, root: Path) -> dict[str, Any]:
    baseline_path = _resolve_path(DEFAULT_BASELINE, root=root)
    if not baseline_path.exists():
        raise ValueError(f"baseline not found: {baseline_path}")
    try:
        payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid baseline JSON: {exc}") from exc

    if int(payload.get("schema_version", 0)) != 1:
        raise ValueError("baseline schema_version must be 1")
    if not isinstance(payload.get("documents"), dict) or not payload.get("documents"):
        raise ValueError("baseline documents mapping is required")
    if not isinstance(payload.get("patterns"), dict) or not payload.get("patterns"):
        raise ValueError("baseline patterns mapping is required")
    return payload


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_step_id(*, text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = str(match.group("step") or "").strip()
    return value or None


def _extract_execution_marker_step(*, text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = str(match.group("step") or "").strip()
    return value or None


def _check_roadmap_step_status(*, text: str, step_id: str) -> bool:
    # Intent: strict mode requires current step to be explicitly marked NOW or DONE in execution roadmap.
    escaped = re.escape(step_id)
    pattern = re.compile(rf"(?m)^-\s+`{escaped}`\s+.*`(?P<state>NOW|DONE)`\s*$")
    return bool(pattern.search(text))


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = _repo_root()

    try:
        baseline = _load_baseline_config(root=root)
        documents = dict(baseline["documents"])
        patterns = dict(baseline["patterns"])
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    step_pattern_raw = str(patterns.get("step_id", "")).strip()
    marker_pattern_raw = str(patterns.get("roadmap_current_position", "")).strip()
    if not step_pattern_raw or not marker_pattern_raw:
        print("Error: invalid baseline patterns (step_id/roadmap_current_position required)", file=sys.stderr)
        return EXIT_USAGE

    try:
        step_pattern = re.compile(step_pattern_raw, flags=re.MULTILINE | re.IGNORECASE)
        marker_pattern = re.compile(marker_pattern_raw, flags=re.MULTILINE | re.IGNORECASE)
    except re.error as exc:
        print(f"Error: invalid baseline regex ({exc})", file=sys.stderr)
        return EXIT_USAGE

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    step_ids: dict[str, str] = {}
    roadmap_text = ""

    def _record(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"id": check_id, "ok": bool(ok), "detail": str(detail)})
        if not ok:
            errors.append(f"{check_id}: {detail}")

    for alias, rel in documents.items():
        path = _resolve_path(str(rel), root=root)
        if not path.exists():
            _record("doc.exists", False, f"{alias} missing: {path}")
            continue

        text = _read_text(path)
        if alias == "execution_roadmap":
            roadmap_text = text

        step_id = _extract_step_id(text=text, pattern=step_pattern)
        if not step_id:
            _record("doc.step_id", False, f"{alias} missing step id marker: {path}")
            continue

        step_ids[str(alias)] = str(step_id)
        _record("doc.step_id", True, f"{alias}={step_id}")

    consensus = ""
    if step_ids:
        unique_steps = sorted(set(step_ids.values()))
        if len(unique_steps) == 1:
            consensus = unique_steps[0]
            _record("step.consensus", True, f"consensus={consensus}")
        else:
            _record("step.consensus", False, f"mismatch={unique_steps}")

    if bool(args.strict) and roadmap_text:
        marker = _extract_execution_marker_step(text=roadmap_text, pattern=marker_pattern)
        if not marker:
            _record("roadmap.current_position", False, "missing current position marker")
        else:
            _record("roadmap.current_position", True, f"marker={marker}")
            if consensus and marker != consensus:
                _record("roadmap.current_position.match", False, f"marker={marker}, consensus={consensus}")
            elif consensus:
                _record("roadmap.current_position.match", True, f"{marker}")

        if consensus:
            has_now_or_done = _check_roadmap_step_status(text=roadmap_text, step_id=consensus)
            _record(
                "roadmap.step_status",
                has_now_or_done,
                f"step={consensus} has explicit NOW/DONE status" if has_now_or_done else f"step={consensus} missing NOW/DONE status",
            )

    status = "ok" if not errors else "drift"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "step_id": consensus,
        "documents": step_ids,
        "checks": checks,
        "errors": errors,
    }

    if bool(args.json):
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    else:
        print(f"status={status}")
        if consensus:
            print(f"step_id={consensus}")
        for item in checks:
            mark = "OK" if bool(item["ok"]) else "FAIL"
            print(f"[{mark}] {item['id']} - {item['detail']}")
        if errors:
            print("errors:")
            for err in errors:
                print(f"- {err}")

    return EXIT_OK if not errors else EXIT_DRIFT


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
