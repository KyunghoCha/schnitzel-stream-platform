#!/usr/bin/env python3
# Docs: docs/guides/plugin_authoring_guide.md, docs/implementation/plugin_packs.md, docs/ops/command_reference.md
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
SCHEMA_VERSION = 1

_ALL_BLOCK_RE = re.compile(r"(?ms)^__all__\s*=\s*\[(?P<body>.*?)\]\s*$")
_INIT_IMPORT_RE = re.compile(r"(?m)^from\s+\.(?P<module>[A-Za-z0-9_]+)\s+import\s+(?P<name>[A-Za-z0-9_]+)\s*$")
_GRAPH_PLUGIN_RE = re.compile(r"(?m)^\s*plugin:\s*['\"]?(?P<plugin>[^'\"\s]+)['\"]?\s*$")
_GRAPH_VALIDATE_INLINE = """
from __future__ import annotations
import pathlib
import sys

repo_root = pathlib.Path(sys.argv[1]).resolve()
graph_path = pathlib.Path(sys.argv[2]).resolve()
extra_pkg_root = repo_root / "src" / "schnitzel_stream"

if extra_pkg_root.exists():
    import schnitzel_stream
    extra_pkg = str(extra_pkg_root)
    if extra_pkg not in schnitzel_stream.__path__:
        schnitzel_stream.__path__.append(extra_pkg)

    import schnitzel_stream.packs as packs_pkg
    extra_packs = str(extra_pkg_root / "packs")
    if extra_packs not in packs_pkg.__path__:
        packs_pkg.__path__.append(extra_packs)

from schnitzel_stream.cli.__main__ import main
sys.argv = ["schnitzel_stream", "validate", "--graph", str(graph_path)]
raise SystemExit(main())
""".strip()


def _snake_case(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def _script_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_root(raw: str) -> Path:
    p = Path(str(raw or "."))
    return p.resolve()


def _resolve_graph_path(*, graph: str, repo_root: Path) -> Path:
    p = Path(str(graph).strip())
    if p.is_absolute():
        return p
    cwd_candidate = Path.cwd() / p
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    return (repo_root / p).resolve()


def _build_validation_env(*, repo_root: Path, current_repo_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    merged: list[str] = [str((repo_root / "src").resolve()), str((current_repo_root / "src").resolve())]
    existing = str(env.get("PYTHONPATH", "") or "").strip()
    if existing:
        merged.append(existing)

    deduped: list[str] = []
    seen: set[str] = set()
    for raw in merged:
        for token in str(raw).split(os.pathsep):
            val = str(token).strip()
            if not val or val in seen:
                continue
            seen.add(val)
            deduped.append(val)
    env["PYTHONPATH"] = os.pathsep.join(deduped)
    return env


def _run_subprocess(*, cmd: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _tail(text: str, *, lines: int = 20) -> str:
    chunks = str(text or "").splitlines()
    if not chunks:
        return ""
    return "\n".join(chunks[-lines:])


def _ensure_import_overlay(*, repo_root: Path, current_repo_root: Path) -> None:
    repo_src = str((repo_root / "src").resolve())
    current_src = str((current_repo_root / "src").resolve())
    if repo_src not in sys.path:
        sys.path.insert(0, repo_src)
    if current_src not in sys.path:
        sys.path.insert(1, current_src)

    try:
        import schnitzel_stream  # type: ignore

        extra_pkg = str((repo_root / "src" / "schnitzel_stream").resolve())
        if extra_pkg not in schnitzel_stream.__path__:
            schnitzel_stream.__path__.append(extra_pkg)

        import schnitzel_stream.packs as packs_pkg  # type: ignore

        extra_packs = str((repo_root / "src" / "schnitzel_stream" / "packs").resolve())
        if extra_packs not in packs_pkg.__path__:
            packs_pkg.__path__.append(extra_packs)
    except Exception:
        # Intent: import overlay should be best-effort and never abort contract checks by itself.
        return


def _parse_init_exports(init_file: Path) -> tuple[dict[str, set[str]], set[str]]:
    text = init_file.read_text(encoding="utf-8")
    module_exports: dict[str, set[str]] = {}
    for match in _INIT_IMPORT_RE.finditer(text):
        mod = str(match.group("module") or "").strip()
        name = str(match.group("name") or "").strip()
        if not mod or not name:
            continue
        module_exports.setdefault(mod, set()).add(name)

    all_names: set[str] = set()
    block = _ALL_BLOCK_RE.search(text)
    if block:
        all_names = {x.strip() for x in re.findall(r"['\"]([^'\"]+)['\"]", block.group("body")) if x.strip()}
    return module_exports, all_names


def _extract_graph_plugins(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [str(m.group("plugin")).strip() for m in _GRAPH_PLUGIN_RE.finditer(text) if str(m.group("plugin")).strip()]


def _resolve_plugin_class(plugin_path: str) -> tuple[bool, str]:
    txt = str(plugin_path or "").strip()
    if ":" not in txt:
        return False, f"invalid plugin path (module:Class required): {txt}"
    module_name, class_name = txt.split(":", 1)
    module_name = str(module_name).strip()
    class_name = str(class_name).strip()
    if not module_name or not class_name:
        return False, f"invalid plugin path (empty module/class): {txt}"
    try:
        mod = importlib.import_module(module_name)
    except Exception as exc:
        return False, f"module import failed: {module_name} ({exc})"
    obj = getattr(mod, class_name, None)
    if obj is None:
        return False, f"class not found: {module_name}:{class_name}"
    return True, f"resolved: {module_name}:{class_name}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check plugin pack contract and scaffold integrity")
    parser.add_argument("--pack", required=True, help="Pack name to check (for example: sensor)")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--module", default="", help="Plugin module name without .py")
    parser.add_argument("--class", dest="class_name", default="", help="Plugin class name")
    parser.add_argument("--graph", default="", help="Graph path to validate with plugin checks")
    parser.add_argument("--strict", action="store_true", help="Enable strict contract checks")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _resolve_repo_root(args.repo_root)
    current_repo_root = _script_repo_root()
    pack = _snake_case(str(args.pack))
    module = _snake_case(str(args.module).strip()) if str(args.module or "").strip() else ""
    class_name = str(args.class_name or "").strip()
    graph_raw = str(args.graph or "").strip()
    strict = bool(args.strict)

    if class_name and not module:
        print("Error: --class requires --module", file=sys.stderr)
        return EXIT_USAGE

    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    def _record(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"id": check_id, "ok": bool(ok), "detail": str(detail)})
        if not ok:
            errors.append(f"{check_id}: {detail}")

    pack_root = repo_root / "src" / "schnitzel_stream" / "packs" / pack
    nodes_dir = pack_root / "nodes"
    init_file = nodes_dir / "__init__.py"
    _record("pack.path", nodes_dir.exists(), f"nodes_dir={nodes_dir}")

    module_exports: dict[str, set[str]] = {}
    all_exports: set[str] = set()
    if init_file.exists():
        module_exports, all_exports = _parse_init_exports(init_file)
        _record("pack.init.exists", True, f"init_file={init_file}")
    else:
        _record("pack.init.exists", False, f"missing init file: {init_file}")

    _ensure_import_overlay(repo_root=repo_root, current_repo_root=current_repo_root)

    if module:
        module_path = f"schnitzel_stream.packs.{pack}.nodes.{module}"
        try:
            imported_mod = importlib.import_module(module_path)
            _record("module.import", True, f"imported {module_path}")
        except Exception as exc:
            imported_mod = None
            _record("module.import", False, f"{module_path} import failed: {exc}")

        if class_name:
            if imported_mod is None:
                _record("class.import", False, f"cannot resolve class without imported module: {class_name}")
            else:
                target = getattr(imported_mod, class_name, None)
                _record("class.import", target is not None, f"class={class_name}")

            expected_import = class_name in module_exports.get(module, set())
            _record("init.import", expected_import, f"from .{module} import {class_name}")
            in_all = class_name in all_exports
            _record("init.all", in_all, f"__all__ contains {class_name}")

    if graph_raw:
        graph_path = _resolve_graph_path(graph=graph_raw, repo_root=repo_root)
        if not graph_path.exists():
            _record("graph.exists", False, f"graph not found: {graph_path}")
        else:
            _record("graph.exists", True, f"graph={graph_path}")
            plugins = _extract_graph_plugins(graph_path)
            expected_plugin = f"schnitzel_stream.packs.{pack}.nodes.{module}:{class_name}" if module and class_name else ""
            if expected_plugin:
                _record("graph.plugin.match", expected_plugin in plugins, f"expected={expected_plugin}")

            env = _build_validation_env(repo_root=repo_root, current_repo_root=current_repo_root)
            cmd = [sys.executable, "-c", _GRAPH_VALIDATE_INLINE, str(repo_root), str(graph_path)]
            result = _run_subprocess(cmd=cmd, cwd=current_repo_root, env=env)
            if int(result.returncode) == 0:
                _record("graph.validate", True, f"validated {graph_path}")
            else:
                _record("graph.validate", False, _tail(result.stderr) or _tail(result.stdout) or "validate failed")

    if strict and nodes_dir.exists():
        if not init_file.exists():
            _record("strict.init.required", False, f"strict mode requires init file: {init_file}")
        else:
            node_modules = sorted(p.stem for p in nodes_dir.glob("*.py") if p.name != "__init__.py")
            for mod in node_modules:
                exported = bool(module_exports.get(mod))
                _record("strict.module.export", exported, f"module={mod}")
            for mod, class_set in sorted(module_exports.items()):
                for name in sorted(class_set):
                    _record("strict.all.sync", name in all_exports, f"{mod}:{name}")

        prefix = f"schnitzel_stream.packs.{pack}.nodes."
        graph_files = sorted((repo_root / "configs" / "graphs").glob(f"dev_{pack}_*_v2.yaml"))
        _record("strict.graph.discovery", True, f"graph_count={len(graph_files)}")
        for graph_file in graph_files:
            plugins = _extract_graph_plugins(graph_file)
            targeted = [p for p in plugins if p.startswith(prefix)]
            if not targeted:
                _record("strict.graph.plugin_ref", True, f"{graph_file.name}: no pack plugin reference")
                continue
            unresolved: list[str] = []
            for plugin_path in targeted:
                ok, _ = _resolve_plugin_class(plugin_path)
                if not ok:
                    unresolved.append(plugin_path)
            if unresolved:
                _record("strict.graph.plugin_ref", False, f"{graph_file.name}: unresolved={','.join(unresolved)}")
            else:
                _record("strict.graph.plugin_ref", True, f"{graph_file.name}: resolved {len(targeted)}")

    status = "ok" if not errors else "failed"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "pack": pack,
        "repo_root": str(repo_root),
        "checks": checks,
        "errors": errors,
    }

    if bool(args.json):
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    else:
        print(f"pack={pack} status={status}")
        for item in checks:
            mark = "OK" if bool(item["ok"]) else "FAIL"
            print(f"[{mark}] {item['id']} - {item['detail']}")
        if errors:
            print("errors:")
            for err in errors:
                print(f"- {err}")

    return EXIT_OK if not errors else EXIT_FAILED


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
