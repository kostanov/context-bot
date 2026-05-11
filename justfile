set shell := ["bash", "-cu"]

default:
    just --list

sync:
    uv sync

run:
    uv run context-bot

lint:
    uv run ruff check .

fix:
    uv run ruff check . --fix

format:
    uv run ruff format .
