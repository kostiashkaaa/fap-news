#!/usr/bin/env python3
"""
Alternative News Sources - альтернативные источники новостей помимо RSS
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import feedparser

from parser import NewsItem

logger = logging.getLogger(__name__)

@dataclass
class NewsAPIConfig:
    """Конфигурация для News API"""
    api_key: str
    base_url: str = "https://newsapi.org/v2"
    max_requests_per_day: int = 1000
    rate_limit_delay: float = 1.0

@dataclass
class TwitterConfig:
    """Конфигурация для Twitter API"""
    bearer_token: str
    base_url: str = "https://api.twitter.com/2"
    max_requests_per_15min: int = 300

class AlternativeNewsCollector:
    """Сборщик новостей из альтернативных источников"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Инициализация конфигураций
        self.newsapi_config = None
        if config.get("newsapi", {}).get("enabled", False):
            api_key = config["newsapi"].get("api_key") or os.getenv("NEWSAPI_KEY")
            if api_key:
                self.newsapi_config = NewsAPIConfig(api_key=api_key)
        
        self.twitter_config = None
        if config.get("twitter", {}).get("enabled", False):
            bearer_token = config["twitter"].get("bearer_token") or os.getenv("TWITTER_BEARER_TOKEN")
            if bearer_token:
                self.twitter_config = TwitterConfig(bearer_token=bearer_token)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "FAP-News-Bot/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def collect_newsapi_news(self, sources: List[str] = None, 
                                 keywords: List[str] = None) -> List[NewsItem]:
        """Собирает новости через News API"""
        if not self.newsapi_config or not self.session:
            return []
        
        items = []
        
        try:
            # Формируем параметры запроса
            params = {
                "apiKey": self.newsapi_config.api_key,
                "language": "en,ru",
                "sortBy": "publishedAt",
                "pageSize": 50
            }
            
            if sources:
                params["sources"] = ",".join(sources)
            elif keywords:
                params["q"] = " OR ".join(keywords)
            else:
                # Получаем топ новости
                params["country"] = "us,gb,ru"
            
            # Делаем запрос
            url = f"{self.newsapi_config.base_url}/everything"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for article in data.get("articles", []):
                        if article.get("title") and article.get("url"):
                            item = NewsItem(
                                id=f"newsapi_{hash(article['url'])}",
                                title=article["title"],
                                summary=article.get("description", ""),
                                link=article["url"],
                                source="News API",
                                published_at=article.get("publishedAt", datetime.utcnow().isoformat()),
                                tag="#newsapi"
                            )
                            items.append(item)
                    
                    logger.info(f"📰 News API: collected {len(items)} items")
                else:
                    logger.warning(f"News API request failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"News API collection failed: {e}")
        
        return items
    
    async def collect_reddit_news(self, subreddits: List[str] = None) -> List[NewsItem]:
        """Собирает новости из Reddit"""
        if not self.session:
            return []
        
        items = []
        subreddits = subreddits or ["worldnews", "news", "politics", "technology"]
        
        try:
            for subreddit in subreddits:
                # Используем JSON API Reddit
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for post in data.get("data", {}).get("children", []):
                            post_data = post.get("data", {})
                            
                            if post_data.get("title") and post_data.get("url"):
                                # Пропускаем self-posts
                                if post_data.get("is_self", False):
                                    continue
                                
                                item = NewsItem(
                                    id=f"reddit_{post_data['id']}",
                                    title=post_data["title"],
                                    summary=post_data.get("selftext", "")[:500],
                                    link=post_data["url"],
                                    source=f"Reddit r/{subreddit}",
                                    published_at=datetime.fromtimestamp(
                                        post_data.get("created_utc", 0)
                                    ).isoformat(),
                                    tag=f"#reddit_{subreddit}"
                                )
                                items.append(item)
                        
                        logger.info(f"📰 Reddit r/{subreddit}: collected {len([p for p in data.get('data', {}).get('children', []) if not p.get('data', {}).get('is_self', False)])} items")
                        
                        # Задержка между запросами
                        await asyncio.sleep(1)
                    else:
                        logger.warning(f"Reddit request failed for r/{subreddit}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Reddit collection failed: {e}")
        
        return items
    
    async def collect_hackernews(self) -> List[NewsItem]:
        """Собирает новости из Hacker News"""
        if not self.session:
            return []
        
        items = []
        
        try:
            # Получаем топ истории
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    story_ids = await response.json()
                    
                    # Получаем детали для первых 30 историй
                    for story_id in story_ids[:30]:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        async with self.session.get(story_url) as story_response:
                            if story_response.status == 200:
                                story_data = await story_response.json()
                                
                                if story_data.get("title") and story_data.get("url"):
                                    item = NewsItem(
                                        id=f"hn_{story_id}",
                                        title=story_data["title"],
                                        summary=f"Score: {story_data.get('score', 0)} | Comments: {story_data.get('descendants', 0)}",
                                        link=story_data["url"],
                                        source="Hacker News",
                                        published_at=datetime.fromtimestamp(
                                            story_data.get("time", 0)
                                        ).isoformat(),
                                        tag="#hackernews"
                                    )
                                    items.append(item)
                        
                        # Небольшая задержка
                        await asyncio.sleep(0.1)
                    
                    logger.info(f"📰 Hacker News: collected {len(items)} items")
                else:
                    logger.warning(f"Hacker News request failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Hacker News collection failed: {e}")
        
        return items
    
    async def collect_github_trending(self) -> List[NewsItem]:
        """Собирает трендовые репозитории с GitHub"""
        if not self.session:
            return []
        
        items = []
        
        try:
            # GitHub Trending API (неофициальный)
            url = "https://github-trending-api.now.sh/repositories"
            params = {"language": "", "since": "daily"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for repo in data[:20]:  # Топ 20
                        if repo.get("name") and repo.get("url"):
                            item = NewsItem(
                                id=f"github_{repo['name']}",
                                title=f"🔥 {repo['name']} - {repo.get('description', '')[:100]}",
                                summary=f"⭐ {repo.get('stars', 0)} stars | {repo.get('language', 'Unknown')} | {repo.get('description', '')}",
                                link=repo["url"],
                                source="GitHub Trending",
                                published_at=datetime.utcnow().isoformat(),
                                tag="#github"
                            )
                            items.append(item)
                    
                    logger.info(f"📰 GitHub Trending: collected {len(items)} items")
                else:
                    logger.warning(f"GitHub Trending request failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"GitHub Trending collection failed: {e}")
        
        return items
    
    async def collect_all_alternative_sources(self) -> List[NewsItem]:
        """Собирает новости из всех альтернативных источников"""
        all_items = []
        
        # Собираем из всех источников параллельно
        tasks = []
        
        if self.newsapi_config:
            tasks.append(self.collect_newsapi_news())
        
        tasks.extend([
            self.collect_reddit_news(),
            self.collect_hackernews(),
            self.collect_github_trending()
        ])
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Alternative source collection error: {result}")
        
        logger.info(f"📰 Alternative sources: collected {len(all_items)} total items")
        return all_items


def create_alternative_sources_config() -> Dict:
    """Создает конфигурацию для альтернативных источников"""
    return {
        "newsapi": {
            "enabled": False,  # Требует API ключ
            "api_key": "",  # Получить на https://newsapi.org/
            "sources": ["bbc-news", "cnn", "reuters", "associated-press"],
            "keywords": ["breaking", "urgent", "crisis", "war", "politics"]
        },
        "reddit": {
            "enabled": True,
            "subreddits": ["worldnews", "news", "politics", "technology", "programming"]
        },
        "hackernews": {
            "enabled": True
        },
        "github": {
            "enabled": True
        },
        "twitter": {
            "enabled": False,  # Требует API ключ
            "bearer_token": "",  # Получить на https://developer.twitter.com/
            "accounts": ["@BBCBreaking", "@CNN", "@Reuters", "@AP"]
        }
    }


async def test_alternative_sources():
    """Тест альтернативных источников"""
    config = create_alternative_sources_config()
    
    async with AlternativeNewsCollector(config) as collector:
        items = await collector.collect_all_alternative_sources()
        
        print(f"Collected {len(items)} items from alternative sources:")
        for item in items[:10]:  # Показываем первые 10
            print(f"- {item.source}: {item.title[:80]}...")


if __name__ == "__main__":
    asyncio.run(test_alternative_sources())
