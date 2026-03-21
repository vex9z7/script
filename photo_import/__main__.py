from __future__ import annotations

from photo_import.app import main as app_main


def main(argv: list[str] | None = None) -> int:
    del argv
    return app_main()


if __name__ == "__main__":
    raise SystemExit(main())
