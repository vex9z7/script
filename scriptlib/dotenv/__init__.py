import os
from collections.abc import Mapping
from pathlib import Path


def read_dotenv(path: Path | str) -> dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {}

    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key] = value.strip()

    return values


def inject_env(values: Mapping[str, str], *, overwrite: bool = False) -> None:
    for key, value in values.items():
        if overwrite or key not in os.environ:
            os.environ[key] = value


def load_dotenv(path: Path | str | None = None) -> None:
    path = Path(path) if path else Path(__file__).parent / ".env"
    inject_env(read_dotenv(path))
