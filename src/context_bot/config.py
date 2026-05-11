import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    bot_base_url: str | None
    bot_base_file_url: str | None


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        msg = "BOT_TOKEN is required"
        raise ValueError(msg)

    bot_base_url = os.getenv("BOT_BASE_URL", "").strip() or None
    bot_base_file_url = os.getenv("BOT_BASE_FILE_URL", "").strip() or None

    return Settings(
        bot_token=bot_token,
        bot_base_url=bot_base_url,
        bot_base_file_url=bot_base_file_url,
    )
