#!/usr/bin/env python3
"""
Диагностика FAP News бота
Проверяет конфигурацию, подключение к Telegram и базу данных
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def print_header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print('='*50)


def print_ok(text):
    print(f"  ✅ {text}")


def print_error(text):
    print(f"  ❌ {text}")


def print_warn(text):
    print(f"  ⚠️  {text}")


def print_info(text):
    print(f"  ℹ️  {text}")


async def main():
    print("\n🔍 FAP News - Диагностика\n")
    
    # 1. Проверка конфигурации
    print_header("1. Проверка конфигурации")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print_error("config.json не найден!")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print_ok("config.json загружен")
    except Exception as e:
        print_error(f"Ошибка чтения config.json: {e}")
        return
    
    # 2. Проверка Telegram настроек
    print_header("2. Проверка Telegram настроек")
    
    telegram_cfg = config.get("telegram", {})
    token = telegram_cfg.get("token") or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = telegram_cfg.get("channel_id")
    
    if not token:
        print_error("Telegram token НЕ НАЙДЕН!")
        print_info("Установите token в config.json или переменную TELEGRAM_BOT_TOKEN")
    else:
        masked_token = token[:10] + "..." + token[-5:] if len(token) > 20 else "***"
        print_ok(f"Token найден: {masked_token}")
    
    if not channel_id:
        print_error("Channel ID НЕ НАЙДЕН!")
        print_info("Установите channel_id в config.json (например: @your_channel)")
    else:
        print_ok(f"Channel ID: {channel_id}")
    
    # 3. Проверка подключения к Telegram
    print_header("3. Проверка подключения к Telegram")
    
    if token:
        try:
            from aiogram import Bot
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            
            bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            me = await bot.get_me()
            print_ok(f"Бот подключен: @{me.username} ({me.first_name})")
            
            # Проверяем канал
            if channel_id:
                try:
                    chat = await bot.get_chat(channel_id)
                    print_ok(f"Канал найден: {chat.title} ({chat.type})")
                    
                    # Проверяем права бота
                    try:
                        member = await bot.get_chat_member(channel_id, me.id)
                        if member.status in ['administrator', 'creator']:
                            print_ok(f"Бот является администратором канала")
                        else:
                            print_error(f"Бот НЕ администратор! Статус: {member.status}")
                            print_info("Добавьте бота как администратора канала с правом публикации")
                    except Exception as e:
                        print_warn(f"Не удалось проверить права: {e}")
                        
                except Exception as e:
                    print_error(f"Ошибка доступа к каналу: {e}")
                    print_info("Убедитесь, что бот добавлен в канал как администратор")
            
            await bot.session.close()
            
        except Exception as e:
            print_error(f"Ошибка подключения к Telegram: {e}")
    
    # 4. Проверка базы данных
    print_header("4. Проверка базы данных")
    
    try:
        from db import get_database_stats, get_last_published
        
        stats = get_database_stats()
        print_ok(f"База данных доступна")
        print_info(f"Всего записей: {stats.get('total_entries', 0)}")
        print_info(f"Размер БД: {stats.get('file_size_mb', 0)} МБ")
        
        last_posts = get_last_published(limit=3)
        if last_posts:
            print_info("Последние опубликованные:")
            for news_id, url, source, date in last_posts:
                print(f"      - {source} ({date[:16]})")
        else:
            print_warn("Нет опубликованных постов в БД")
            
    except Exception as e:
        print_error(f"Ошибка БД: {e}")
    
    # 5. Проверка источников
    print_header("5. Проверка источников новостей")
    
    sources = config.get("sources", [])
    print_info(f"RSS источников: {len(sources)}")
    
    # Google News
    google_cfg = config.get("google_news", {})
    if google_cfg.get("enabled"):
        print_ok("Google News: ВКЛЮЧЕН")
    else:
        print_warn("Google News: отключен")
    
    # Telegram каналы
    tg_cfg = config.get("telegram_channels", {})
    if tg_cfg.get("enabled"):
        channels = tg_cfg.get("channels", [])
        print_ok(f"Telegram каналы: ВКЛЮЧЕНО ({len(channels)} каналов)")
    else:
        print_warn("Telegram каналы: отключены")
    
    # 6. Тест сбора новостей
    print_header("6. Тест сбора новостей")
    
    try:
        from parser import collect_news
        items = collect_news(config)
        print_ok(f"Собрано {len(items)} новостей из RSS")
        
        if items:
            print_info("Примеры:")
            for item in items[:3]:
                print(f"      - {item.source}: {item.title[:50]}...")
    except Exception as e:
        print_error(f"Ошибка сбора: {e}")
    
    # 7. Рекомендации
    print_header("7. Рекомендации")
    
    issues = []
    
    if not token:
        issues.append("Добавьте Telegram токен")
    if not channel_id:
        issues.append("Добавьте Channel ID")
    if not google_cfg.get("enabled") and not tg_cfg.get("enabled"):
        issues.append("Включите дополнительные источники (Google News или Telegram)")
    
    if issues:
        print_warn("Обнаружены проблемы:")
        for issue in issues:
            print(f"      • {issue}")
    else:
        print_ok("Всё настроено правильно!")
        print_info("Запустите бот командой: python run_all.py")
    
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
