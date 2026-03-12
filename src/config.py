import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".transcript_formatter"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "output_dir": str(Path.home() / "Documents" / "Transcripts"),
    "ai_provider": None,
    "ai_model": None,
    "api_keys": {},
    "timestamp_interval_minutes": 5,
    "always_use_ai": False,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    return DEFAULTS.copy()


def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
