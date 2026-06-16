from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import MOCK_DATA_ROOT


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_mock_data() -> dict[str, Any]:
    """Load every JSON file under data/mock into a dictionary keyed by filename."""

    data: dict[str, Any] = {}
    for file_path in sorted(MOCK_DATA_ROOT.glob("*.json")):
        data[file_path.stem] = load_json_file(file_path)
    return data
