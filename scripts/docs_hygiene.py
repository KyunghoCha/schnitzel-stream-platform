#!/usr/bin/env python3
# Docs: docs/governance/documentation_policy.md, docs/reference/document_inventory.md
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


LAST_UPDATED_RE = re.compile(r"^Last updated: \d{4}-\d{2}-\d{2}$", re.MULTILINE)
DOCS_PATH_RE = re.compile(r"docs/[A-Za-z0-9_./-]+\.md")
FORBIDDEN_LEGACY_PATH_RE = re.compile(r"\blegacy/(docs|scripts|ai)\b")


@dataclass(frozen=True)
class Issue:
    kind: str
    path: str
    detail: str


def _iter_md_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if path.is_file():
            yield path


def _iter_py_files(root: Path) -> Iterable[Path]:
    for rel in ("scripts", "src"):
        base = root / rel
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if path.is_file():
                yield path


def _check_last_updated(md_path: Path, text: str, out: list[Issue], *, root: Path) -> None:
    if LAST_UPDATED_RE.search(text):
        return
    out.append(Issue("missing_last_updated", str(md_path.relative_to(root)), "Last updated header not found"))


def _check_bilingual_headers(md_path: Path, text: str, out: list[Issue], *, root: Path) -> None:
    en = text.find("## English")
    ko = text.find("## 한국어")
    rel = str(md_path.relative_to(root))
    if en < 0 or ko < 0:
        out.append(Issue("missing_bilingual_header", rel, "Both `## English` and `## 한국어` are required"))
        return
    if en > ko:
        out.append(Issue("bilingual_header_order", rel, "`## English` must appear before `## 한국어`"))


def _check_no_legacy_paths(path: Path, text: str, out: list[Issue], *, root: Path) -> None:
    for match in FORBIDDEN_LEGACY_PATH_RE.finditer(text):
        rel = str(path.relative_to(root))
        out.append(Issue("forbidden_legacy_path", rel, f"Forbidden path reference: {match.group(0)}"))


def _check_docs_paths(path: Path, text: str, out: list[Issue], *, root: Path) -> None:
    rel = str(path.relative_to(root))
    for m in DOCS_PATH_RE.finditer(text):
        doc_rel = m.group(0)
        if not (root / doc_rel).exists():
            out.append(Issue("broken_docs_reference", rel, f"Referenced doc does not exist: {doc_rel}"))


def run_checks(*, repo_root: Path, docs_root: Path, require_last_updated: bool) -> list[Issue]:
    issues: list[Issue] = []

    for md_path in _iter_md_files(docs_root):
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        if require_last_updated:
            _check_last_updated(md_path, text, issues, root=repo_root)
        _check_bilingual_headers(md_path, text, issues, root=repo_root)
        _check_no_legacy_paths(md_path, text, issues, root=repo_root)
        _check_docs_paths(md_path, text, issues, root=repo_root)

    for py_path in _iter_py_files(repo_root):
        text = py_path.read_text(encoding="utf-8", errors="ignore")
        _check_no_legacy_paths(py_path, text, issues, root=repo_root)
        _check_docs_paths(py_path, text, issues, root=repo_root)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Documentation hygiene checks")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--docs-root", default="docs", help="Documentation root path")
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero status if any issue is found")
    parser.add_argument(
        "--require-last-updated",
        action="store_true",
        help="Require `Last updated: YYYY-MM-DD` in every markdown doc",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_root = (repo_root / args.docs_root).resolve()

    if not docs_root.exists():
        print(f"docs root not found: {docs_root}", file=sys.stderr)
        return 2

    issues = run_checks(
        repo_root=repo_root,
        docs_root=docs_root,
        require_last_updated=bool(args.require_last_updated),
    )
    payload = {
        "summary": {
            "issues_total": len(issues),
        },
        "issues": [issue.__dict__ for issue in issues],
    }

    print("== Docs Hygiene Report ==")
    print(f"issues_total={len(issues)}")
    for issue in issues:
        print(f"- [{issue.kind}] {issue.path}: {issue.detail}")

    if args.json_out:
        out_path = Path(args.json_out)
        if not out_path.is_absolute():
            out_path = repo_root / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"json_report={out_path}")

    if args.strict and issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
