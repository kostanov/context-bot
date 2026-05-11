import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from bot.api_client import build_openai_client
from bot.config import load_settings
from bot.context_manager import ContextManager
from bot.handlers import router


async def run_bot() -> None:
    settings = load_settings()
    context_manager = ContextManager()
    openai_client = build_openai_client(settings.proxy_api_key)

    dispatcher = Dispatcher(
        context_manager=context_manager,
        openai_client=openai_client,
        settings=settings,
    )
    dispatcher.include_router(router)

    session: AiohttpSession | None = None
    if settings.bot_base_url:
        if settings.bot_base_file_url:
            api_server = TelegramAPIServer(
                base=f"{settings.bot_base_url}/bot{{token}}/{{method}}",
                file=f"{settings.bot_base_file_url}/file/bot{{token}}/{{path}}",
            )
        else:
            api_server = TelegramAPIServer.from_base(settings.bot_base_url)
        session = AiohttpSession(api=api_server)

    bot = Bot(token=settings.bot_token, session=session)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def main() -> None:
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Bot stopped by Ctrl+C")
