#!/usr/bin/env python3
"""
FAP News - Main Bot
Collects news from multiple sources, applies AI analysis, and posts to Telegram
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from config import ConfigManager, load_config, get_config
from db import init_db, is_published, mark_published, cleanup_old_entries, get_database_stats
from parser import NewsItem, collect_news
from poster import post_news_item
from smart_deduplicator import SmartDeduplicator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("fap-news")
ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"


@dataclass
class BotState:
    """Encapsulated bot state to avoid global variables"""
    post_queue: deque = field(default_factory=lambda: deque(maxlen=50))
    processed_count: int = 0
    posted_count: int = 0
    errors_count: int = 0
    last_run: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        uptime = datetime.now() - self.start_time
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "queue_size": len(self.post_queue),
            "processed_count": self.processed_count,
            "posted_count": self.posted_count, 
            "errors_count": self.errors_count,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }


class NewsBot:
    """Main news bot class with encapsulated state"""
    
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.config_manager = ConfigManager.get_instance()
        self.state = BotState()
        self.scheduler: Optional[AsyncIOScheduler] = None
        
    def get_config(self) -> Dict[str, Any]:
        """Load configuration"""
        return self.config_manager.load_raw_config()
    
    def get_source_priority(self, source_name: str, config: Dict[str, Any]) -> int:
        """
        Get priority for a source from config or default priorities
        
        Args:
            source_name: Name of the source
            config: Configuration dictionary
            
        Returns:
            Priority level (1=low, 2=medium, 3=high)
        """
        # First check if source has explicit priority in sources list
        sources = config.get("sources", [])
        for source in sources:
            if source.get("name") == source_name:
                return source.get("priority", 2)
        
        # Fall back to source_priority config
        priority_config = config.get("source_priority", {})
        
        if source_name in priority_config.get("high_priority", []):
            return 3
        elif source_name in priority_config.get("medium_priority", []):
            return 2
        elif source_name in priority_config.get("low_priority", []):
            return 1
        
        # Default medium priority
        return 2
    
    async def process_urgent_news(self, items: List[NewsItem], config: Dict[str, Any]) -> None:
        """Process urgent news and publish immediately"""
        if not items:
            return
        
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
        
        filters_cfg = config.get("filters", {})
        max_age_minutes = filters_cfg.get("max_age_minutes", 120)
        
        urgent_items = []
        
        rate_limit_cfg = ai_config.get("rate_limit", {})
        max_checks = rate_limit_cfg.get("max_urgency_checks", 10)
        items_to_check = [item for item in items if not is_published(item.id, item.source)][:max_checks]
        
        logger.info(f"🔍 Checking {len(items_to_check)} items for urgency (limited to {max_checks})")
        
        for item in items_to_check:
            try:
                is_fresh = await summarizer.check_news_freshness(
                    title=item.title,
                    content=item.summary or "",
                    max_age_minutes=max_age_minutes
                )
                
                if not is_fresh:
                    logger.info(f"⏰ OLD NEWS SKIPPED: '{item.title[:50]}...' from {item.source}")
                    continue
                
                is_urgent = await summarizer.check_urgency(
                    title=item.title,
                    content=item.summary or ""
                )
                
                if is_urgent:
                    urgent_items.append(item)
                    logger.info(f"🚨 URGENT NEWS DETECTED: '{item.title[:50]}...' from {item.source}")
                    
            except Exception as e:
                logger.warning(f"Failed to check urgency for '{item.title[:50]}...': {e}")
                self.state.errors_count += 1
        
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
                    self.state.posted_count += 1
                    logger.info(f"⚡ URGENT POSTED: '{item.title[:50]}...' from {item.source}")
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to post urgent news '{item.title[:50]}...': {e}")
                    self.state.errors_count += 1
    
    async def process_post_queue(self) -> None:
        """Publish one post from queue"""
        if not self.state.post_queue:
            return
        
        item, config, token, channel_id = self.state.post_queue.popleft()
        
        try:
            await post_news_item(item, config, bot_token=token, channel_id=channel_id)
            mark_published(item.id, item.link, item.source, item.published_at)
            self.state.posted_count += 1
            logger.info(f"✅ Posted: '{item.title[:50]}...' from {item.source}")
        except Exception as e:
            logger.error(f"❌ Failed to post '{item.title[:50]}...': {e}")
            self.state.errors_count += 1
            # Return to end of queue for retry (with limit)
            if len(self.state.post_queue) < self.state.post_queue.maxlen:
                self.state.post_queue.append((item, config, token, channel_id))
    
    async def process_once(self, config: Dict[str, Any]) -> None:
        """Process news once"""
        init_db()
        self.state.last_run = datetime.now()
        
        logger.info("Collecting news from %d sources", len(config.get("sources", [])))
        
        # Collect news from RSS sources
        items: List[NewsItem] = collect_news(config)
        logger.info("Collected %d items from RSS sources", len(items))
        
        # Collect from alternative sources
        alt_config = config.get("alternative_sources", {})
        if any(source.get("enabled", False) for source in alt_config.values() if isinstance(source, dict)):
            try:
                from alternative_sources import AlternativeNewsCollector
                async with AlternativeNewsCollector(alt_config) as alt_collector:
                    alt_items = await alt_collector.collect_all_alternative_sources()
                    items.extend(alt_items)
                    logger.info("Collected %d items from alternative sources", len(alt_items))
            except ImportError:
                logger.warning("alternative_sources module not available")
            except Exception as e:
                logger.error(f"Failed to collect from alternative sources: {e}")
                self.state.errors_count += 1
        
        # Collect from Google News
        google_news_config = config.get("google_news", {})
        if google_news_config.get("enabled", False):
            try:
                from google_news import GoogleNewsCollector
                google_collector = GoogleNewsCollector(google_news_config)
                google_items = google_collector.collect_all()
                items.extend(google_items)
                logger.info("Collected %d items from Google News", len(google_items))
            except ImportError:
                logger.warning("google_news module not available")
            except Exception as e:
                logger.error(f"Failed to collect from Google News: {e}")
                self.state.errors_count += 1
        
        # Collect from Telegram channels
        telegram_config = config.get("telegram_channels", {})
        if telegram_config.get("enabled", False):
            try:
                from telegram_channels import TelegramCollector
                tg_collector = TelegramCollector(telegram_config)
                tg_items = await tg_collector.collect_all()
                items.extend(tg_items)
                logger.info("Collected %d items from Telegram channels", len(tg_items))
            except ImportError:
                logger.warning("telegram_channels module not available")
            except Exception as e:
                logger.error(f"Failed to collect from Telegram channels: {e}")
                self.state.errors_count += 1
        
        logger.info("Total collected %d items before dedup/filter", len(items))
        self.state.processed_count += len(items)
        
        # Apply smart deduplication
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
            logger.info("After deduplication: %d unique items, %d duplicates filtered", 
                       len(items), len(duplicate_items))
        
        telegram_cfg = config.get("telegram", {})
        token = telegram_cfg.get("token") or os.getenv("TELEGRAM_BOT_TOKEN")
        channel_id = telegram_cfg.get("channel_id")
        
        # Process urgent news first
        await self.process_urgent_news(items, config)
        
        # Filter fresh items
        fresh_items = await self._filter_fresh_items(items, config)
        logger.info(f"📰 Fresh items after filtering: {len(fresh_items)}")
        
        new_items = fresh_items
        
        if new_items:
            selected_items = self._select_items_by_priority(new_items, config)
            
            logger.info(f"Adding {len(selected_items)} new items to posting queue")
            
            for item in selected_items:
                self.state.post_queue.append((item, config, token, channel_id))
                logger.info(f"Added to queue: '{item.title[:50]}...' from {item.source}")
        else:
            logger.info("No new items to post")
        
        # Periodic cleanup
        cleanup_old_entries(days=30)
    
    async def _filter_fresh_items(self, items: List[NewsItem], config: Dict[str, Any]) -> List[NewsItem]:
        """Filter items by freshness"""
        filters_cfg = config.get("filters", {})
        max_age_minutes = filters_cfg.get("max_age_minutes", 120)
        
        ai_config = config.get("ai_summarization", {})
        if not ai_config.get("enabled", False):
            return [item for item in items if not is_published(item.id, item.source)]
        
        from ai_summarizer import AISummarizer
        summarizer = AISummarizer(ai_config)
        
        if not summarizer.is_enabled():
            return [item for item in items if not is_published(item.id, item.source)]
        
        rate_limit_cfg = ai_config.get("rate_limit", {})
        max_freshness_checks = rate_limit_cfg.get("max_freshness_checks", 15)
        items_to_check = [item for item in items if not is_published(item.id, item.source)][:max_freshness_checks]
        
        logger.info(f"🔍 Checking freshness of {len(items_to_check)} items (max age: {max_age_minutes} minutes)")
        
        fresh_items = []
        
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
                fresh_items.append(item)  # Include if check fails
        
        # Add remaining items without check (API limit reached)
        remaining_items = [item for item in items if not is_published(item.id, item.source)][max_freshness_checks:]
        fresh_items.extend(remaining_items)
        
        if remaining_items:
            logger.info(f"📰 Added {len(remaining_items)} items without freshness check (API limit reached)")
        
        return fresh_items
    
    def _select_items_by_priority(self, items: List[NewsItem], config: Dict[str, Any]) -> List[NewsItem]:
        """Select items by priority configuration"""
        items_by_source = defaultdict(list)
        for item in items:
            items_by_source[item.source].append(item)
        
        # Sort sources by priority
        source_priorities = {}
        for source in items_by_source.keys():
            source_priorities[source] = self.get_source_priority(source, config)
        
        sorted_sources = sorted(
            items_by_source.keys(),
            key=lambda s: source_priorities.get(s, 2),
            reverse=True  # Higher priority first
        )
        
        # Get max sources from config
        posting_config = config.get("posting", {})
        max_sources = posting_config.get("max_sources_per_cycle", 3)
        
        # Select items
        selected_items = []
        sources_used = 0
        
        for source in sorted_sources:
            if sources_used >= max_sources:
                break
            if source in items_by_source and items_by_source[source]:
                selected_items.append(items_by_source[source][0])
                sources_used += 1
        
        selected_sources = [(item.source, source_priorities.get(item.source, 2)) for item in selected_items]
        logger.info(f"Priority sources selected: {selected_sources}")
        
        return selected_items
    
    async def run(self) -> None:
        """Run the bot"""
        load_dotenv()
        
        if not self.config_path.exists():
            raise RuntimeError(f"Config file not found at {self.config_path}")
        
        config = self.get_config()
        
        interval = int(config.get("scheduler", {}).get("interval_minutes", 10))
        
        # Run once at start
        await self.process_once(config)
        
        self.scheduler = AsyncIOScheduler()
        
        # Collect news periodically
        self.scheduler.add_job(
            self.process_once, 
            "interval", 
            minutes=interval, 
            args=[config], 
            id="collect-and-post"
        )
        
        # Post from queue
        posting_cfg = config.get("posting", {})
        min_delay = posting_cfg.get("min_delay_minutes", 5)
        max_delay = posting_cfg.get("max_delay_minutes", 7)
        avg_delay = (min_delay + max_delay) // 2
        
        self.scheduler.add_job(
            self.process_post_queue, 
            "interval", 
            minutes=avg_delay, 
            id="post-from-queue"
        )
        
        self.scheduler.start()
        
        logger.info("Scheduler started:")
        logger.info("  - Collecting news every %d minutes", interval)
        logger.info("  - Posting from queue every %d-%d minutes", min_delay, max_delay)
        
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
            if self.scheduler:
                self.scheduler.shutdown(wait=False)


async def scheduler_main() -> None:
    """Main entry point"""
    bot = NewsBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(scheduler_main())
