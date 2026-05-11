from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command, CommandStart
from aiogram.types import Message

from bot.api_client import append_llm_log_async, chat_completion
from bot.config import CHAT_MODEL

if TYPE_CHECKING:
    from openai import AsyncOpenAI

    from bot.config import Settings
    from bot.context_manager import ContextManager

router = Router()
logger = logging.getLogger(__name__)


def normalize_command(text: str, bot_username: str | None) -> str:
    """Снимает @bot из /cmd@bot и /cmd@bot=… для сравнения с каноническим видом."""

    if not bot_username:
        return text
    tag = "@" + bot_username
    lowered_tag = tag.lower()

    if text.startswith("/reset"):
        tail = text[len("/reset") :]
        if tail.lower().startswith(lowered_tag):
            tail = tail[len(tag) :]
        return "/reset" if tail.strip() == "" else text

    for base in ("/temp", "/tokens"):
        if not text.startswith(base):
            continue
        tail = text[len(base) :]
        if tail.lower().startswith(lowered_tag):
            tail = tail[len(tag) :]
        if tail.startswith("="):
            return base + tail
        return text
    return text


class TempOrTokensFilter(BaseFilter):
    """Срабатывает только на /temp=… и /tokens=… (с учётом @username бота)."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        text = message.text or ""
        me = await bot.me()
        n = normalize_command(text, me.username)
        return n.startswith("/temp=") or n.startswith("/tokens=")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Пиши обычный текст — отвечает модель "
        f"{CHAT_MODEL}.\n"
        "Сообщения с / или ! в начале в чат не отправляются.\n\n"
        "Команды:\n"
        "/start — это сообщение\n"
        "/help — краткая справка\n"
        "/reset — сбросить контекст диалога\n"
        "/temp=0.7 — temperature следующих запросов (0.0…1.0, по умолчанию 0.7)\n"
        "/tokens=1000 — max_tokens следующих запросов (по умолчанию 1000)"
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Обычный текст → ответ LLM. Префиксы / и ! (кроме перечисленных команд) "
        "не уходят в модель.\n"
        "/reset, /temp=…, /tokens=… — см. /start."
    )


@router.message(Command("reset"))
async def reset_handler(message: Message, context_manager: ContextManager) -> None:
    uid = message.from_user.id if message.from_user else 0
    context_manager.reset(uid)
    await message.answer("Контекст для этого чата сброшен.")


@router.message(F.text, TempOrTokensFilter())
async def temp_tokens_handler(
    message: Message,
    bot: Bot,
    context_manager: ContextManager,
) -> None:
    text = message.text or ""
    me = await bot.me()
    n = normalize_command(text, me.username)
    uid = message.from_user.id if message.from_user else 0

    if n.startswith("/temp="):
        raw = n[len("/temp=") :].strip().replace(",", ".")
        try:
            t = float(raw)
        except ValueError:
            await message.answer("Нужно число, например /temp=0.5")
            return
        if not 0.0 <= t <= 1.0:
            await message.answer("temperature должен быть от 0.0 до 1.0.")
            return
        context_manager.set_temperature(uid, t)
        await message.answer(f"temperature для следующих запросов: {t}")
        return

    if n.startswith("/tokens="):
        raw = n[len("/tokens=") :].strip()
        try:
            mt = int(raw)
        except ValueError:
            await message.answer("Нужно целое число, например /tokens=1500")
            return
        if mt < 1:
            await message.answer("max_tokens должен быть не меньше 1.")
            return
        if mt > 128_000:
            await message.answer("Слишком большое значение max_tokens.")
            return
        context_manager.set_max_tokens(uid, mt)
        await message.answer(f"max_tokens для следующих запросов: {mt}")


@router.message(F.text & ~F.text.startswith("/") & ~F.text.startswith("!"))
async def llm_chat_handler(
    message: Message,
    context_manager: ContextManager,
    openai_client: AsyncOpenAI,
    settings: Settings,
) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    user = message.from_user
    uid = user.id if user else 0
    st = context_manager.state(uid)
    context_manager.append_user(uid, text)

    messages = context_manager.messages_snapshot(uid)
    try:
        reply, in_tok, out_tok = await chat_completion(
            openai_client,
            messages=messages,
            temperature=st.temperature,
            max_tokens=st.max_tokens,
        )
    except Exception:
        context_manager.state(uid).messages.pop()
        logger.exception("LLM request failed for user_id=%s", uid)
        await message.answer("Не удалось получить ответ от модели. Попробуй позже.")
        return

    if reply:
        context_manager.append_assistant(uid, reply)
    else:
        context_manager.state(uid).messages.pop()
        await message.answer("Модель вернула пустой ответ.")
        return

    await message.answer(reply)

    await append_llm_log_async(
        settings.llm_log_path,
        when=datetime.now(UTC),
        user_id=uid,
        username=user.username if user else None,
        temperature=st.temperature,
        max_tokens=st.max_tokens,
        prompt_tokens=in_tok,
        completion_tokens=out_tok,
        user_preview=text,
        assistant_preview=reply,
    )
