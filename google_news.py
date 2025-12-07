#!/usr/bin/env python3
"""
Google News RSS Collector - сбор новостей через Google News RSS
Бесплатно, без API ключа, работает сразу
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import feedparser
import httpx

from parser import NewsItem

logger = logging.getLogger(__name__)


class GoogleNewsCollector:
    """Сборщик новостей из Google News RSS"""
    
    # Базовые URL для Google News RSS
    BASE_URL = "https://news.google.com/rss"
    SEARCH_URL = "https://news.google.com/rss/search"
    TOPICS_URL = "https://news.google.com/rss/topics"
    
    # Предустановленные темы Google News
    TOPICS = {
        "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FuSjFHZ0pTVlNnQVAB",
        "nation": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FuSjFHZ0pTVlNnQVAB",
        "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FuSjFHZ0pTVlNnQVAB",
        "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FuSjFHZ0pTVlNnQVAB",
        "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FuSjFHZ0pTVlNnQVAB",
        "health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FuSjFLQUFQAQ",
        "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FuSjFHZ0pTVlNnQVAB",
    }
    
    def __init__(self, config: Dict):
        """
        Инициализация сборщика
        
        Args:
            config: Конфигурация с ключами:
                - enabled: bool
                - language: str (ru, en, etc.)
                - country: str (RU, US, etc.)
                - topics: List[str] - темы для сбора
                - search_queries: List[str] - поисковые запросы
                - max_items_per_source: int
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.language = config.get("language", "ru")
        self.country = config.get("country", "RU")
        self.topics = config.get("topics", ["world", "nation"])
        self.search_queries = config.get("search_queries", [
            "Россия Украина",
            "Putin",
            "Zelensky",
            "NATO",
            "война",
            "санкции"
        ])
        self.max_items = config.get("max_items_per_source", 20)
    
    def _make_id(self, url: str) -> str:
        """Генерирует уникальный ID для новости"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    
    def _clean_title(self, title: str) -> str:
        """Очищает заголовок от артефактов"""
        # Убираем название источника в конце (обычно после " - ")
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            if len(parts) == 2 and len(parts[1]) < 50:
                title = parts[0]
        return title.strip()
    
    def _extract_source(self, entry) -> str:
        """Извлекает название источника из записи"""
        # Google News добавляет источник в конце заголовка
        title = getattr(entry, "title", "")
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            if len(parts) == 2 and len(parts[1]) < 50:
                return parts[1].strip()
        
        # Или из поля source
        source = getattr(entry, "source", None)
        if source:
            return getattr(source, "title", "Google News")
        
        return "Google News"
    
    def _build_topic_url(self, topic: str) -> str:
        """Строит URL для темы"""
        topic_id = self.TOPICS.get(topic.lower())
        if topic_id:
            return f"{self.TOPICS_URL}/{topic_id}?hl={self.language}&gl={self.country}&ceid={self.country}:{self.language}"
        return None
    
    def _build_search_url(self, query: str) -> str:
        """Строит URL для поискового запроса"""
        encoded_query = quote_plus(query)
        return f"{self.SEARCH_URL}?q={encoded_query}&hl={self.language}&gl={self.country}&ceid={self.country}:{self.language}"
    
    def _parse_feed(self, url: str, tag: str) -> List[NewsItem]:
        """Парсит RSS фид и возвращает список новостей"""
        items = []
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:self.max_items]:
                title = self._clean_title(getattr(entry, "title", ""))
                link = getattr(entry, "link", "")
                
                if not title or not link:
                    continue
                
                # Парсим дату публикации
                published_parsed = getattr(entry, "published_parsed", None)
                if published_parsed:
                    published_at = datetime(*published_parsed[:6]).isoformat()
                else:
                    published_at = datetime.utcnow().isoformat()
                
                # Извлекаем описание
                summary = getattr(entry, "summary", "")
                # Убираем HTML теги из summary
                summary = re.sub(r'<[^>]+>', '', summary)
                
                source = self._extract_source(entry)
                
                items.append(NewsItem(
                    id=self._make_id(link),
                    title=title,
                    link=link,
                    summary=summary[:500] if summary else "",
                    source=f"Google News ({source})",
                    published_at=published_at,
                    tag=tag
                ))
            
        except Exception as e:
            logger.warning(f"Failed to parse Google News feed: {e}")
        
        return items
    
    def collect_by_topics(self) -> List[NewsItem]:
        """Собирает новости по темам"""
        if not self.enabled:
            return []
        
        all_items = []
        
        for topic in self.topics:
            url = self._build_topic_url(topic)
            if url:
                items = self._parse_feed(url, f"#gnews_{topic}")
                all_items.extend(items)
                logger.info(f"📰 Google News [{topic}]: collected {len(items)} items")
        
        return all_items
    
    def collect_by_search(self) -> List[NewsItem]:
        """Собирает новости по поисковым запросам"""
        if not self.enabled:
            return []
        
        all_items = []
        
        for query in self.search_queries:
            url = self._build_search_url(query)
            # Создаем безопасный тег из запроса
            safe_tag = re.sub(r'[^\w]', '_', query.lower())[:20]
            items = self._parse_feed(url, f"#gnews_{safe_tag}")
            all_items.extend(items)
            logger.info(f"📰 Google News [{query}]: collected {len(items)} items")
        
        return all_items
    
    def collect_all(self) -> List[NewsItem]:
        """Собирает все новости из Google News"""
        if not self.enabled:
            logger.debug("Google News collector is disabled")
            return []
        
        all_items = []
        
        # Собираем по темам
        all_items.extend(self.collect_by_topics())
        
        # Собираем по поисковым запросам  
        all_items.extend(self.collect_by_search())
        
        # Удаляем дубликаты по ID
        seen_ids = set()
        unique_items = []
        for item in all_items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_items.append(item)
        
        logger.info(f"📰 Google News total: {len(unique_items)} unique items")
        return unique_items


def create_google_news_config() -> Dict:
    """Создает конфигурацию по умолчанию для Google News"""
    return {
        "enabled": True,
        "language": "ru",
        "country": "RU",
        "topics": ["world", "nation", "business"],
        "search_queries": [
            "Россия Украина",
            "Путин",
            "Зеленский",
            "NATO НАТО",
            "санкции sanctions",
            "война war",
            "США Европа",
            "Китай China"
        ],
        "max_items_per_source": 15
    }


# Тест
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = create_google_news_config()
    collector = GoogleNewsCollector(config)
    
    items = collector.collect_all()
    
    print(f"\nCollected {len(items)} items:")
    for item in items[:10]:
        print(f"- [{item.tag}] {item.title[:70]}...")
        print(f"  Source: {item.source}")
        print()
