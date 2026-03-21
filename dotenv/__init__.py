import os
from pathlib import Path


def load_dotenv(path: Path | str | None = None) -> None:
    path = Path(path) if path else Path(__file__).parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key, value.strip())
