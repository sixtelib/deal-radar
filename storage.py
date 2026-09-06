import json
import os
from datetime import datetime, timezone

from config import SEEN_STORE_PATH, DATA_DIR


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_seen() -> dict:
    _ensure_dir()
    if not os.path.exists(SEEN_STORE_PATH):
        return {}
    with open(SEEN_STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen(seen: dict) -> None:
    _ensure_dir()
    with open(SEEN_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def mark_seen(seen: dict, url: str, is_match: bool, score: int) -> None:
    seen[url] = {
        "first_seen": seen.get(url, {}).get("first_seen", datetime.now(timezone.utc).isoformat()),
        "last_checked": datetime.now(timezone.utc).isoformat(),
        "is_match": is_match,
        "score": score,
    }
