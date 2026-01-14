# Telegram Content Bot

Автоматически публикует новости по темам:
- Telegram
- Telegram-боты
- Искусственный интеллект

## Как развернуть на Railway

1. Форкни этот репозиторий.
2. Зайди на [Railway.app](https://railway.app) → «New Project» → «Deploy from GitHub repo».
3. Выбери этот репозиторий.
4. Добавь переменные окружения:
   - `BOT_TOKEN` — токен от @BotFather
   - `CHANNEL_ID` — ID канала (например, `@my_channel`)
   - (опционально) `POST_INTERVAL_HOURS` — интервал в часах (по умолчанию: 6)
5. Нажми «Deploy».

Готово! Бот будет работать 24/7.
