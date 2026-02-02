from __future__ import annotations

import json
from pathlib import Path

from config import defaults

# User overrides live here (often not committed to git)
CONFIG_PATH = Path("data/config.json")


def _defaults_dict() -> dict:
    return {
        "ASSUME_ALL_INCOME_IS_RENTAL": defaults.ASSUME_ALL_INCOME_IS_RENTAL,
        "REVIEW_AMOUNT_THRESHOLD": defaults.REVIEW_AMOUNT_THRESHOLD,
        "VENDOR_RULES": defaults.VENDOR_RULES,
    }


def load_config() -> dict:
    cfg = _defaults_dict()

    if CONFIG_PATH.exists():
        try:
            override = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(override, dict):
                # Shallow merge is enough for now
                cfg.update(override)
        except Exception as e:
            # Don't crash the app because a settings file is malformed
            print(f"[config] Warning: could not read {CONFIG_PATH}: {e}")

    return cfg


CFG = load_config()
