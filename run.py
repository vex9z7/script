#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent

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
    return f"Usage: run.py <script>\nAvailable scripts: {available}"


if __name__ == "__main__":
    raise SystemExit(main())
