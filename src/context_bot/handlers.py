from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Я простой бот на aiogram.\n"
        "Доступные команды:\n"
        "/start - приветствие\n"
        "/help - справка"
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer("Используй /start для приветствия и /help для этой подсказки.")
