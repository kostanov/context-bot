from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from openai import AsyncOpenAI

from bot.config import CHAT_MODEL, PROXY_OPENAI_BASE_URL


def build_openai_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(base_url=PROXY_OPENAI_BASE_URL, api_key=api_key)


async def chat_completion(
    client: AsyncOpenAI,
    *,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> tuple[str, int | None, int | None]:
    """Текст ответа и числа токенов из usage (если API их отдал)."""

    response = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )
    choice = response.choices[0]
    text = (choice.message.content or "").strip()
    usage = response.usage
    in_tok = usage.prompt_tokens if usage else None
    out_tok = usage.completion_tokens if usage else None
    return text, in_tok, out_tok


def append_llm_log(
    path: Path,
    *,
    when: datetime,
    user_id: int,
    username: str | None,
    temperature: float,
    max_tokens: int,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    user_preview: str,
    assistant_preview: str,
) -> None:
    """Одна строка на запрос: время, пользователь, параметры, токены, укороченный текст."""

    ts = when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    user_label = f"{user_id}" + (f" @{username}" if username else "")
    pt = prompt_tokens if prompt_tokens is not None else "?"
    ct = completion_tokens if completion_tokens is not None else "?"
    u_prev = _one_line(user_preview, 200)
    a_prev = _one_line(assistant_preview, 200)
    line = (
        f"{ts}\tuser={user_label}\ttemperature={temperature}\tmax_tokens={max_tokens}\t"
        f"prompt_tokens={pt}\tcompletion_tokens={ct}\t"
        f"in={u_prev}\tout={a_prev}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


async def append_llm_log_async(
    path: Path,
    *,
    when: datetime,
    user_id: int,
    username: str | None,
    temperature: float,
    max_tokens: int,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    user_preview: str,
    assistant_preview: str,
) -> None:
    await asyncio.to_thread(
        append_llm_log,
        path,
        when=when,
        user_id=user_id,
        username=username,
        temperature=temperature,
        max_tokens=max_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        user_preview=user_preview,
        assistant_preview=assistant_preview,
    )


def _one_line(s: str, max_len: int) -> str:
    x = " ".join(s.split())
    if len(x) <= max_len:
        return x
    return x[: max_len - 1] + "…"
