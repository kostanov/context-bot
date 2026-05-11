from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UserChatState:
    messages: list[dict[str, str]] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 1000


class ContextManager:
    """Хранит историю диалога и параметры генерации отдельно для каждого user_id."""

    def __init__(self) -> None:
        self._by_user: dict[int, UserChatState] = {}

    def state(self, user_id: int) -> UserChatState:
        if user_id not in self._by_user:
            self._by_user[user_id] = UserChatState()
        return self._by_user[user_id]

    def reset(self, user_id: int) -> None:
        self._by_user.pop(user_id, None)

    def messages_snapshot(self, user_id: int) -> list[dict[str, str]]:
        return list(self.state(user_id).messages)

    def append_user(self, user_id: int, content: str) -> None:
        self.state(user_id).messages.append({"role": "user", "content": content})

    def append_assistant(self, user_id: int, content: str) -> None:
        self.state(user_id).messages.append({"role": "assistant", "content": content})

    def set_temperature(self, user_id: int, value: float) -> None:
        self.state(user_id).temperature = value

    def set_max_tokens(self, user_id: int, value: int) -> None:
        self.state(user_id).max_tokens = value
