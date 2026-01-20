import os
import asyncio
import feedparser
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import re
import json
from urllib.parse import urlparse
import random
import hashlib

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("❌ BOT_TOKEN и CHANNEL_ID обязательны!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# GIF по умолчанию
DEFAULT_GIF_URL = "https://media.giphy.com/media/3o7TKsQ8UQ4l4LhG2c/giphy.gif"

# Источники (только русские)
FEEDS = [
    {"name": "Хабр — ИИ", "url": "https://habr.com/ru/rss/articles/?q=искусственный+интеллект", "tag": "🧠 Хабр ИИ"},
    {"name": "Хабр — Telegram", "url": "https://habr.com/ru/rss/articles/?q=telegram", "tag": "🤖 Хабр TG"},
    {"name": "VC.ru — Технологии", "url": "https://vc.ru/rss", "tag": "📈 VC.ru"},
    {"name": "aiogram Releases", "url": "https://github.com/aiogram/aiogram/releases.atom", "tag": "🛠️ aiogram"},
    {"name": "python-telegram-bot Releases", "url": "https://github.com/python-telegram-bot/python-telegram-bot/releases.atom", "tag": "🧩 PTB"},
]

SEEN_POSTS_FILE = "/tmp/seen_posts_ru_ai.json"

def get_post_id(title, link):
    """Уникальный ID на основе заголовка и ссылки"""
    combined = (title.strip() + "|" + link.strip()).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()

def is_valid_image_url(url):
    if not url:
        return False
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))

def load_seen_posts():
    if os.path.exists(SEEN_POSTS_FILE):
        try:
            with open(SEEN_POSTS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen_post(post_id):
    seen = load_seen_posts()
    seen.add(post_id)
    if len(seen) > 200:
        seen = set(list(seen)[-150:])
    try:
        with open(SEEN_POSTS_FILE, "w") as f:
            json.dump(list(seen), f)
    except:
        pass

async def send_test_message():
    try:
        await bot.send_message(CHANNEL_ID, "✅ Тест: бот по ИИ и ботам запущен!")
        logging.info("✅ Тестовое сообщение отправлено.")
    except Exception as e:
        logging.error(f"❌ Ошибка теста: {e}")

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
        logging.error(f"Ошибка отправки: {e}")
        await bot.send_message(chat_id=channel_id, text=caption, parse_mode="HTML")

async def publish_fallback(seen_posts):
    fallback_posts = [
        "💡 <b>Знаете ли вы?</b>\nTelegram Bot API поддерживает платежи, игры и даже видеозвонки!",
        "🧠 <b>Факт об ИИ:</b>\nПервый чат-бот ELIZA был создан в 1966 году и имитировал психотерапевта.",
        "🤖 <b>Совет разработчику:</b>\nВсегда используйте Webhook вместо polling для продакшена!",
        "🐍 <b>Python-лайфхак:</b>\nБиблиотека `aiogram` позволяет создать бота за 5 строк кода.",
        "🚀 <b>Идея для бота:</b>\nСоздайте бота, который генерирует изображения по тексту через DALL·E прямо в чате!",
        "🔧 <b>Инструмент:</b>\nGitHub Actions позволяет автоматически деплоить бота при каждом коммите.",
        "💬 <b>Best practice:</b>\nВсегда добавляйте кнопку «Поддержка» в меню бота.",
        "📊 <b>Статистика:</b>\nБолее 80% Telegram-ботов используют Python.",
    ]

    available = [post for post in fallback_posts if post not in seen_posts]
    if available:
        fallback = random.choice(available)
        await bot.send_message(CHANNEL_ID, fallback, parse_mode="HTML")
        logging.info("📤 Опубликован резервный пост")
        save_seen_post(fallback)
    else:
        seen_clean = {item for item in seen_posts if len(item) == 64}
        try:
            with open(SEEN_POSTS_FILE, "w") as f:
                json.dump(list(seen_clean), f)
        except:
            pass
        fallback = fallback_posts[0]
        await bot.send_message(CHANNEL_ID, fallback, parse_mode="HTML")
        logging.info("🔄 Резервные посты исчерпаны — сброс и повтор")

async def fetch_and_post():
    logging.info("🔄 Сбор всех записей со всех источников...")
    seen_posts = load_seen_posts()
    all_entries = []

    # Сбор всех записей
    for feed in FEEDS:
        try:
            logging.info(f"Источник: {feed['name']}")
            parsed = feedparser.parse(feed["url"])
            logging.info(f"📥 Получено записей: {len(parsed.entries)}")
            for entry in parsed.entries[:5]:
                title = entry.get("title", "Без заголовка").strip()
                link = entry.get("link", "").strip()
                if title and link:
                    post_id = get_post_id(title, link)
                    all_entries.append({
                        "title": title,
                        "link": link,
                        "post_id": post_id,
                        "feed_tag": feed["tag"],
                        "entry": entry
                    })
        except Exception as e:
            logging.error(f"Ошибка при сборе {feed['name']}: {e}")

    # Фильтрация новых
    new_entries = [e for e in all_entries if e["post_id"] not in seen_posts]

    if not new_entries:
        logging.info("ℹ️ Нет новых записей. Публикуем резервный контент.")
        await publish_fallback(seen_posts)
        return

    # Публикация (макс. 2 поста за раз)
    published_count = 0
    max_posts = 2

    for entry in new_entries:
        if published_count >= max_posts:
            break

        caption = (
            f'{entry["feed_tag"]}\n\n'
            f'<b>{entry["title"]}</b>\n\n'
            f'🔗 <a href="{entry["link"]}">Читать оригинал</a>'
        )

        image_url = None
        e = entry["entry"]
        if hasattr(e, 'enclosures') and e.enclosures:
            for enc in e.enclosures:
                url = getattr(enc, 'href', None) or (enc.get('href') if isinstance(enc, dict) else None)
                if url and is_valid_image_url(url):
                    image_url = url
                    break
        if not image_url and hasattr(e, 'media_thumbnail') and e.media_thumbnail:
            image_url = e.media_thumbnail[0].get('url')
        if not image_url:
            content = getattr(e, 'summary', '') + getattr(e, 'content', [{}])[0].get('value', '')
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if match:
                image_url = match.group(1)

        await send_post(bot, CHANNEL_ID, caption, image_url)
        logging.info(f"✅ Опубликовано: {entry['title']}")
        save_seen_post(entry["post_id"])
        published_count += 1
        await asyncio.sleep(1)

    logging.info(f"🔚 Опубликовано {published_count} новых постов.")

async def main():
    await send_test_message()
    logging.info("🚀 Принудительная публикация при старте...")
    await fetch_and_post()

    scheduler = AsyncIOScheduler()
    interval_hours = int(os.getenv("POST_INTERVAL_HOURS", 24))
    scheduler.add_job(fetch_and_post, 'interval', hours=interval_hours)
    scheduler.start()
    logging.info(f"✅ Бот 'Русский ИИ и Боты' запущен. Интервал: {interval_hours} ч.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
