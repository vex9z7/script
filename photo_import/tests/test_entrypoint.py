from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path


def test_package_main_delegates_to_app_main(monkeypatch):
    package_main = importlib.import_module("photo_import.__main__")
    called = []

    monkeypatch.setattr(package_main, "app_main", lambda: called.append("main") or 7)

    assert package_main.main() == 7
    assert called == ["main"]


def test_run_dispatches_registered_package(monkeypatch):
    run_module = importlib.import_module("run")

    class FakeModule:
        @staticmethod
        def main(argv):
            assert argv == ["--flag"]
            return 5

    monkeypatch.setattr(run_module.importlib, "import_module", lambda _: FakeModule)

    assert run_module.main(["photo_import", "--flag"]) == 5


def test_run_returns_error_for_unknown_script(capsys):
    run_module = importlib.import_module("run")

    assert run_module.main(["unknown_script"]) == 2

    captured = capsys.readouterr()
    assert "Unknown script: unknown_script" in captured.err
    assert "Available scripts: photo_import" in captured.err


def test_run_returns_error_when_script_name_missing(capsys):
    run_module = importlib.import_module("run")

    assert run_module.main([]) == 2

    captured = capsys.readouterr()
    assert "Usage: run.py <script>" in captured.err
    assert "Available scripts: photo_import" in captured.err


def test_run_py_is_portable_from_arbitrary_cwd(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    run_path = repo_root / "run.py"
    env = dict(os.environ)

    env.pop("PHOTO_IMPORT_MOUNT_POINT", None)
    env.pop("PHOTO_IMPORT_DESTINATION_ROOT", None)

    result = subprocess.run(
        [sys.executable, str(run_path), "photo_import"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 1
    assert "Configuration error:" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    assert "ImportError" not in result.stderr
