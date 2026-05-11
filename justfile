set shell := ["bash", "-cu"]

# Показать список доступных команд.
default:
    just --list

# Установить и синхронизировать зависимости проекта.
sync:
    uv sync

# Запустить бота через entrypoint проекта.
run:
    uv run context-bot

# Проверить код линтером ruff.
lint:
    uv run ruff check .

# Автоматически исправить проблемы, которые умеет ruff.
fix:
    uv run ruff check . --fix

# Отформатировать код через ruff format.
format:
    uv run ruff format .
