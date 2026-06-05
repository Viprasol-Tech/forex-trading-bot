# Contributing to forex-trading-bot

Thanks for your interest! This project is maintained by
[Viprasol Tech](https://viprasol.com). Contributions of all kinds are welcome.

## Development setup

```bash
git clone https://github.com/Viprasol-Tech/forex-trading-bot.git
cd forex-trading-bot
python -m pip install -e ".[dev]"
```

## Before opening a PR

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

## Guidelines

- Keep public functions typed and documented; `mypy` runs in strict mode.
- `ruff format` is the source of truth for style.
- **Never** commit secrets, API keys, `.env`, or private keys.
- Update `CHANGELOG.md` for user-facing changes.

## Questions

Reach us on [Telegram](https://t.me/viprasol_help) or at
[support@viprasol.com](mailto:support@viprasol.com).
