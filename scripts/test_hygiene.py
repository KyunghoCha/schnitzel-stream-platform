#!/usr/bin/env python3
# Docs: docs/implementation/testing_quality.md, docs/ops/command_reference.md
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class HygieneCase:
    test_id: str
    file_path: str
    line: int
    normalized_body_hash: str
    has_assert: bool
    has_raises: bool
    has_assert_call: bool
    trivial_assert_true: bool


class _NormalizeConstants(ast.NodeTransformer):
    """Normalize constants to reduce noise when comparing test bodies.

    Intent:
    - Detect near-duplicate test logic where only literal values differ.
    - Keep function/attribute names as-is to avoid over-grouping unrelated tests.
    """

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        return ast.copy_location(ast.Constant(value="CONST"), node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        return node


def _iter_test_functions(tree: ast.AST) -> Iterable[tuple[str, ast.FunctionDef]]:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            yield "", node
            continue
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                    yield node.name, child


def _has_pytest_raises(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            ctx = item.context_expr
            if not isinstance(ctx, ast.Call):
                continue
            func = ctx.func
            if isinstance(func, ast.Attribute) and func.attr == "raises":
                return True
            if isinstance(func, ast.Name) and func.id == "raises":
                return True
    return False


def _has_assert_call(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id.startswith("assert"):
            return True
        if isinstance(func, ast.Attribute) and func.attr.startswith("assert"):
            return True
    return False


def _is_trivial_assert_true(fn: ast.FunctionDef) -> bool:
    asserts = [node for node in ast.walk(fn) if isinstance(node, ast.Assert)]
    if not asserts:
        return False
    for node in asserts:
        if not isinstance(node.test, ast.Constant) or node.test.value is not True:
            return False
    return True


def _hash_normalized_body(fn: ast.FunctionDef) -> str:
    module = ast.Module(body=fn.body, type_ignores=[])
    normalized = _NormalizeConstants().visit(module)
    ast.fix_missing_locations(normalized)
    payload = ast.dump(normalized, include_attributes=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def collect_tests(tests_root: Path) -> list[HygieneCase]:
    out: list[HygieneCase] = []
    for path in sorted(tests_root.rglob("test_*.py")):
        rel = path.as_posix()
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue

        for class_name, fn in _iter_test_functions(tree):
            has_assert = any(isinstance(node, ast.Assert) for node in ast.walk(fn))
            has_raises = _has_pytest_raises(fn)
            has_assert_call = _has_assert_call(fn)
            trivial_assert_true = _is_trivial_assert_true(fn)
            test_id = f"{rel}::{fn.name}" if not class_name else f"{rel}::{class_name}::{fn.name}"
            out.append(
                HygieneCase(
                    test_id=test_id,
                    file_path=rel,
                    line=fn.lineno,
                    normalized_body_hash=_hash_normalized_body(fn),
                    has_assert=has_assert,
                    has_raises=has_raises,
                    has_assert_call=has_assert_call,
                    trivial_assert_true=trivial_assert_true,
                )
            )
    return out


def build_report(cases: list[HygieneCase], show_top: int) -> dict:
    groups: dict[str, list[HygieneCase]] = defaultdict(list)
    for case in cases:
        groups[case.normalized_body_hash].append(case)

    duplicate_groups = [
        sorted(group, key=lambda item: item.test_id)
        for group in groups.values()
        if len(group) > 1
    ]
    duplicate_groups.sort(key=len, reverse=True)

    no_assert_cases = sorted(
        [
            case
            for case in cases
            if not case.has_assert and not case.has_raises and not case.has_assert_call
        ],
        key=lambda item: item.test_id,
    )
    trivial_cases = sorted(
        [case for case in cases if case.trivial_assert_true],
        key=lambda item: item.test_id,
    )

    visible_duplicate_groups = duplicate_groups[: max(0, show_top)]
    duplicate_payload = [
        {
            "size": len(group),
            "tests": [item.test_id for item in group],
        }
        for group in visible_duplicate_groups
    ]

    return {
        "summary": {
            "tests_total": len(cases),
            "duplicate_groups_total": len(duplicate_groups),
            "duplicate_tests_total": sum(len(group) for group in duplicate_groups),
            "no_assert_tests_total": len(no_assert_cases),
            "trivial_assert_true_total": len(trivial_cases),
            "duplicate_groups_shown": len(visible_duplicate_groups),
        },
        "duplicate_groups": duplicate_payload,
        "no_assert_tests": [item.test_id for item in no_assert_cases],
        "trivial_assert_true_tests": [item.test_id for item in trivial_cases],
    }


def print_report(report: dict) -> None:
    summary = report["summary"]
    print("== Test Hygiene Report ==")
    print(f"tests_total={summary['tests_total']}")
    print(f"duplicate_groups_total={summary['duplicate_groups_total']}")
    print(f"duplicate_tests_total={summary['duplicate_tests_total']}")
    print(f"no_assert_tests_total={summary['no_assert_tests_total']}")
    print(f"trivial_assert_true_total={summary['trivial_assert_true_total']}")

    if report["duplicate_groups"]:
        print("\n[duplicate_groups]")
        for group in report["duplicate_groups"]:
            print(f"- size={group['size']}")
            for test_id in group["tests"]:
                print(f"  - {test_id}")

    if report["no_assert_tests"]:
        print("\n[no_assert_tests]")
        for test_id in report["no_assert_tests"]:
            print(f"- {test_id}")

    if report["trivial_assert_true_tests"]:
        print("\n[trivial_assert_true_tests]")
        for test_id in report["trivial_assert_true_tests"]:
            print(f"- {test_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static test hygiene checker (duplicates/meaningless tests)",
    )
    parser.add_argument(
        "--tests-root",
        default="tests",
        help="root directory containing pytest tests (default: tests)",
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=20,
        help="number of duplicate groups to print (default: 20)",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="optional json output path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when hygiene issues are found",
    )
    parser.add_argument(
        "--max-duplicate-groups",
        type=int,
        default=0,
        help="strict threshold for duplicate groups (default: 0)",
    )
    parser.add_argument(
        "--max-no-assert",
        type=int,
        default=0,
        help="strict threshold for no-assert tests (default: 0)",
    )
    parser.add_argument(
        "--max-trivial-assert-true",
        type=int,
        default=0,
        help="strict threshold for trivial 'assert True' tests (default: 0)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tests_root = Path(args.tests_root)
    if not tests_root.exists():
        print(f"tests root not found: {tests_root}", file=sys.stderr)
        return 2

    cases = collect_tests(tests_root)
    report = build_report(cases, show_top=max(0, args.show_top))
    print_report(report)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\njson_report={out_path}")

    if args.strict:
        summary = report["summary"]
        if summary["duplicate_groups_total"] > args.max_duplicate_groups:
            return 1
        if summary["no_assert_tests_total"] > args.max_no_assert:
            return 1
        if summary["trivial_assert_true_total"] > args.max_trivial_assert_true:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
