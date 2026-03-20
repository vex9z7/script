import os
from pathlib import Path


def load_dotenv(path: Path | str | None = None) -> None:
    if path is None:
        path = Path(__file__).parent / ".env"
    else:
        path = Path(path)
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
