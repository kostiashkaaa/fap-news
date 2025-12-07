#!/usr/bin/env python3
"""
Telegram Channel Collector - сбор новостей из публичных Telegram каналов
Использует веб-версию Telegram (t.me/s/channel) для парсинга без API
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from parser import NewsItem

logger = logging.getLogger(__name__)


@dataclass
class TelegramChannel:
    """Конфигурация Telegram канала"""
    username: str  # Без @
    name: str  # Человекочитаемое название
    tag: str  # Хэштег для постов
    priority: int = 2  # 1=low, 2=medium, 3=high


class TelegramCollector:
    """
    Сборщик новостей из публичных Telegram каналов
    Использует веб-версию t.me/s/ для парсинга
    """
    
    BASE_URL = "https://t.me/s"
    
    # Предустановленные каналы с новостями
    DEFAULT_CHANNELS = [
        TelegramChannel("raborufr", "Рабокалрия", "#рабокалрия"),
        TelegramChannel("bbcrussian", "BBC Russian", "#bbcru", priority=3),
        TelegramChannel("medaborufr", "Медаборка", "#медабока"),
        TelegramChannel("breakingmash", "Mash", "#mash", priority=3),
        TelegramChannel("rian_ru", "РИА Новости", "#ria", priority=2),
        TelegramChannel("taborufr", "Табоока", "#таборока"),
        TelegramChannel("rt_russian", "RT на русском", "#rt", priority=1),
        TelegramChannel("raborufrua", "Рабока Украина", "#рабокаюа"),
    ]
    
    def __init__(self, config: Dict):
        """
        Инициализация сборщика
        
        Args:
            config: Конфигурация с ключами:
                - enabled: bool
                - channels: List[Dict] - список каналов
                - max_posts_per_channel: int
                - max_age_hours: int
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.max_posts = config.get("max_posts_per_channel", 10)
        self.max_age_hours = config.get("max_age_hours", 24)
        
        # Парсим каналы из конфига или используем дефолтные
        self.channels = []
        channels_config = config.get("channels", [])
        
        if channels_config:
            for ch in channels_config:
                if isinstance(ch, dict):
                    self.channels.append(TelegramChannel(
                        username=ch.get("username", "").lstrip("@"),
                        name=ch.get("name", ch.get("username", "")),
                        tag=ch.get("tag", f"#tg_{ch.get('username', '')}"),
                        priority=ch.get("priority", 2)
                    ))
                elif isinstance(ch, str):
                    username = ch.lstrip("@")
                    self.channels.append(TelegramChannel(
                        username=username,
                        name=username,
                        tag=f"#tg_{username}"
                    ))
        else:
            self.channels = self.DEFAULT_CHANNELS.copy()
    
    def _make_id(self, channel: str, post_id: str) -> str:
        """Генерирует уникальный ID для поста"""
        unique = f"tg_{channel}_{post_id}"
        return hashlib.sha256(unique.encode("utf-8")).hexdigest()[:32]
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Парсит дату/время из Telegram"""
        try:
            # Telegram использует формат "2024-01-15T12:30:00+00:00"
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст поста"""
        if not text:
            return ""
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Убираем ссылки на другие каналы формата @channel
        # text = re.sub(r'@\w+', '', text)
        
        return text[:1000]  # Ограничиваем длину
    
    async def _fetch_channel(self, channel: TelegramChannel) -> List[NewsItem]:
        """Получает посты из канала"""
        items = []
        url = f"{self.BASE_URL}/{channel.username}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch @{channel.username}: {response.status_code}")
                    return []
                
                soup = BeautifulSoup(response.text, "lxml")
                
                # Ищем все сообщения
                messages = soup.select(".tgme_widget_message")
                
                cutoff_time = datetime.utcnow() - timedelta(hours=self.max_age_hours)
                
                for msg in messages[:self.max_posts]:
                    try:
                        # ID поста
                        post_id = msg.get("data-post", "").split("/")[-1]
                        if not post_id:
                            continue
                        
                        # Текст сообщения
                        text_div = msg.select_one(".tgme_widget_message_text")
                        if not text_div:
                            continue
                        
                        text = self._clean_text(text_div.get_text())
                        if not text or len(text) < 20:
                            continue
                        
                        # Дата публикации
                        time_elem = msg.select_one(".tgme_widget_message_date time")
                        published_at = datetime.utcnow()
                        
                        if time_elem and time_elem.get("datetime"):
                            parsed_time = self._parse_datetime(time_elem["datetime"])
                            if parsed_time:
                                published_at = parsed_time.replace(tzinfo=None)
                        
                        # Проверяем свежесть
                        if published_at < cutoff_time:
                            continue
                        
                        # Ссылка на пост
                        link = f"https://t.me/{channel.username}/{post_id}"
                        
                        # Заголовок - первые 100 символов или первое предложение
                        title = text[:100]
                        if ". " in title:
                            title = title.split(". ")[0] + "."
                        elif "! " in title:
                            title = title.split("! ")[0] + "!"
                        
                        items.append(NewsItem(
                            id=self._make_id(channel.username, post_id),
                            title=title,
                            link=link,
                            summary=text,
                            source=f"Telegram: {channel.name}",
                            published_at=published_at.isoformat(),
                            tag=channel.tag
                        ))
                        
                    except Exception as e:
                        logger.debug(f"Error parsing message from @{channel.username}: {e}")
                        continue
                
                logger.info(f"📱 Telegram @{channel.username}: collected {len(items)} posts")
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching @{channel.username}")
        except Exception as e:
            logger.error(f"Error fetching @{channel.username}: {e}")
        
        return items
    
    async def collect_all(self) -> List[NewsItem]:
        """Собирает посты из всех каналов"""
        if not self.enabled:
            logger.debug("Telegram collector is disabled")
            return []
        
        if not self.channels:
            logger.warning("No Telegram channels configured")
            return []
        
        all_items = []
        
        # Собираем параллельно, но с небольшой задержкой
        for channel in self.channels:
            items = await self._fetch_channel(channel)
            all_items.extend(items)
            await asyncio.sleep(0.5)  # Небольшая задержка между запросами
        
        # Сортируем по приоритету канала и времени
        all_items.sort(
            key=lambda x: (
                -next((c.priority for c in self.channels if c.name in x.source), 2),
                x.published_at
            ),
            reverse=True
        )
        
        logger.info(f"📱 Telegram total: {len(all_items)} posts from {len(self.channels)} channels")
        return all_items


def create_telegram_config() -> Dict:
    """Создает конфигурацию по умолчанию для Telegram"""
    return {
        "enabled": True,
        "max_posts_per_channel": 10,
        "max_age_hours": 24,
        "channels": [
            {"username": "bbcrussian", "name": "BBC Russian", "tag": "#bbcru", "priority": 3},
            {"username": "breakingmash", "name": "Mash", "tag": "#mash", "priority": 3},
            {"username": "rian_ru", "name": "РИА Новости", "tag": "#ria", "priority": 2},
            {"username": "rt_russian", "name": "RT на русском", "tag": "#rt", "priority": 1},
            {"username": "taborufr", "name": "TACC", "tag": "#tass", "priority": 2},
        ]
    }


# Тест
async def test_telegram_collector():
    logging.basicConfig(level=logging.INFO)
    
    config = create_telegram_config()
    collector = TelegramCollector(config)
    
    items = await collector.collect_all()
    
    print(f"\nCollected {len(items)} posts:")
    for item in items[:10]:
        print(f"- [{item.tag}] {item.title[:60]}...")
        print(f"  Source: {item.source}")
        print(f"  Published: {item.published_at}")
        print()


if __name__ == "__main__":
    asyncio.run(test_telegram_collector())
