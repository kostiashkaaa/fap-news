#!/usr/bin/env python3
"""
FAP News - Main Bot
Collects news from multiple sources, applies AI analysis, and posts to Telegram
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import deque

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from db import init_db, is_published, mark_published
from parser import NewsItem, collect_news, load_config
from poster import post_news_item
from smart_deduplicator import SmartDeduplicator
from alternative_sources import AlternativeNewsCollector


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Глобальная очередь постов
post_queue: deque = deque()
logger = logging.getLogger("fap-news")


ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"


async def process_urgent_news(items: List[NewsItem], config: Dict) -> None:
    """Обрабатывает срочные новости и публикует их немедленно"""
    if not items:
        return
    
    # Инициализируем AI summarizer для проверки срочности
    ai_config = config.get("ai_summarization", {})
    if not ai_config.get("enabled", False):
        return
    
    from ai_summarizer import AISummarizer
    summarizer = AISummarizer(ai_config)
    
    if not summarizer.is_enabled():
        return
    
    telegram_cfg = config.get("telegram", {})
    token = telegram_cfg.get("token") or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = telegram_cfg.get("channel_id")
    
    if not token or not channel_id:
        logger.warning("Telegram credentials not available for urgent news")
        return
    
    # Получаем настройку максимального возраста новостей
    filters_cfg = config.get("filters", {})
    max_age_minutes = filters_cfg.get("max_age_minutes", 120)  # По умолчанию 2 часа
    
    urgent_items = []
    
    # Проверяем каждую новость на срочность и свежесть (ограничиваем количество для экономии API)
    rate_limit_cfg = ai_config.get("rate_limit", {})
    max_checks = rate_limit_cfg.get("max_urgency_checks", 10)
    items_to_check = [item for item in items if not is_published(item.id, item.source)][:max_checks]
    
    logger.info(f"🔍 Checking {len(items_to_check)} items for urgency (limited to {max_checks} to save API calls)")
    
    for item in items_to_check:
        try:
            # Сначала проверяем свежесть
            is_fresh = await summarizer.check_news_freshness(
                title=item.title,
                content=item.summary or "",
                max_age_minutes=max_age_minutes
            )
            
            if not is_fresh:
                logger.info(f"⏰ OLD NEWS SKIPPED: '{item.title[:50]}...' from {item.source} (older than {max_age_minutes} minutes)")
                continue
            
            # Затем проверяем срочность
            is_urgent = await summarizer.check_urgency(
                title=item.title,
                content=item.summary or ""
            )
            
            if is_urgent:
                urgent_items.append(item)
                logger.info(f"🚨 URGENT NEWS DETECTED: '{item.title[:50]}...' from {item.source}")
                
        except Exception as e:
            logger.warning(f"Failed to check urgency/freshness for '{item.title[:50]}...': {e}")
    
    # Публикуем все срочные новости немедленно
    if urgent_items:
        logger.info(f"🚨 Publishing {len(urgent_items)} urgent news items immediately")
        
        for item in urgent_items:
            try:
                await post_news_item(
                    item, config, 
                    bot_token=token, channel_id=channel_id, 
                    is_urgent=True
                )
                mark_published(item.id, item.link, item.source, item.published_at)
                logger.info(f"⚡ URGENT POSTED: '{item.title[:50]}...' from {item.source}")
                
                # Небольшая пауза между срочными постами
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to post urgent news '{item.title[:50]}...': {e}")


async def process_post_queue() -> None:
    """Публикует один пост из очереди каждые 2-4 минуты"""
    global post_queue
    
    if not post_queue:
        return
    
    # Берем первый пост из очереди
    item, config, token, channel_id = post_queue.popleft()
    
    try:
        await post_news_item(item, config, bot_token=token, channel_id=channel_id)
        mark_published(item.id, item.link, item.source, item.published_at)
        logger.info(f"✅ Posted: '{item.title[:50]}...' from {item.source}")
    except Exception as e:
        logger.error(f"❌ Failed to post '{item.title[:50]}...': {e}")
        # Возвращаем пост в конец очереди для повторной попытки
        post_queue.append((item, config, token, channel_id))


async def post_single_item(item, translation_cfg, token, channel_id):
    """Post a single news item with error handling (deprecated - use queue)"""
    try:
        await post_news_item(item, translation_cfg, bot_token=token, channel_id=channel_id)
        mark_published(item.id, item.link, item.source, item.published_at)
        logger.info(f"Posted: {item.title[:50]}...")
    except Exception as e:
        logger.exception("Failed to post item '%s': %s", item.title, e)


async def process_once(config: Dict) -> None:
    init_db()
    logger.info("Collecting news from %d sources", len(config.get("sources", [])))

    # Собираем новости из RSS источников
    items: List[NewsItem] = collect_news(config)
    logger.info("Collected %d items from RSS sources", len(items))
    
    # Собираем новости из альтернативных источников
    alt_config = config.get("alternative_sources", {})
    if any(source.get("enabled", False) for source in alt_config.values() if isinstance(source, dict)):
        try:
            async with AlternativeNewsCollector(alt_config) as alt_collector:
                alt_items = await alt_collector.collect_all_alternative_sources()
                items.extend(alt_items)
                logger.info("Collected %d items from alternative sources", len(alt_items))
        except Exception as e:
            logger.error(f"Failed to collect from alternative sources: {e}")
    
    logger.info("Total collected %d items before dedup/filter", len(items))
    
    # Применяем умную дедупликацию
    dedup_config = config.get("deduplication", {
        "enabled": True,
        "similarity_threshold": 0.7,
        "title_weight": 0.6,
        "content_weight": 0.4
    })
    
    if dedup_config.get("enabled", True):
        deduplicator = SmartDeduplicator(dedup_config)
        unique_items, duplicate_items = deduplicator.filter_duplicates(items)
        items = unique_items
        logger.info("After deduplication: %d unique items, %d duplicates filtered", len(items), len(duplicate_items))

    telegram_cfg = config.get("telegram", {})

    token = telegram_cfg.get("token") or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = telegram_cfg.get("channel_id")

    # Сначала обрабатываем срочные новости
    await process_urgent_news(items, config)

    # Добавляем новые посты в очередь (максимум 3 за раз, из разных источников)
    # Сначала фильтруем по свежести
    fresh_items = []
    filters_cfg = config.get("filters", {})
    max_age_minutes = filters_cfg.get("max_age_minutes", 120)  # По умолчанию 2 часа
    
    # Инициализируем AI summarizer для проверки свежести
    ai_config = config.get("ai_summarization", {})
    if ai_config.get("enabled", False):
        from ai_summarizer import AISummarizer
        summarizer = AISummarizer(ai_config)
        
        if summarizer.is_enabled():
            # Ограничиваем количество проверок для экономии API
            rate_limit_cfg = ai_config.get("rate_limit", {})
            max_freshness_checks = rate_limit_cfg.get("max_freshness_checks", 15)
            items_to_check = [item for item in items if not is_published(item.id, item.source)][:max_freshness_checks]
            
            logger.info(f"🔍 Checking freshness of {len(items_to_check)} items (max age: {max_age_minutes} minutes, limited to {max_freshness_checks} to save API calls)")
            
            for item in items_to_check:
                try:
                    is_fresh = await summarizer.check_news_freshness(
                        title=item.title,
                        content=item.summary or "",
                        max_age_minutes=max_age_minutes
                    )
                    
                    if is_fresh:
                        fresh_items.append(item)
                    else:
                        logger.info(f"⏰ OLD NEWS FILTERED: '{item.title[:50]}...' from {item.source}")
                        
                except Exception as e:
                    logger.warning(f"Failed to check freshness for '{item.title[:50]}...': {e}")
                    # Если не удалось проверить, добавляем в список
                    fresh_items.append(item)
            
            # Добавляем остальные новости без проверки (если их больше чем лимит)
            remaining_items = [item for item in items if not is_published(item.id, item.source)][max_freshness_checks:]
            fresh_items.extend(remaining_items)
            if remaining_items:
                logger.info(f"📰 Added {len(remaining_items)} items without freshness check (API limit reached)")
        else:
            # Если AI недоступен, берем все новости
            fresh_items = [item for item in items if not is_published(item.id, item.source)]
    else:
        # Если AI отключен, берем все новости
        fresh_items = [item for item in items if not is_published(item.id, item.source)]
    
    logger.info(f"📰 Fresh items after filtering: {len(fresh_items)}")
    
    new_items = fresh_items
    
    if new_items:
        # Группируем по источникам для приоритизированного распределения
        from collections import defaultdict
        items_by_source = defaultdict(list)
        for item in new_items:
            items_by_source[item.source].append(item)
        
        # Определяем приоритеты источников
        priority_sources = {
            # Высокий приоритет - европейские и американские СМИ
            'high': [
                'Fox News', 'New York Times World', 'Financial Times World',
                'Washington Post World', 'The Guardian World', 'BBC News Russian',
                'Euronews', 'Deutsche Welle', 'France 24', 'Al Jazeera'
            ],
            # Средний приоритет - международные и азиатские
            'medium': [
                'South China Morning Post', 'Japan Times', 'Reuters - World News'
            ],
            # Низкий приоритет - российские СМИ
            'low': [
                'RT Russian', 'TASS', 'RIA Novosti', 'Lenta.ru'
            ]
        }
        
        # Сортируем источники по приоритету
        prioritized_sources = []
        
        # Сначала высокий приоритет
        for source in priority_sources['high']:
            if source in items_by_source and items_by_source[source]:
                prioritized_sources.append(source)
        
        # Потом средний приоритет
        for source in priority_sources['medium']:
            if source in items_by_source and items_by_source[source]:
                prioritized_sources.append(source)
        
        # Потом низкий приоритет
        for source in priority_sources['low']:
            if source in items_by_source and items_by_source[source]:
                prioritized_sources.append(source)
        
        # Добавляем остальные источники (если есть новые)
        for source in items_by_source:
            if source not in prioritized_sources:
                prioritized_sources.append(source)
        
        # Берем по 1 новости из приоритетных источников (максимум 3 источника)
        selected_items = []
        sources_used = 0
        max_sources = 3
        
        for source in prioritized_sources:
            if sources_used >= max_sources:
                break
            if source in items_by_source and items_by_source[source]:
                selected_items.append(items_by_source[source][0])  # Берем первую новость из источника
                sources_used += 1
        
        # Логируем приоритеты
        selected_sources = [item.source for item in selected_items]
        logger.info(f"Priority sources selected: {selected_sources}")
        logger.info(f"Adding {len(selected_items)} new items to posting queue from {sources_used} sources")
        
        # Добавляем в глобальную очередь постов
        global post_queue
        for item in selected_items:
            post_queue.append((item, config, token, channel_id))
            logger.info(f"Added to queue: '{item.title[:50]}...' from {item.source}")
    else:
        logger.info("No new items to post")


async def scheduler_main() -> None:
    load_dotenv()
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Config file not found at {CONFIG_PATH}")
    config = load_config(str(CONFIG_PATH))

    interval = int(config.get("scheduler", {}).get("interval_minutes", 10))

    # Run once at start
    await process_once(config)

    scheduler = AsyncIOScheduler()
    # Собираем новости каждые 10 минут
    scheduler.add_job(process_once, "interval", minutes=interval, args=[config], id="collect-and-post")
    
    # Публикуем из очереди каждые 6 минут (средний интервал между 5-7)
    posting_cfg = config.get("posting", {})
    min_delay = posting_cfg.get("min_delay_minutes", 5)
    max_delay = posting_cfg.get("max_delay_minutes", 7)
    avg_delay = (min_delay + max_delay) // 2
    
    # Первая публикация через случайное время
    first_post_delay = random.randint(min_delay, max_delay)
    scheduler.add_job(process_post_queue, "interval", minutes=avg_delay, id="post-from-queue")
    
    scheduler.start()

    logger.info("Scheduler started:")
    logger.info("  - Collecting news every %d minutes", interval)
    logger.info("  - Posting from queue every %d-%d minutes", min_delay, max_delay)

    # Keep the event loop alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(scheduler_main())
