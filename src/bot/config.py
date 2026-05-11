import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROXY_OPENAI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
CHAT_MODEL = "gpt-5.4-mini"


@dataclass(slots=True)
class Settings:
    bot_token: str
    bot_base_url: str | None
    bot_base_file_url: str | None
    proxy_api_key: str
    llm_log_path: Path


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        msg = "BOT_TOKEN is required"
        raise ValueError(msg)

    proxy_api_key = os.getenv("PROXY_API_KEY", "").strip()
    if not proxy_api_key:
        msg = "PROXY_API_KEY is required"
        raise ValueError(msg)

    bot_base_url = os.getenv("BOT_BASE_URL", "").strip() or None
    bot_base_file_url = os.getenv("BOT_BASE_FILE_URL", "").strip() or None

    log_raw = os.getenv("LLM_LOG_FILE", "llm_chat.log").strip()
    llm_log_path = Path(log_raw).expanduser()

    return Settings(
        bot_token=bot_token,
        bot_base_url=bot_base_url,
        bot_base_file_url=bot_base_file_url,
        proxy_api_key=proxy_api_key,
        llm_log_path=llm_log_path,
    )
