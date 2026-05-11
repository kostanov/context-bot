import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from context_bot.config import load_settings
from context_bot.handlers import router


async def run_bot() -> None:
    settings = load_settings()
    dispatcher = Dispatcher()
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
