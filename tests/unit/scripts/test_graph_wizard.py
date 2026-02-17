from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_graph_wizard_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "graph_wizard.py"
    spec = importlib.util.spec_from_file_location("graph_wizard_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_list_profiles_hides_experimental_by_default(monkeypatch, capsys):
    mod = _load_graph_wizard_module()
    profile = mod.wizard_ops.GraphWizardProfile
    table = {
        "alpha": profile(
            profile_id="alpha",
            description="public",
            template_path=Path("configs/graphs/templates/alpha.yaml"),
            experimental=False,
            defaults={},
        ),
        "beta_exp": profile(
            profile_id="beta_exp",
            description="exp",
            template_path=Path("configs/graphs/templates/beta.yaml"),
            experimental=True,
            defaults={},
        ),
    }
    monkeypatch.setattr(mod.wizard_ops, "load_profile_table", lambda _repo: table)

    code = mod.run(["--list-profiles"])
    assert code == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta_exp" not in out


def test_generate_json_output(monkeypatch, capsys):
    mod = _load_graph_wizard_module()
    profile = mod.wizard_ops.GraphWizardProfile
    generation = mod.wizard_ops.GraphWizardGeneration
    table = {
        "inproc_demo": profile(
            profile_id="inproc_demo",
            description="demo",
            template_path=Path("configs/graphs/templates/inproc_demo_v2.template.yaml"),
            experimental=False,
            defaults={},
        )
    }

    monkeypatch.setattr(mod.wizard_ops, "load_profile_table", lambda _repo: table)
    monkeypatch.setattr(
        mod.wizard_ops,
        "generate_graph",
        lambda **_kwargs: generation(
            profile_id="inproc_demo",
            output_path=Path("/tmp/generated.yaml"),
            template_path=Path("/tmp/template.yaml"),
            experimental=False,
            overrides={"MAX_FRAMES": "30"},
            max_events=30,
        ),
    )

    code = mod.run(["--profile", "inproc_demo", "--out", "tmp.yaml", "--json"])
    assert code == mod.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "generate"
    assert payload["profile_id"] == "inproc_demo"
    assert payload["validation"]["enabled"] is False


def test_validate_mode_returns_precondition_when_invalid(monkeypatch):
    mod = _load_graph_wizard_module()
    profile = mod.wizard_ops.GraphWizardProfile
    table = {
        "inproc_demo": profile(
            profile_id="inproc_demo",
            description="demo",
            template_path=Path("configs/graphs/templates/inproc_demo_v2.template.yaml"),
            experimental=False,
            defaults={},
        )
    }
    validation = mod.wizard_ops.GraphWizardValidation(spec_path=Path("x.yaml"), ok=False, error="broken")
    monkeypatch.setattr(mod.wizard_ops, "load_profile_table", lambda _repo: table)
    monkeypatch.setattr(mod.wizard_ops, "validate_graph_file", lambda **_kwargs: validation)

    code = mod.run(["--validate", "--spec", "x.yaml"])
    assert code == mod.EXIT_PRECONDITION


def test_generate_requires_experimental_opt_in(monkeypatch, capsys):
    mod = _load_graph_wizard_module()
    profile = mod.wizard_ops.GraphWizardProfile
    table = {
        "file_yolo_view": profile(
            profile_id="file_yolo_view",
            description="exp",
            template_path=Path("configs/graphs/templates/file_yolo_view_v2.template.yaml"),
            experimental=True,
            defaults={},
        )
    }
    monkeypatch.setattr(mod.wizard_ops, "load_profile_table", lambda _repo: table)
    monkeypatch.setattr(
        mod.wizard_ops,
        "generate_graph",
        lambda **_kwargs: (_ for _ in ()).throw(
            mod.wizard_ops.GraphWizardPreconditionError("experimental profile requires --experimental")
        ),
    )

    code = mod.run(["--profile", "file_yolo_view", "--out", "x.yaml"])
    assert code == mod.EXIT_PRECONDITION
    assert "experimental" in capsys.readouterr().err.lower()
