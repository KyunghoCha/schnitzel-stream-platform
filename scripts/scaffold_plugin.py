#!/usr/bin/env python3
# Docs: docs/guides/plugin_authoring_guide.md, docs/implementation/plugin_packs.md
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


def _snake_case(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def _normalize_kind(raw: str) -> str:
    val = str(raw or "").strip().lower()
    if val not in {"source", "node", "sink"}:
        raise ValueError("--kind must be one of: source, node, sink")
    return val


def _parse_kinds(raw: str) -> list[str]:
    txt = str(raw or "*").strip()
    if not txt:
        return ["*"]
    out = [x.strip() for x in txt.split(",") if x.strip()]
    return out or ["*"]


@dataclass(frozen=True)
class ScaffoldPaths:
    plugin_file: Path
    test_file: Path
    graph_file: Path


_ALL_BLOCK_RE = re.compile(r"(?ms)^__all__\s*=\s*\[(?P<body>.*?)\]\s*$")


def _build_paths(repo_root: Path, *, pack: str, module: str) -> ScaffoldPaths:
    plugin_file = repo_root / "src" / "schnitzel_stream" / "packs" / pack / "nodes" / f"{module}.py"
    test_file = repo_root / "tests" / "unit" / "packs" / pack / "nodes" / f"test_{module}.py"
    graph_file = repo_root / "configs" / "graphs" / f"dev_{pack}_{module}_v2.yaml"
    return ScaffoldPaths(plugin_file=plugin_file, test_file=test_file, graph_file=graph_file)


def _render_plugin(*, kind: str, class_name: str, input_kinds: list[str], output_kinds: list[str]) -> str:
    base = [
        "from __future__ import annotations",
        "",
        "from typing import Any, Iterable",
        "",
        "from schnitzel_stream.packet import StreamPacket",
        "",
        "",
        f"class {class_name}:",
        "    # Intent: scaffold baseline for plugin authors; replace placeholder behavior before production use.",
    ]

    if kind in {"node", "sink"}:
        base.append(f"    INPUT_KINDS = {set(input_kinds)}")
    if kind in {"source", "node"}:
        base.append(f"    OUTPUT_KINDS = {set(output_kinds)}")

    base.extend(
        [
            "",
            "    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:",
            "        self.node_id = str(node_id or \"scaffold\")",
            "        self.config = dict(config or {})",
        ]
    )

    if kind == "source":
        base.extend(
            [
                "",
                "    def run(self) -> Iterable[StreamPacket]:",
                "        return []",
            ]
        )
    elif kind == "node":
        base.extend(
            [
                "",
                "    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:",
                "        return [packet]",
            ]
        )
    else:
        base.extend(
            [
                "",
                "    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:",
                "        return []",
            ]
        )

    base.extend(
        [
            "",
            "    def close(self) -> None:",
            "        return",
            "",
        ]
    )
    return "\n".join(base)


def _render_test(*, kind: str, pack: str, module: str, class_name: str) -> str:
    import_path = f"schnitzel_stream.packs.{pack}.nodes.{module}"

    lines = [
        "from __future__ import annotations",
        "",
        f"from {import_path} import {class_name}",
        "from schnitzel_stream.packet import StreamPacket",
        "",
        "",
        f"def test_{module}_scaffold_smoke():",
        f"    plugin = {class_name}(node_id=\"n1\", config={{}})",
    ]

    if kind == "source":
        lines.extend(
            [
                "    out = list(plugin.run())",
                "    assert out == []",
            ]
        )
    else:
        lines.extend(
            [
                "    packet = StreamPacket.new(kind=\"demo\", source_id=\"s1\", payload={\"ok\": True})",
                "    out = list(plugin.process(packet))",
                "    assert isinstance(out, list)",
            ]
        )

    lines.extend(
        [
            "    plugin.close()",
            "",
        ]
    )
    return "\n".join(lines)


def _render_graph(*, kind: str, pack: str, module: str, class_name: str) -> str:
    plugin = f"schnitzel_stream.packs.{pack}.nodes.{module}:{class_name}"

    if kind == "source":
        return (
            "version: 2\n"
            "nodes:\n"
            "  - id: src\n"
            "    kind: source\n"
            f"    plugin: {plugin}\n"
            "    config: {}\n"
            "\n"
            "  - id: out\n"
            "    kind: sink\n"
            "    plugin: schnitzel_stream.nodes.dev:PrintSink\n"
            "    config:\n"
            "      prefix: \"SCAFFOLD \"\n"
            "\n"
            "edges:\n"
            "  - from: src\n"
            "    to: out\n"
            "\n"
            "config: {}\n"
        )

    if kind == "node":
        return (
            "version: 2\n"
            "nodes:\n"
            "  - id: src\n"
            "    kind: source\n"
            "    plugin: schnitzel_stream.nodes.dev:StaticSource\n"
            "    config:\n"
            "      packets:\n"
            "        - kind: demo\n"
            "          source_id: demo01\n"
            "          payload: { msg: hello }\n"
            "\n"
            "  - id: op\n"
            "    kind: node\n"
            f"    plugin: {plugin}\n"
            "    config: {}\n"
            "\n"
            "  - id: out\n"
            "    kind: sink\n"
            "    plugin: schnitzel_stream.nodes.dev:PrintSink\n"
            "    config:\n"
            "      prefix: \"SCAFFOLD \"\n"
            "\n"
            "edges:\n"
            "  - from: src\n"
            "    to: op\n"
            "  - from: op\n"
            "    to: out\n"
            "\n"
            "config: {}\n"
        )

    return (
        "version: 2\n"
        "nodes:\n"
        "  - id: src\n"
        "    kind: source\n"
        "    plugin: schnitzel_stream.nodes.dev:StaticSource\n"
        "    config:\n"
        "      packets:\n"
        "        - kind: demo\n"
        "          source_id: demo01\n"
        "          payload: { msg: hello }\n"
        "\n"
        "  - id: out\n"
        "    kind: sink\n"
        f"    plugin: {plugin}\n"
        "    config: {}\n"
        "\n"
        "edges:\n"
        "  - from: src\n"
        "    to: out\n"
        "\n"
        "config: {}\n"
    )


def _write_file(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"already exists: {path} (use --force to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _format_all_block(names: list[str]) -> str:
    rows = "".join(f'    "{name}",\n' for name in names)
    return f"__all__ = [\n{rows}]\n"


def _register_export(nodes_dir: Path, *, module: str, class_name: str) -> None:
    init_file = nodes_dir / "__init__.py"
    import_line = f"from .{module} import {class_name}"

    if not init_file.exists():
        content = (
            "from __future__ import annotations\n\n"
            f"{import_line}\n\n"
            + _format_all_block([class_name])
        )
        init_file.write_text(content, encoding="utf-8")
        return

    text = init_file.read_text(encoding="utf-8")
    updated = text
    if import_line not in updated:
        if not updated.endswith("\n"):
            updated += "\n"
        updated += f"\n{import_line}\n"

    match = _ALL_BLOCK_RE.search(updated)
    if match:
        current = [x for x in re.findall(r"['\"]([^'\"]+)['\"]", match.group("body"))]
        if class_name not in current:
            current.append(class_name)
        block = _format_all_block(current)
        updated = updated[: match.start()] + block + updated[match.end() :]
    else:
        if not updated.endswith("\n"):
            updated += "\n"
        updated += "\n" + _format_all_block([class_name])

    init_file.write_text(updated, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate plugin scaffold (code + test + graph)")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--pack", required=True, help="Target pack name (e.g., vision, sensor, audio)")
    parser.add_argument("--kind", required=True, choices=("source", "node", "sink"), help="Plugin kind")
    parser.add_argument("--name", required=True, help="Plugin class name (e.g., TemperatureSource)")
    parser.add_argument("--module", default="", help="Module filename without .py (default: derived from class name)")
    parser.add_argument("--input-kinds", default="*", help="Comma-separated INPUT_KINDS for node/sink")
    parser.add_argument("--output-kinds", default="*", help="Comma-separated OUTPUT_KINDS for source/node")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--register-export",
        dest="register_export",
        action="store_true",
        help="Register generated class in pack nodes/__init__.py (default: on)",
    )
    group.add_argument(
        "--no-register-export",
        dest="register_export",
        action="store_false",
        help="Skip nodes/__init__.py export registration",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold files")
    parser.set_defaults(register_export=True)
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    kind = _normalize_kind(args.kind)
    class_name = str(args.name).strip()
    if not class_name or not class_name[0].isalpha():
        print("Error: --name must start with an alphabetic character", file=sys.stderr)
        return 2

    pack = _snake_case(args.pack)
    module = _snake_case(args.module) if args.module else _snake_case(class_name)
    input_kinds = _parse_kinds(args.input_kinds)
    output_kinds = _parse_kinds(args.output_kinds)

    paths = _build_paths(repo_root, pack=pack, module=module)

    try:
        _write_file(
            paths.plugin_file,
            _render_plugin(kind=kind, class_name=class_name, input_kinds=input_kinds, output_kinds=output_kinds),
            force=args.force,
        )
        _write_file(paths.test_file, _render_test(kind=kind, pack=pack, module=module, class_name=class_name), force=args.force)
        _write_file(
            paths.graph_file,
            _render_graph(kind=kind, pack=pack, module=module, class_name=class_name),
            force=args.force,
        )
        if bool(args.register_export):
            # Intent: make generated plugin discoverable from pack namespace without manual export wiring.
            _register_export(paths.plugin_file.parent, module=module, class_name=class_name)
    except FileExistsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"generated plugin: {paths.plugin_file}")
    print(f"generated test: {paths.test_file}")
    print(f"generated graph: {paths.graph_file}")
    print("example plugin path: " f"schnitzel_stream.packs.{pack}.nodes.{module}:{class_name}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
