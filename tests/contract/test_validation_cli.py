from __future__ import annotations

import json
import importlib.util
from pathlib import Path


_SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "validate_catalog.py"
_SPEC = importlib.util.spec_from_file_location("validate_catalog", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
main = _MODULE.main


def test_cli_emits_json_and_nonzero_for_errors(tmp_path, capsys):
    exit_code = main([str(tmp_path)])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["valid"] is False
