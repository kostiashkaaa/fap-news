#!/usr/bin/env python3
"""Admin Telegram bot for managing RSS sources"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Configuration
CONFIG_PATH = Path(__file__).parent / "config.json"
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # Set this in .env file


class AddSourceStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_tag = State()
    waiting_for_rss_url = State()


def load_config() -> Dict:
    """Load configuration from JSON file"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    try:
        config = load_config()
        allowed_ids = config.get("admin", {}).get("allowed_user_ids", [])
        
        # Если список пустой, используем переменную окружения для совместимости
        if not allowed_ids and ADMIN_USER_ID:
            allowed_ids = [int(ADMIN_USER_ID)]
        
        return user_id in allowed_ids
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


def save_config(config: Dict) -> None:
    """Save configuration to JSON file"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def create_sources_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with current sources"""
    config = load_config()
    sources = config.get('sources', [])
    
    keyboard = []
    for i, source in enumerate(sources):
        name = source.get('name', 'Unknown')
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {name}",
                callback_data=f"delete_source_{i}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="➕ Добавить источник", callback_data="add_source")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_sources")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_main_keyboard() -> InlineKeyboardMarkup:
    """Create main admin keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📰 Управление источниками", callback_data="manage_sources")],
        [InlineKeyboardButton(text="⚙️ Настройки фильтров", callback_data="manage_filters")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def manage_filters(callback: CallbackQuery):
    """Show filters management"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    config = load_config()
    filters = config.get('filters', {})
    include_kw = filters.get('include_keywords', [])
    exclude_kw = filters.get('exclude_keywords', [])
    max_age = filters.get('max_age_hours', 24)
    
    text = f"⚙️ <b>Настройки фильтров</b>\n\n"
    text += f"🔍 Включающие слова: {', '.join(include_kw) if include_kw else 'Нет'}\n\n"
    text += f"❌ Исключающие слова: {', '.join(exclude_kw) if exclude_kw else 'Нет'}\n\n"
    text += f"⏰ Максимальный возраст: {max_age} часов\n\n"
    text += "Для изменения фильтров отредактируйте config.json"
    
    keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except Exception:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()




# Bot and dispatcher will be initialized in main()
bot = None
dp = None


async def admin_start(message: Message):
    """Admin panel start command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await message.answer(
        "🔧 <b>Панель управления FAP News</b>\n\n"
        "Выберите действие:",
        reply_markup=create_main_keyboard()
    )


async def manage_sources(callback: CallbackQuery):
    """Show sources management"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    config = load_config()
    sources = config.get('sources', [])
    
    text = f"📰 <b>Управление источниками</b>\n\n"
    text += f"Всего источников: {len(sources)}\n\n"
    
    for i, source in enumerate(sources):
        name = source.get('name', 'Unknown')
        tag = source.get('tag', '')
        text += f"{i+1}. {name} {tag}\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=create_sources_keyboard()
        )
    except Exception:
        # If edit fails, send new message
        await callback.message.answer(
            text,
            reply_markup=create_sources_keyboard()
        )
    await callback.answer()


async def start_add_source(callback: CallbackQuery, state: FSMContext):
    """Start adding new source"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    await state.set_state(AddSourceStates.waiting_for_name)
    try:
        await callback.message.edit_text(
            "➕ <b>Добавление нового источника</b>\n\n"
            "Введите название источника (например: BBC News):"
        )
    except Exception:
        await callback.message.answer(
            "➕ <b>Добавление нового источника</b>\n\n"
            "Введите название источника (например: BBC News):"
        )
    await callback.answer()


async def process_source_name(message: Message, state: FSMContext):
    """Process source name input"""
    await state.update_data(name=message.text.strip())
    await state.set_state(AddSourceStates.waiting_for_tag)
    
    await message.answer(
        f"✅ Название: <b>{message.text.strip()}</b>\n\n"
        "Теперь введите тег для источника (например: #bbc):"
    )


async def process_source_tag(message: Message, state: FSMContext):
    """Process source tag input"""
    tag = message.text.strip()
    if not tag.startswith('#'):
        tag = f"#{tag}"
    
    await state.update_data(tag=tag)
    await state.set_state(AddSourceStates.waiting_for_rss_url)
    
    await message.answer(
        f"✅ Тег: <b>{tag}</b>\n\n"
        "Теперь введите RSS URL (например: https://feeds.bbci.co.uk/news/rss.xml):"
    )


async def process_source_url(message: Message, state: FSMContext):
    """Process source URL and save"""
    url = message.text.strip()
    data = await state.get_data()
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await message.answer("❌ URL должен начинаться с http:// или https://")
        return
    
    # Add source to config
    config = load_config()
    new_source = {
        "name": data['name'],
        "tag": data['tag'],
        "rss": url
    }
    
    config.setdefault('sources', []).append(new_source)
    save_config(config)
    
    await state.clear()
    await message.answer(
        f"✅ <b>Источник добавлен!</b>\n\n"
        f"Название: {data['name']}\n"
        f"Тег: {data['tag']}\n"
        f"URL: {url}\n\n"
        "Источник будет использоваться при следующем сборе новостей.",
        reply_markup=create_main_keyboard()
    )


async def delete_source(callback: CallbackQuery):
    """Delete source"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    source_index = int(callback.data.split("_")[-1])
    config = load_config()
    sources = config.get('sources', [])
    
    if 0 <= source_index < len(sources):
        deleted_source = sources.pop(source_index)
        save_config(config)
        
        await callback.answer(f"✅ Источник '{deleted_source.get('name')}' удален")
        
        # Refresh the sources list
        await manage_sources(callback)
    else:
        await callback.answer("❌ Источник не найден")


async def refresh_sources(callback: CallbackQuery):
    """Refresh sources list"""
    await manage_sources(callback)


async def show_stats(callback: CallbackQuery):
    """Show statistics"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    config = load_config()
    sources_count = len(config.get('sources', []))
    
    # Try to get DB stats
    try:
        from db import get_last_published
        recent_posts = get_last_published(limit=10)
        posts_count = len(recent_posts)
    except:
        posts_count = "N/A"
    
    text = f"📊 <b>Статистика</b>\n\n"
    text += f"Источников: {sources_count}\n"
    text += f"Последних постов: {posts_count}\n\n"
    
    if isinstance(posts_count, int) and posts_count > 0:
        text += "Последние посты:\n"
        for i, (news_id, url, source, date) in enumerate(recent_posts[:5], 1):
            text += f"{i}. {source} ({date[:10]})\n"
    
    keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except Exception:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


async def back_to_main(callback: CallbackQuery):
    """Back to main menu"""
    try:
        await callback.message.edit_text(
            "🔧 <b>Панель управления FAP News</b>\n\n"
            "Выберите действие:",
            reply_markup=create_main_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "🔧 <b>Панель управления FAP News</b>\n\n"
            "Выберите действие:",
            reply_markup=create_main_keyboard()
        )
    await callback.answer()


async def main():
    """Main function"""
    global bot, dp
    
    logger.info("Starting admin bot...")
    
    if not ADMIN_USER_ID:
        logger.warning("ADMIN_USER_ID not set in environment variables!")
    
    # Get token from config.json if not in environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        try:
            config = load_config()
            token = config.get("telegram", {}).get("token")
            logger.info("Using token from config.json")
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return
    
    if not token:
        logger.error("No Telegram bot token found! Set TELEGRAM_BOT_TOKEN in environment or config.json")
        return
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    dp.message.register(admin_start, Command("start", "admin"))
    dp.message.register(process_source_name, AddSourceStates.waiting_for_name)
    dp.message.register(process_source_tag, AddSourceStates.waiting_for_tag)
    dp.message.register(process_source_url, AddSourceStates.waiting_for_rss_url)
    
    dp.callback_query.register(manage_sources, F.data == "manage_sources")
    dp.callback_query.register(manage_filters, F.data == "manage_filters")
    dp.callback_query.register(start_add_source, F.data == "add_source")
    dp.callback_query.register(delete_source, F.data.startswith("delete_source_"))
    dp.callback_query.register(refresh_sources, F.data == "refresh_sources")
    dp.callback_query.register(show_stats, F.data == "show_stats")
    dp.callback_query.register(back_to_main, F.data == "back_to_main")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
