from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from string import Template
from typing import Mapping

from omegaconf import OmegaConf

from schnitzel_stream.graph.compat import validate_graph_compat
from schnitzel_stream.graph.spec import load_node_graph_spec, peek_graph_version
from schnitzel_stream.graph.validate import validate_graph


_PLACEHOLDER_RE = re.compile(r"\$\{[A-Z0-9_]+\}")


class GraphWizardError(RuntimeError):
    pass


class GraphWizardUsageError(ValueError):
    pass


class GraphWizardPreconditionError(ValueError):
    pass


@dataclass(frozen=True)
class GraphWizardProfile:
    profile_id: str
    description: str
    template_path: Path
    experimental: bool = False
    defaults: Mapping[str, str] | None = None


@dataclass(frozen=True)
class GraphWizardGeneration:
    profile_id: str
    output_path: Path
    template_path: Path
    experimental: bool
    overrides: Mapping[str, str]
    max_events: int | None


@dataclass(frozen=True)
class GraphWizardValidation:
    spec_path: Path
    ok: bool
    error: str = ""


def _as_mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _norm_text(value: object) -> str:
    return str(value or "").strip()


def _resolved_path(raw: str, *, repo_root: Path) -> str:
    p = Path(raw)
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    try:
        return p.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def _normalize_graph_path(path: Path, *, repo_root: Path) -> Path:
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    return path


def load_profile_table(repo_root: Path, *, profiles_dir: Path | None = None) -> dict[str, GraphWizardProfile]:
    base = profiles_dir or (repo_root / "configs" / "wizard_profiles")
    if not base.exists():
        raise GraphWizardError(f"wizard profiles directory not found: {base}")

    table: dict[str, GraphWizardProfile] = {}
    for path in sorted(base.glob("*.yaml")):
        payload = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
        data = _as_mapping(payload)

        profile_id = _norm_text(data.get("id"))
        description = _norm_text(data.get("description"))
        template_raw = _norm_text(data.get("template"))
        experimental = bool(data.get("experimental", False))
        defaults = {str(k): str(v) for k, v in _as_mapping(data.get("defaults")).items()}

        if not profile_id:
            raise GraphWizardError(f"profile id is required: {path}")
        if not description:
            raise GraphWizardError(f"profile description is required: {path}")
        if not template_raw:
            raise GraphWizardError(f"profile template is required: {path}")
        if profile_id in table:
            raise GraphWizardError(f"duplicate wizard profile id: {profile_id}")

        template_path = Path(template_raw)
        if not template_path.is_absolute():
            template_path = (repo_root / template_path).resolve()
        if not template_path.exists():
            raise GraphWizardError(f"wizard template not found for profile '{profile_id}': {template_path}")

        table[profile_id] = GraphWizardProfile(
            profile_id=profile_id,
            description=description,
            template_path=template_path,
            experimental=experimental,
            defaults=defaults,
        )

    return table


def list_profile_rows(*, table: Mapping[str, GraphWizardProfile], include_experimental: bool) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for profile_id in sorted(table):
        profile = table[profile_id]
        if profile.experimental and not include_experimental:
            continue
        rows.append(
            (
                profile.profile_id,
                "yes" if profile.experimental else "no",
                str(profile.template_path),
                profile.description,
            )
        )
    return rows


def _build_context(
    *,
    repo_root: Path,
    profile: GraphWizardProfile,
    input_path: str = "",
    camera_index: int | None = None,
    device: str = "",
    model_path: str = "",
    loop: str = "",
    max_events: int | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    context: dict[str, str] = {str(k): str(v) for k, v in (profile.defaults or {}).items()}
    overrides: dict[str, str] = {}

    if input_path:
        normalized = _resolved_path(str(input_path), repo_root=repo_root)
        context["INPUT_PATH"] = normalized
        overrides["INPUT_PATH"] = normalized
    if camera_index is not None:
        context["CAMERA_INDEX"] = str(int(camera_index))
        overrides["CAMERA_INDEX"] = context["CAMERA_INDEX"]
    if device:
        context["YOLO_DEVICE"] = str(device)
        overrides["YOLO_DEVICE"] = context["YOLO_DEVICE"]
    if model_path:
        normalized = _resolved_path(str(model_path), repo_root=repo_root)
        context["YOLO_MODEL_PATH"] = normalized
        overrides["YOLO_MODEL_PATH"] = normalized
    if loop:
        lower = str(loop).strip().lower()
        if lower not in {"true", "false"}:
            raise GraphWizardUsageError("--loop must be true or false")
        context["INPUT_LOOP"] = lower
        overrides["INPUT_LOOP"] = lower
    if max_events is not None:
        if int(max_events) <= 0:
            raise GraphWizardUsageError("--max-events must be > 0")
        # Intent: keep generated templates bounded by default when operator asks for event budget control.
        context["MAX_FRAMES"] = str(int(max_events))
        overrides["MAX_FRAMES"] = context["MAX_FRAMES"]
        context["MAX_EVENTS"] = str(int(max_events))
        overrides["MAX_EVENTS"] = context["MAX_EVENTS"]
    return context, overrides


def _render_template(*, template_path: Path, context: Mapping[str, str]) -> str:
    raw = template_path.read_text(encoding="utf-8")
    try:
        rendered = Template(raw).substitute(context)
    except KeyError as exc:
        missing = str(exc).strip("'")
        raise GraphWizardPreconditionError(f"missing template variable: {missing}") from exc

    leftovers = sorted(set(_PLACEHOLDER_RE.findall(rendered)))
    if leftovers:
        raise GraphWizardPreconditionError(f"unresolved template placeholders: {', '.join(leftovers)}")

    return rendered.strip() + "\n"


def _build_header(*, profile: GraphWizardProfile, overrides: Mapping[str, str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if overrides:
        parts = [f"{key}={value}" for key, value in sorted(overrides.items())]
        override_text = ", ".join(parts)
    else:
        override_text = "none"
    return (
        "# Generated by graph_wizard v1\n"
        f"# profile_id: {profile.profile_id}\n"
        f"# generated_at_utc: {ts}\n"
        f"# overrides: {override_text}\n"
    )


def generate_graph(
    *,
    repo_root: Path,
    table: Mapping[str, GraphWizardProfile],
    profile_id: str,
    out_path: str,
    allow_experimental: bool,
    input_path: str = "",
    camera_index: int | None = None,
    device: str = "",
    model_path: str = "",
    loop: str = "",
    max_events: int | None = None,
) -> GraphWizardGeneration:
    profile = table.get(str(profile_id).strip())
    if profile is None:
        raise GraphWizardUsageError(f"unknown profile: {profile_id}")
    if profile.experimental and not allow_experimental:
        # Intent: expensive/optional dependency profiles stay opt-in to keep default flows deterministic.
        raise GraphWizardPreconditionError(
            f"profile '{profile.profile_id}' is experimental. Re-run with --experimental.",
        )
    if not str(out_path).strip():
        raise GraphWizardUsageError("--out is required when --profile is used")

    output = _normalize_graph_path(Path(out_path), repo_root=repo_root)
    output.parent.mkdir(parents=True, exist_ok=True)

    context, overrides = _build_context(
        repo_root=repo_root,
        profile=profile,
        input_path=input_path,
        camera_index=camera_index,
        device=device,
        model_path=model_path,
        loop=loop,
        max_events=max_events,
    )
    rendered = _render_template(template_path=profile.template_path, context=context)
    header = _build_header(profile=profile, overrides=overrides)
    output.write_text(header + rendered, encoding="utf-8")

    return GraphWizardGeneration(
        profile_id=profile.profile_id,
        output_path=output,
        template_path=profile.template_path,
        experimental=profile.experimental,
        overrides=overrides,
        max_events=max_events,
    )


def validate_graph_file(*, repo_root: Path, spec_path: str) -> GraphWizardValidation:
    if not str(spec_path).strip():
        raise GraphWizardUsageError("--spec is required with --validate")

    path = _normalize_graph_path(Path(spec_path), repo_root=repo_root)
    if not path.exists():
        return GraphWizardValidation(spec_path=path, ok=False, error=f"graph spec not found: {path}")

    try:
        version = peek_graph_version(path)
        if int(version) != 2:
            return GraphWizardValidation(spec_path=path, ok=False, error=f"unsupported version: {version}")
        spec = load_node_graph_spec(path)
        validate_graph(spec.nodes, spec.edges, allow_cycles=False)
        validate_graph_compat(spec.nodes, spec.edges, transport="inproc")
    except Exception as exc:  # pragma: no cover - error branch covered by tests through return payload.
        return GraphWizardValidation(spec_path=path, ok=False, error=str(exc))
    return GraphWizardValidation(spec_path=path, ok=True, error="")


def shell_cmd(cmd: list[str]) -> str:
    return " ".join(os.fspath(part) for part in cmd)
