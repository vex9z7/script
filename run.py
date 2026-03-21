#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
IMPORTCHECK_MANIFEST = REPO_ROOT / "importcheck.txt"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


SCRIPTS = {
    "photo_import": "photo_import.__main__",
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        print(_usage(), file=sys.stderr)
        return 2

    if args[0] == "importcheck":
        return run_importcheck(args[1:])

    script_name = args[0]
    module_name = SCRIPTS.get(script_name)

    if module_name is None:
        print(f"Unknown script: {script_name}", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2

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


if __name__ == "__main__":
    raise SystemExit(main())
