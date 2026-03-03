#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
from typing import Any

from omegaconf import OmegaConf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

SCHEMA_VERSION = 1
DEFAULT_MATRIX = "configs/experiments/backpressure_fairness/final_matrix_v1.yaml"
DEFAULT_ANALYSIS = "configs/experiments/backpressure_fairness/analysis_spec_v1.yaml"
DEFAULT_OUT_ROOT = "outputs/experiments/backpressure_fairness/paper_submission_v1"
DEFAULT_PAPER_ROOT = "docs/paper/backpressure_fairness"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = OmegaConf.load(path)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"yaml must be a mapping: {path}")
    return dict(cont)


def _as_dict(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def _as_list(raw: Any) -> list[Any]:
    return list(raw) if isinstance(raw, list) else []


def _as_int(raw: Any, *, default: int, minimum: int | None = None) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = int(default)
    if minimum is not None and value < int(minimum):
        return int(minimum)
    return int(value)


def _as_float(raw: Any, *, default: float) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def _json_from_stdout(stdout: str) -> dict[str, Any] | None:
    txt = str(stdout or "").strip()
    if not txt:
        return None
    try:
        obj = json.loads(txt)
    except json.JSONDecodeError:
        return None
    return dict(obj) if isinstance(obj, dict) else None


def _run_cmd(*, cmd: list[str], cwd: Path, name: str, env: dict[str, str]) -> dict[str, Any]:
    started = _utc_now_iso()
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True)
    finished = _utc_now_iso()
    out = _json_from_stdout(proc.stdout)
    return {
        "name": name,
        "cmd": cmd,
        "started": started,
        "finished": finished,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "json": out,
    }


def _latest_session(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    sessions = sorted([p for p in base_dir.glob("session_*") if p.is_dir()])
    return sessions[-1] if sessions else None


def _validate_output_contract(payload: dict[str, Any], *, required_keys: list[str]) -> list[str]:
    missing = []
    for key in required_keys:
        if key not in payload:
            missing.append(str(key))
    return missing


def _write_repro_commands(path: Path, commands: list[list[str]]) -> None:
    lines = [
        "# Repro Commands",
        "",
        f"- Generated at: `{_utc_now_iso()}`",
        "",
        "## Commands",
    ]
    for cmd in commands:
        joined = " ".join(str(x) for x in cmd)
        lines.append(f"- `{joined}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_submission_checklist(path: Path, *, artifacts: dict[str, Any], quality: dict[str, Any]) -> None:
    def _mark(ok: bool) -> str:
        return "[x]" if ok else "[ ]"

    agg = Path(str(artifacts.get("aggregate_json", "")))
    tables = Path(str(artifacts.get("research_tables", "")))
    latex_manifest = Path(str(artifacts.get("latex_manifest", "")))
    ros2_json = str(artifacts.get("ros2_comparison_json", "")).strip()

    lines = [
        "# Submission Checklist",
        "",
        f"- Generated at: `{_utc_now_iso()}`",
        "",
        "## Artifact Gates",
        f"- {_mark(agg.exists())} aggregate json exists",
        f"- {_mark(tables.exists())} markdown research tables exists",
        f"- {_mark(latex_manifest.exists())} latex table manifest exists",
        f"- {_mark(bool(ros2_json))} ros2 appendix comparison available (optional by policy)",
        "",
        "## Quality Gates",
        f"- {_mark(bool(quality.get('required_tests_ok', False)))} required unit tests",
        f"- {_mark(bool(quality.get('docs_hygiene_ok', False)))} docs hygiene strict",
        f"- {_mark(bool(quality.get('full_pytest_ok', False) or quality.get('profile') != 'full'))} full pytest when profile=full",
        f"- {_mark(str(quality.get('latex_compile_status', 'skipped')) in {'ok', 'skipped'})} latex compile check (2 passes or explicit skip)",
        f"- {_mark(bool(quality.get('contract_ok', False)))} schema contract checks",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full paper-grade backpressure fairness pipeline")
    parser.add_argument("--matrix", default=DEFAULT_MATRIX, help="final matrix yaml path")
    parser.add_argument("--analysis-spec", default="", help="analysis spec yaml override")
    parser.add_argument("--out-root", default="", help="pipeline output root override")
    parser.add_argument("--paper-root", default=DEFAULT_PAPER_ROOT, help="paper tex root path")
    parser.add_argument("--quality-profile", choices=["none", "quick", "full"], default="", help="quality gate profile override")
    parser.add_argument("--max-runs", type=int, default=None, help="optional max run cap for quick execution")
    parser.add_argument("--skip-native-run", action="store_true", help="reuse latest native session in output root")
    parser.add_argument("--skip-ros2-compare", action="store_true", help="skip ros2 appendix comparison stage")
    parser.add_argument("--strict-native", action="store_true", help="force strict mode for benchmark run")
    parser.add_argument("--json", action="store_true", help="print manifest as json")
    parser.add_argument("--compact", action="store_true", help="compact json output")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    matrix_path = _resolve_path(args.matrix)
    if not matrix_path.exists():
        print(f"Error: matrix config not found: {matrix_path}", file=sys.stderr)
        return 2
    matrix = _load_yaml(matrix_path)

    analysis_path = _resolve_path(args.analysis_spec) if str(args.analysis_spec).strip() else _resolve_path(
        str(matrix.get("analysis_spec", DEFAULT_ANALYSIS))
    )
    if not analysis_path.exists():
        print(f"Error: analysis spec not found: {analysis_path}", file=sys.stderr)
        return 2
    analysis = _load_yaml(analysis_path)

    paths_cfg = _as_dict(matrix.get("paths"))
    exec_cfg = _as_dict(matrix.get("execution"))

    out_root = _resolve_path(args.out_root) if str(args.out_root).strip() else _resolve_path(
        str(paths_cfg.get("output_root", DEFAULT_OUT_ROOT))
    )
    out_root.mkdir(parents=True, exist_ok=True)

    native_out = out_root / "native"
    aggregate_out = out_root / "aggregate"
    plots_out = out_root / "plots"
    tables_out = out_root / "tables"
    ros2_out = out_root / "ros2_compare"
    package_out = out_root / "package"
    latex_tables_out = package_out / "latex_tables"
    paper_draft_root = package_out / "paper_draft"
    package_out.mkdir(parents=True, exist_ok=True)

    py = str(Path(sys.executable).resolve())
    env = dict(os.environ)
    existing_path = env.get("PYTHONPATH", "")
    src_path = str((PROJECT_ROOT / "src").resolve())
    env["PYTHONPATH"] = src_path if not existing_path else f"{src_path}{os.pathsep}{existing_path}"

    commands_executed: list[list[str]] = []
    stages: list[dict[str, Any]] = []

    policies = [str(x) for x in _as_list(matrix.get("policies")) if str(x).strip()]
    workloads = [str(x) for x in _as_list(matrix.get("workloads")) if str(x).strip()]
    if not policies or not workloads:
        print("Error: matrix must provide policies and workloads", file=sys.stderr)
        return 2

    repeats = _as_int(exec_cfg.get("repeats", 50), default=50, minimum=1)
    seed_base = _as_int(exec_cfg.get("seed_base", 12000), default=12000)
    strict_native = bool(exec_cfg.get("strict", False) or bool(args.strict_native))
    profile = str(args.quality_profile or exec_cfg.get("quality_profile", "full")).strip().lower()
    if profile not in {"none", "quick", "full"}:
        profile = "full"
    continue_on_ros2_missing = bool(exec_cfg.get("continue_on_ros2_missing", True))
    ros2_runs_glob = str(paths_cfg.get("ros2_runs_glob", "")).strip()
    max_runs = _as_int(args.max_runs if args.max_runs is not None else exec_cfg.get("max_runs", 0), default=0, minimum=0)

    native_session_dir: Path | None = None
    bench_json: dict[str, Any] | None = None
    if bool(args.skip_native_run):
        native_session_dir = _latest_session(native_out)
        if native_session_dir is None:
            print("Error: skip-native-run requested but no prior native session found", file=sys.stderr)
            return 2
    else:
        bench_cmd = [
            py,
            "scripts/experiments/run_backpressure_bench.py",
            "--base",
            str(matrix.get("base_config", "configs/experiments/backpressure_fairness/bench_base.yaml")),
            "--repeats",
            str(repeats),
            "--seed-base",
            str(seed_base),
            "--out-dir",
            str(native_out),
            "--json",
            "--compact",
        ]
        if max_runs > 0:
            bench_cmd.extend(["--max-runs", str(max_runs)])
        if strict_native:
            bench_cmd.append("--strict")
        for p in policies:
            bench_cmd.extend(["--policy", p])
        for w in workloads:
            bench_cmd.extend(["--workload", w])

        commands_executed.append(bench_cmd)
        bench_stage = _run_cmd(cmd=bench_cmd, cwd=PROJECT_ROOT, name="native_bench", env=env)
        stages.append(bench_stage)
        if bench_stage["returncode"] != 0:
            print(bench_stage["stderr"], file=sys.stderr)
            return 1
        bench_json = bench_stage.get("json") if isinstance(bench_stage.get("json"), dict) else None
        native_session_txt = str((bench_json or {}).get("session_dir", "")).strip()
        if not native_session_txt:
            print("Error: native bench json missing session_dir", file=sys.stderr)
            return 2
        native_session_dir = Path(native_session_txt).resolve()

    if native_session_dir is None:
        print("Error: failed to resolve native session dir", file=sys.stderr)
        return 2

    runs_glob = str((native_session_dir / "runs" / "*.json").resolve())

    alpha = _as_float(_as_dict(analysis.get("statistics")).get("alpha", 0.05), default=0.05)
    aggregate_cmd = [
        py,
        "scripts/experiments/aggregate_backpressure_results.py",
        "--runs-glob",
        runs_glob,
        "--out-dir",
        str(aggregate_out),
        "--alpha",
        str(alpha),
        "--json",
        "--compact",
    ]
    commands_executed.append(aggregate_cmd)
    agg_stage = _run_cmd(cmd=aggregate_cmd, cwd=PROJECT_ROOT, name="aggregate", env=env)
    stages.append(agg_stage)
    if agg_stage["returncode"] != 0:
        print(agg_stage["stderr"], file=sys.stderr)
        return 1
    agg_json = agg_stage.get("json") if isinstance(agg_stage.get("json"), dict) else {}
    aggregate_json_path = aggregate_out / "backpressure_aggregate.json"

    plot_cmd = [
        py,
        "scripts/experiments/plot_backpressure_results.py",
        "--aggregate-json",
        str(aggregate_json_path),
        "--out-dir",
        str(plots_out),
        "--json",
        "--compact",
    ]
    commands_executed.append(plot_cmd)
    plot_stage = _run_cmd(cmd=plot_cmd, cwd=PROJECT_ROOT, name="plots", env=env)
    stages.append(plot_stage)
    if plot_stage["returncode"] != 0:
        print(plot_stage["stderr"], file=sys.stderr)
        return 1

    table_cmd = [
        py,
        "scripts/experiments/build_research_tables.py",
        "--aggregate-json",
        str(aggregate_json_path),
        "--out-dir",
        str(tables_out),
        "--json",
        "--compact",
    ]
    commands_executed.append(table_cmd)
    table_stage = _run_cmd(cmd=table_cmd, cwd=PROJECT_ROOT, name="tables", env=env)
    stages.append(table_stage)
    if table_stage["returncode"] != 0:
        print(table_stage["stderr"], file=sys.stderr)
        return 1

    ros2_json_path = ros2_out / "ros2_comparison.json"
    ros2_stage_status = "skipped"
    if not bool(args.skip_ros2_compare):
        if not ros2_runs_glob:
            if not continue_on_ros2_missing:
                print("Error: ros2_runs_glob missing and continue_on_ros2_missing=false", file=sys.stderr)
                return 2
        else:
            ros2_cmd = [
                py,
                "scripts/experiments/compare_ros2_baseline.py",
                "--native-runs-glob",
                runs_glob,
                "--ros2-runs-glob",
                ros2_runs_glob,
                "--out-dir",
                str(ros2_out),
                "--json",
                "--compact",
            ]
            commands_executed.append(ros2_cmd)
            ros2_stage = _run_cmd(cmd=ros2_cmd, cwd=PROJECT_ROOT, name="ros2_compare", env=env)
            stages.append(ros2_stage)
            if ros2_stage["returncode"] == 0:
                ros2_stage_status = "ok"
            else:
                ros2_stage_status = "failed"
                if not continue_on_ros2_missing:
                    print(ros2_stage["stderr"], file=sys.stderr)
                    return 1

    latex_cmd = [
        py,
        "scripts/experiments/export_latex_tables.py",
        "--aggregate-json",
        str(aggregate_json_path),
        "--out-dir",
        str(latex_tables_out),
        "--json",
        "--compact",
    ]
    if ros2_json_path.exists():
        latex_cmd.extend(["--ros2-json", str(ros2_json_path)])
    commands_executed.append(latex_cmd)
    latex_stage = _run_cmd(cmd=latex_cmd, cwd=PROJECT_ROOT, name="latex_export", env=env)
    stages.append(latex_stage)
    if latex_stage["returncode"] != 0:
        print(latex_stage["stderr"], file=sys.stderr)
        return 1

    paper_root = _resolve_path(args.paper_root)
    if paper_root.exists():
        shutil.copytree(paper_root, paper_draft_root, dirs_exist_ok=True)
        draft_tables = paper_draft_root / "tables"
        draft_tables.mkdir(parents=True, exist_ok=True)
        for tex_file in sorted(latex_tables_out.glob("*.tex")):
            shutil.copy2(tex_file, draft_tables / tex_file.name)

    quality_result = {
        "profile": profile,
        "required_tests_ok": False,
        "docs_hygiene_ok": False,
        "full_pytest_ok": False,
        "latex_compile_status": "skipped",
        "contract_ok": False,
    }

    req_test_cmd = [
        py,
        "-m",
        "pytest",
        "-q",
        "tests/unit/test_inproc_backpressure.py",
        "tests/unit/scripts/test_backpressure_experiment_scripts.py",
    ]
    docs_cmd = [py, "scripts/docs_hygiene.py", "--strict"]
    full_pytest_cmd = [py, "-m", "pytest", "-q"]

    if profile in {"quick", "full"}:
        commands_executed.append(req_test_cmd)
        req_stage = _run_cmd(cmd=req_test_cmd, cwd=PROJECT_ROOT, name="quality_required_tests", env=env)
        stages.append(req_stage)
        quality_result["required_tests_ok"] = req_stage["returncode"] == 0

        commands_executed.append(docs_cmd)
        docs_stage = _run_cmd(cmd=docs_cmd, cwd=PROJECT_ROOT, name="quality_docs_hygiene", env=env)
        stages.append(docs_stage)
        quality_result["docs_hygiene_ok"] = docs_stage["returncode"] == 0

    if profile == "full":
        commands_executed.append(full_pytest_cmd)
        full_stage = _run_cmd(cmd=full_pytest_cmd, cwd=PROJECT_ROOT, name="quality_full_pytest", env=env)
        stages.append(full_stage)
        quality_result["full_pytest_ok"] = full_stage["returncode"] == 0
    else:
        quality_result["full_pytest_ok"] = True

    main_tex = paper_draft_root / "main.tex"
    pdflatex = shutil.which("pdflatex")
    if main_tex.exists() and pdflatex:
        latex_build_dir = package_out / "latex_build"
        latex_build_dir.mkdir(parents=True, exist_ok=True)
        latex_cmd_1 = [
            str(pdflatex),
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={latex_build_dir}",
            str(main_tex),
        ]
        commands_executed.append(latex_cmd_1)
        latex_stage_1 = _run_cmd(cmd=latex_cmd_1, cwd=PROJECT_ROOT, name="latex_compile_pass1", env=env)
        stages.append(latex_stage_1)
        if latex_stage_1["returncode"] != 0:
            quality_result["latex_compile_status"] = "failed"
        else:
            latex_cmd_2 = [
                str(pdflatex),
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={latex_build_dir}",
                str(main_tex),
            ]
            commands_executed.append(latex_cmd_2)
            latex_stage_2 = _run_cmd(cmd=latex_cmd_2, cwd=PROJECT_ROOT, name="latex_compile_pass2", env=env)
            stages.append(latex_stage_2)
            if latex_stage_2["returncode"] != 0:
                quality_result["latex_compile_status"] = "failed"
            else:
                log_path = latex_build_dir / "main.log"
                log_text = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""
                unresolved = ("undefined references" in log_text.lower()) or ("citation" in log_text.lower() and "undefined" in log_text.lower())
                quality_result["latex_compile_status"] = "ok" if not unresolved else "failed"
    elif main_tex.exists():
        quality_result["latex_compile_status"] = "skipped"

    required_contracts = _as_dict(_as_dict(analysis.get("quality_gates")).get("schema_requirements"))
    missing_agg = _validate_output_contract(agg_json, required_keys=[str(x) for x in _as_list(required_contracts.get("aggregate"))])

    missing_ros2: list[str] = []
    if ros2_json_path.exists():
        try:
            ros2_payload = json.loads(ros2_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ros2_payload = {}
        missing_ros2 = _validate_output_contract(
            ros2_payload if isinstance(ros2_payload, dict) else {},
            required_keys=[str(x) for x in _as_list(required_contracts.get("ros2_compare"))],
        )

    quality_result["contract_ok"] = (len(missing_agg) == 0 and len(missing_ros2) == 0)

    if profile in {"quick", "full"}:
        hard_ok = (
            bool(quality_result["required_tests_ok"])
            and bool(quality_result["docs_hygiene_ok"])
            and bool(quality_result["full_pytest_ok"])
            and str(quality_result["latex_compile_status"]) in {"ok", "skipped"}
            and bool(quality_result["contract_ok"])
        )
        if not hard_ok:
            print("Error: quality gates failed", file=sys.stderr)
            return 1

    artifacts = {
        "native_session_dir": str(native_session_dir),
        "aggregate_json": str(aggregate_json_path),
        "aggregate_csv": str(aggregate_out / "backpressure_summary.csv"),
        "pairwise_csv": str(aggregate_out / "backpressure_pairwise_tests.csv"),
        "plots_manifest": str(plots_out / "plots_manifest.json"),
        "research_tables": str(tables_out / "research_tables.md"),
        "tables_manifest": str(tables_out / "tables_manifest.json"),
        "ros2_comparison_json": str(ros2_json_path) if ros2_json_path.exists() else "",
        "latex_manifest": str(latex_tables_out / "latex_tables_manifest.json"),
        "paper_root": str(paper_root),
        "paper_draft_root": str(paper_draft_root),
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ts": _utc_now_iso(),
        "matrix": str(matrix_path),
        "analysis_spec": str(analysis_path),
        "out_root": str(out_root),
        "quality": quality_result,
        "contracts": {
            "missing_aggregate_keys": missing_agg,
            "missing_ros2_keys": missing_ros2,
        },
        "ros2_stage_status": ros2_stage_status,
        "artifacts": artifacts,
        "stages": [
            {
                "name": s.get("name"),
                "returncode": s.get("returncode"),
                "started": s.get("started"),
                "finished": s.get("finished"),
                "stderr_tail": str(s.get("stderr", ""))[-800:],
            }
            for s in stages
        ],
    }

    manifest_path = package_out / "artifacts_manifest.json"
    _write_manifest(manifest_path, manifest)

    repro_path = package_out / "repro_commands.md"
    _write_repro_commands(repro_path, commands_executed)

    checklist_path = package_out / "submission_checklist.md"
    _write_submission_checklist(checklist_path, artifacts=artifacts, quality=quality_result)

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"artifacts_manifest={manifest_path}")
        print(f"repro_commands={repro_path}")
        print(f"submission_checklist={checklist_path}")

    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
