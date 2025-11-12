from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bot.config import load_settings


def test_load_settings_reads_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BOT_TOKEN=test-token:123",
                "BOT_USERNAME=test_bot",
                "DATABASE_PATH=data/custom.db",
            ]
        )
    )

    monkeypatch.chdir(tmp_path)

    try:
        settings = load_settings()
    finally:
        for key in ("BOT_TOKEN", "BOT_USERNAME", "DATABASE_PATH"):
            os.environ.pop(key, None)

    assert settings.bot_token == "test-token:123"
    assert settings.bot_username == "test_bot"
    assert settings.database_path == Path("data/custom.db")
    assert settings.database_path.parent.exists()
