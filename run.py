#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from scriptlib import dotenv


REPO_ROOT = Path(__file__).resolve().parent
IMPORTCHECK_MANIFEST = REPO_ROOT / "importcheck.txt"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


SCRIPTS = {
    "photo_import": {
        "module": "photo_import.__main__",
        "env_file": REPO_ROOT / "photo_import" / ".env",
    },
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        print(_usage(), file=sys.stderr)
        return 2

    if args[0] == "importcheck":
        return run_importcheck(args[1:])

    script_name = args[0]
    script = SCRIPTS.get(script_name)

    if script is None:
        print(f"Unknown script: {script_name}", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2

    _inject_script_env(script)
    module_name = script["module"]
    module = importlib.import_module(module_name)
    return module.main(args[1:])


def _usage() -> str:
    available = ", ".join(sorted(SCRIPTS))
    return (
        "Usage: run.py <script>\n"
        "       run.py importcheck [module]\n"
        f"Available scripts: {available}"
    )


def run_importcheck(args: list[str]) -> int:
    module_names = args if args else _load_importcheck_modules()
    failed = False

    for module_name in module_names:
        _inject_env_for_module(module_name)
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"FAIL {module_name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            failed = True
            continue

        print(f"OK {module_name}")

    return 1 if failed else 0


def _load_importcheck_modules() -> list[str]:
    modules = []

    for line in IMPORTCHECK_MANIFEST.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        modules.append(item)

    return modules


def _inject_env_for_module(module_name: str) -> None:
    root_package = module_name.split(".", maxsplit=1)[0]
    script = SCRIPTS.get(root_package)
    if script is None:
        return
    _inject_script_env(script)


def _inject_script_env(script: dict[str, str | Path]) -> None:
    env_file = script["env_file"]
    dotenv.inject_env(dotenv.read_dotenv(env_file))


if __name__ == "__main__":
    raise SystemExit(main())
