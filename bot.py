import os
import asyncio
import feedparser
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import re
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("❌ BOT_TOKEN и CHANNEL_ID обязательны!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DEFAULT_GIF_URL = "https://media.giphy.com/media/3o7TKsQ8UQ4l4LhG2c/giphy.gif"

FEEDS = [
    {"name": "Telegram Blog", "url": "https://telegram.org/blog/rss", "tag": "📢 Telegram"},
    {"name": "Habr — Telegram", "url": "https://habr.com/ru/hub/telegram/rss/", "tag": "🤖 Боты"},
    {"name": "The Verge — AI", "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml", "tag": "🧠 AI"},
]

def is_valid_image_url(url):
    if not url:
        return False
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))

async def send_test_message():
    """Отправляет тестовое сообщение при запуске"""
    try:
        await bot.send_message(CHANNEL_ID, "✅ ТЕСТ: бот запущен и может публиковать в канал!")
        logging.info("✅ Тестовое сообщение успешно отправлено.")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки тестового сообщения: {e}")

async def send_post(bot, channel_id, caption, image_url=None):
    try:
        if image_url and is_valid_image_url(image_url):
            if image_url.lower().endswith('.gif'):
                await bot.send_animation(chat_id=channel_id, animation=image_url, caption=caption, parse_mode="HTML")
            else:
                await bot.send_photo(chat_id=channel_id, photo=image_url, caption=caption, parse_mode="HTML")
        else:
            await bot.send_animation(chat_id=channel_id, animation=DEFAULT_GIF_URL, caption=caption, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки поста: {e}")
        await bot.send_message(chat_id=channel_id, text=caption, parse_mode="HTML")

async def fetch_and_post():
    for feed
