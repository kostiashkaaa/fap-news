#!/usr/bin/env python3
"""Принудительная публикация одной новости для теста"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def force_post():
    print("🔄 Принудительная публикация новости...\n")
    
    # Загружаем конфиг
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    telegram_cfg = config.get("telegram", {})
    token = telegram_cfg.get("token") or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = telegram_cfg.get("channel_id")
    
    # Собираем новости
    print("📰 Собираем новости из RSS...")
    from parser import collect_news, NewsItem
    items = collect_news(config)
    print(f"   Найдено: {len(items)} новостей")
    
    if not items:
        print("❌ Новости не найдены!")
        return
    
    # Проверяем какие уже опубликованы
    from db import is_published, mark_published, init_db
    init_db()
    
    unpublished = []
    for item in items:
        if not is_published(item.id, item.source):
            unpublished.append(item)
    
    print(f"   Не опубликовано: {len(unpublished)}")
    
    if not unpublished:
        print("\n⚠️ ВСЕ новости уже опубликованы!")
        print("   Это значит, что бот уже обработал все доступные новости.")
        print("   Новые посты появятся, когда источники опубликуют новые статьи.\n")
        
        # Показываем последние опубликованные
        from db import get_last_published
        last = get_last_published(5)
        if last:
            print("📋 Последние опубликованные:")
            for news_id, url, source, date in last:
                print(f"   • {source} ({date[:16]})")
        return
    
    # Берем первую неопубликованную
    item = unpublished[0]
    print(f"\n📤 Публикуем: {item.title[:60]}...")
    print(f"   Источник: {item.source}")
    
    try:
        from poster import post_news_item
        await post_news_item(item, config, bot_token=token, channel_id=channel_id)
        mark_published(item.id, item.link, item.source, item.published_at)
        print("✅ Новость успешно опубликована!")
    except Exception as e:
        print(f"❌ Ошибка публикации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_post())
