#!/usr/bin/env python3
"""
Admin Telegram bot for managing RSS sources
Includes proper error handling, async file operations, and status monitoring
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aiofiles.os
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

from config import ConfigManager, load_config, save_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Configuration
CONFIG_PATH = Path(__file__).parent / "config.json"
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")


class AddSourceStates(StatesGroup):
    """FSM states for adding new source"""
    waiting_for_name = State()
    waiting_for_tag = State()
    waiting_for_rss_url = State()


class BotStats:
    """Statistics tracker for the bot"""
    
    def __init__(self):
        self.start_time: datetime = datetime.now()
        self.commands_processed: int = 0
        self.errors_count: int = 0
        self.sources_added: int = 0
        self.sources_removed: int = 0
    
    def get_uptime(self) -> str:
        """Get bot uptime as formatted string"""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}ч {minutes}м {seconds}с"
    
    def to_dict(self) -> Dict:
        return {
            "uptime": self.get_uptime(),
            "start_time": self.start_time.isoformat(),
            "commands_processed": self.commands_processed,
            "errors_count": self.errors_count,
            "sources_added": self.sources_added,
            "sources_removed": self.sources_removed
        }


# Global bot stats
bot_stats = BotStats()


async def get_config_async() -> Dict:
    """
    Load configuration asynchronously
    
    Returns:
        Configuration dictionary
    """
    try:
        async with aiofiles.open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            import json
            content = await f.read()
            return json.loads(content)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {CONFIG_PATH}")
        raise RuntimeError(f"Config file not found at {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise


async def save_config_async(config: Dict) -> None:
    """
    Save configuration asynchronously
    
    Args:
        config: Configuration dictionary to save
    """
    try:
        import json
        async with aiofiles.open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(config, indent=2, ensure_ascii=False))
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        raise


async def is_admin(user_id: int) -> bool:
    """
    Check if user is admin
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if user is admin, False otherwise
    """
    try:
        config = await get_config_async()
        allowed_ids = config.get("admin", {}).get("allowed_user_ids", [])
        
        # Fallback to environment variable for compatibility
        if not allowed_ids and ADMIN_USER_ID:
            try:
                allowed_ids = [int(ADMIN_USER_ID)]
            except ValueError:
                logger.warning(f"Invalid ADMIN_USER_ID format: {ADMIN_USER_ID}")
                return False
        
        return user_id in allowed_ids
        
    except FileNotFoundError:
        logger.error("Config file not found when checking admin status")
        return False
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        bot_stats.errors_count += 1
        return False


def create_sources_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with current sources"""
    try:
        config = load_config()
        sources = config.get('sources', [])
        
        keyboard = []
        for i, source in enumerate(sources):
            name = source.get('name', 'Unknown')
            priority = source.get('priority', 2)
            priority_emoji = {1: '🔴', 2: '🟡', 3: '🟢'}.get(priority, '⚪')
            keyboard.append([
                InlineKeyboardButton(
                    text=f"❌ {priority_emoji} {name}",
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
        
    except Exception as e:
        logger.error(f"Error creating sources keyboard: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])


def create_main_keyboard() -> InlineKeyboardMarkup:
    """Create main admin keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📰 Управление источниками", callback_data="manage_sources")],
        [InlineKeyboardButton(text="⚙️ Настройки фильтров", callback_data="manage_filters")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")],
        [InlineKeyboardButton(text="🔍 Статус бота", callback_data="show_status")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def admin_start(message: Message) -> None:
    """Admin panel start command"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await message.answer(
        "🔧 <b>Панель управления FAP News</b>\n\n"
        "Выберите действие:",
        reply_markup=create_main_keyboard()
    )


async def manage_sources(callback: CallbackQuery) -> None:
    """Show sources management"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    try:
        config = await get_config_async()
        sources = config.get('sources', [])
        
        text = f"📰 <b>Управление источниками</b>\n\n"
        text += f"Всего источников: {len(sources)}\n"
        text += "🟢 Высокий приоритет | 🟡 Средний | 🔴 Низкий\n\n"
        
        for i, source in enumerate(sources):
            name = source.get('name', 'Unknown')
            tag = source.get('tag', '')
            priority = source.get('priority', 2)
            priority_emoji = {1: '🔴', 2: '🟡', 3: '🟢'}.get(priority, '⚪')
            text += f"{i+1}. {priority_emoji} {name} {tag}\n"
        
        try:
            await callback.message.edit_text(
                text,
                reply_markup=create_sources_keyboard()
            )
        except Exception as edit_error:
            logger.warning(f"Failed to edit message: {edit_error}")
            await callback.message.answer(
                text,
                reply_markup=create_sources_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error in manage_sources: {e}")
        bot_stats.errors_count += 1
        await callback.answer("❌ Ошибка загрузки источников", show_alert=True)
        return
        
    await callback.answer()


async def manage_filters(callback: CallbackQuery) -> None:
    """Show filters management"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    try:
        config = await get_config_async()
        filters = config.get('filters', {})
        include_kw = filters.get('include_keywords', [])
        exclude_kw = filters.get('exclude_keywords', [])
        max_age = filters.get('max_age_hours', 24)
        max_age_min = filters.get('max_age_minutes', 120)
        
        text = f"⚙️ <b>Настройки фильтров</b>\n\n"
        text += f"🔍 Включающих слов: {len(include_kw)}\n"
        text += f"❌ Исключающих слов: {len(exclude_kw)}\n"
        text += f"⏰ Максимальный возраст: {max_age} часов ({max_age_min} минут)\n\n"
        
        if include_kw:
            sample = include_kw[:10]
            text += f"Примеры включающих: {', '.join(sample)}...\n\n"
        
        text += "Для изменения фильтров отредактируйте config.json"
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        
        try:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        except Exception as edit_error:
            logger.warning(f"Failed to edit message: {edit_error}")
            await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            
    except Exception as e:
        logger.error(f"Error in manage_filters: {e}")
        bot_stats.errors_count += 1
        await callback.answer("❌ Ошибка загрузки фильтров", show_alert=True)
        return
        
    await callback.answer()


async def start_add_source(callback: CallbackQuery, state: FSMContext) -> None:
    """Start adding new source"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    await state.set_state(AddSourceStates.waiting_for_name)
    
    try:
        await callback.message.edit_text(
            "➕ <b>Добавление нового источника</b>\n\n"
            "Введите название источника (например: BBC News):"
        )
    except Exception as e:
        logger.warning(f"Failed to edit message: {e}")
        await callback.message.answer(
            "➕ <b>Добавление нового источника</b>\n\n"
            "Введите название источника (например: BBC News):"
        )
        
    await callback.answer()


async def process_source_name(message: Message, state: FSMContext) -> None:
    """Process source name input"""
    await state.update_data(name=message.text.strip())
    await state.set_state(AddSourceStates.waiting_for_tag)
    
    await message.answer(
        f"✅ Название: <b>{message.text.strip()}</b>\n\n"
        "Теперь введите тег для источника (например: #bbc):"
    )


async def process_source_tag(message: Message, state: FSMContext) -> None:
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


async def validate_rss_url(url: str) -> tuple[bool, str]:
    """
    Validate RSS URL format and accessibility
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url.startswith(('http://', 'https://')):
        return False, "URL должен начинаться с http:// или https://"
    
    # Basic URL format check
    if ' ' in url or not '.' in url:
        return False, "Некорректный формат URL"
    
    # Check if URL is accessible (optional, can be slow)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(url, follow_redirects=True)
            if response.status_code >= 400:
                return False, f"URL недоступен (код: {response.status_code})"
    except httpx.TimeoutException:
        logger.warning(f"Timeout checking RSS URL: {url}")
        # Allow timeout, URL might still work
        return True, ""
    except Exception as e:
        logger.warning(f"Error checking RSS URL {url}: {e}")
        # Allow other errors, URL might still work
        return True, ""
    
    return True, ""


async def process_source_url(message: Message, state: FSMContext) -> None:
    """Process source URL and save"""
    url = message.text.strip()
    data = await state.get_data()
    
    # Validate URL
    is_valid, error_msg = await validate_rss_url(url)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите корректный RSS URL:")
        return
    
    try:
        # Add source to config
        config = await get_config_async()
        new_source = {
            "name": data['name'],
            "tag": data['tag'],
            "rss": url,
            "priority": 2  # Default medium priority
        }
        
        config.setdefault('sources', []).append(new_source)
        await save_config_async(config)
        
        bot_stats.sources_added += 1
        
        await state.clear()
        await message.answer(
            f"✅ <b>Источник добавлен!</b>\n\n"
            f"Название: {data['name']}\n"
            f"Тег: {data['tag']}\n"
            f"URL: {url}\n"
            f"Приоритет: 🟡 Средний\n\n"
            "Источник будет использоваться при следующем сборе новостей.",
            reply_markup=create_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        bot_stats.errors_count += 1
        await message.answer(
            f"❌ Ошибка при добавлении источника: {e}",
            reply_markup=create_main_keyboard()
        )
        await state.clear()


async def delete_source(callback: CallbackQuery) -> None:
    """Delete source"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    try:
        source_index = int(callback.data.split("_")[-1])
        config = await get_config_async()
        sources = config.get('sources', [])
        
        if 0 <= source_index < len(sources):
            deleted_source = sources.pop(source_index)
            await save_config_async(config)
            
            bot_stats.sources_removed += 1
            
            await callback.answer(f"✅ Источник '{deleted_source.get('name')}' удален")
            
            # Refresh the sources list
            await manage_sources(callback)
        else:
            await callback.answer("❌ Источник не найден")
            
    except ValueError as e:
        logger.error(f"Invalid source index: {e}")
        await callback.answer("❌ Некорректный индекс источника")
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        bot_stats.errors_count += 1
        await callback.answer("❌ Ошибка при удалении источника")


async def refresh_sources(callback: CallbackQuery) -> None:
    """Refresh sources list"""
    await manage_sources(callback)


async def show_stats(callback: CallbackQuery) -> None:
    """Show statistics"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    try:
        config = await get_config_async()
        sources_count = len(config.get('sources', []))
        
        # Get priority distribution
        sources = config.get('sources', [])
        high_priority = sum(1 for s in sources if s.get('priority', 2) == 3)
        medium_priority = sum(1 for s in sources if s.get('priority', 2) == 2)
        low_priority = sum(1 for s in sources if s.get('priority', 2) == 1)
        
        # Try to get DB stats
        posts_info = ""
        try:
            from db import get_last_published, get_database_stats
            db_stats = get_database_stats()
            recent_posts = get_last_published(limit=5)
            
            posts_info = f"\n📝 Опубликовано всего: {db_stats.get('total_entries', 'N/A')}\n"
            posts_info += f"💾 Размер БД: {db_stats.get('file_size_mb', 0)} МБ\n"
            
            if recent_posts:
                posts_info += "\n<b>Последние посты:</b>\n"
                for i, (news_id, url, source, date) in enumerate(recent_posts, 1):
                    posts_info += f"{i}. {source} ({date[:10]})\n"
                    
        except ImportError:
            posts_info = "\n⚠️ Модуль БД недоступен"
        except Exception as e:
            logger.warning(f"Failed to get DB stats: {e}")
            posts_info = f"\n⚠️ Ошибка получения статистики БД"
        
        text = f"📊 <b>Статистика</b>\n\n"
        text += f"📰 Источников: {sources_count}\n"
        text += f"   🟢 Высокий приоритет: {high_priority}\n"
        text += f"   🟡 Средний приоритет: {medium_priority}\n"
        text += f"   🔴 Низкий приоритет: {low_priority}\n"
        text += posts_info
        
        keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        
        try:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        except Exception as edit_error:
            logger.warning(f"Failed to edit message: {edit_error}")
            await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            
    except Exception as e:
        logger.error(f"Error in show_stats: {e}")
        bot_stats.errors_count += 1
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)
        return
        
    await callback.answer()


async def show_status(callback: CallbackQuery) -> None:
    """Show bot status and health"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    try:
        stats = bot_stats.to_dict()
        
        # Check components health
        components_status = []
        
        # Check config
        try:
            config = await get_config_async()
            components_status.append("✅ Конфигурация")
        except Exception:
            components_status.append("❌ Конфигурация")
        
        # Check database
        try:
            from db import get_database_stats
            db_stats = get_database_stats()
            if "error" in db_stats:
                components_status.append("⚠️ База данных")
            else:
                components_status.append("✅ База данных")
        except Exception:
            components_status.append("❌ База данных")
        
        # Check AI cache
        try:
            from ai_cache import get_ai_cache
            cache = get_ai_cache()
            cache_stats = cache.get_cache_stats()
            components_status.append(f"✅ AI кэш ({cache_stats.get('active_entries', 0)} записей)")
        except Exception:
            components_status.append("⚠️ AI кэш")
        
        text = f"🔍 <b>Статус бота</b>\n\n"
        text += f"⏱ Время работы: {stats['uptime']}\n"
        text += f"🚀 Запущен: {stats['start_time'][:19]}\n\n"
        
        text += "<b>Счётчики:</b>\n"
        text += f"📨 Команд обработано: {stats['commands_processed']}\n"
        text += f"➕ Источников добавлено: {stats['sources_added']}\n"
        text += f"➖ Источников удалено: {stats['sources_removed']}\n"
        text += f"❌ Ошибок: {stats['errors_count']}\n\n"
        
        text += "<b>Компоненты:</b>\n"
        text += "\n".join(components_status)
        
        keyboard = [
            [InlineKeyboardButton(text="🧹 Очистить кэш", callback_data="clear_cache")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
        
        try:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        except Exception as edit_error:
            logger.warning(f"Failed to edit message: {edit_error}")
            await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            
    except Exception as e:
        logger.error(f"Error in show_status: {e}")
        bot_stats.errors_count += 1
        await callback.answer("❌ Ошибка загрузки статуса", show_alert=True)
        return
        
    await callback.answer()


async def clear_cache(callback: CallbackQuery) -> None:
    """Clear AI cache"""
    bot_stats.commands_processed += 1
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    try:
        from ai_cache import get_ai_cache
        cache = get_ai_cache()
        
        # Cleanup expired entries
        expired = cache.cleanup_expired()
        
        await callback.answer(f"✅ Очищено {expired} устаревших записей")
        
        # Refresh status
        await show_status(callback)
        
    except ImportError:
        await callback.answer("⚠️ Модуль кэша недоступен")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        bot_stats.errors_count += 1
        await callback.answer("❌ Ошибка очистки кэша")


async def back_to_main(callback: CallbackQuery) -> None:
    """Back to main menu"""
    try:
        await callback.message.edit_text(
            "🔧 <b>Панель управления FAP News</b>\n\n"
            "Выберите действие:",
            reply_markup=create_main_keyboard()
        )
    except Exception as e:
        logger.warning(f"Failed to edit message: {e}")
        await callback.message.answer(
            "🔧 <b>Панель управления FAP News</b>\n\n"
            "Выберите действие:",
            reply_markup=create_main_keyboard()
        )
    await callback.answer()


async def main() -> None:
    """Main function"""
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
    dp.callback_query.register(show_status, F.data == "show_status")
    dp.callback_query.register(clear_cache, F.data == "clear_cache")
    dp.callback_query.register(back_to_main, F.data == "back_to_main")
    
    logger.info("Admin bot started successfully")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
