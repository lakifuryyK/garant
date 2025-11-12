from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    bot_token: str
    bot_username: str
    database_path: Path


def load_settings() -> Settings:
    """Load runtime configuration from environment variables."""
    bot_token = os.getenv("BOT_TOKEN", "CHANGE_ME")
    bot_username = os.getenv("BOT_USERNAME", "ElfGiftsBot")
    database_path = Path(os.getenv("DATABASE_PATH", "data/bot.db"))
    database_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=bot_token,
        bot_username=bot_username,
        database_path=database_path,
    )
