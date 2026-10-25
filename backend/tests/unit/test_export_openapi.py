import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "export_openapi.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_openapi_is_stable_json_with_the_health_route() -> None:
    module = _load_script()

    rendered = module.render_openapi()

    assert rendered.endswith("\n")
    assert rendered == module.render_openapi()
    document = json.loads(rendered)
    assert "/api/v1/health" in document["paths"]


def test_main_writes_the_document_to_the_given_path(tmp_path: Path) -> None:
    module = _load_script()
    output = tmp_path / "openapi.json"

    assert module.main(["export_openapi.py", str(output)]) == 0

    assert output.read_text(encoding="utf-8") == module.render_openapi()


def test_main_rejects_missing_output_argument(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_script()

    assert module.main(["export_openapi.py"]) == 2
    assert "usage" in capsys.readouterr().err
