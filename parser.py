#!/usr/bin/env python3
"""
FAP News - Parser Module
Handles RSS/HTML parsing and news item filtering
"""

from __future__ import annotations

import hashlib
import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import feedparser
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    id: str
    title: str
    link: str
    summary: str
    source: str
    published_at: str  # ISO 8601
    tag: str


def _make_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove extra whitespace and normalize
    text = re.sub(r"\s+", " ", text).strip()
    
    # Remove common RSS artifacts and tracking parameters
    text = re.sub(r'utm_source=.*?(&|$)', '', text)
    text = re.sub(r'\?utm_.*', '', text)
    text = re.sub(r'&utm_.*', '', text)
    
    # Remove "Читать далее" and similar
    text = re.sub(r'Читать далее.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Read more.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Подробнее.*$', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def parse_rss(source: Dict[str, Any]) -> List[NewsItem]:
    """
    Parse RSS feed from source
    
    Args:
        source: Source configuration dict
        
    Returns:
        List of parsed news items
    """
    rss_url = source.get("rss")
    if not rss_url:
        return []
    
    try:
        parsed = feedparser.parse(rss_url)
        items: List[NewsItem] = []
        
        for entry in parsed.entries:
            title = _normalize_text(getattr(entry, "title", ""))
            link = _normalize_text(getattr(entry, "link", ""))
            summary = _normalize_text(getattr(entry, "summary", getattr(entry, "description", "")))
            published_parsed = getattr(entry, "published_parsed", None)
            
            if published_parsed:
                published_at = datetime(*published_parsed[:6]).isoformat()
            else:
                published_at = datetime.utcnow().isoformat()
            
            unique_basis = link or title
            news_id = _make_id(unique_basis) if unique_basis else _make_id(title + published_at)
            
            items.append(
                NewsItem(
                    id=news_id,
                    title=title,
                    link=link,
                    summary=summary,
                    source=str(source.get("name", "unknown")),
                    published_at=published_at,
                    tag=str(source.get("tag", "")),
                )
            )
        
        logger.debug(f"Parsed {len(items)} items from RSS: {source.get('name', 'unknown')}")
        return items
        
    except Exception as e:
        logger.warning(f"Failed to parse RSS {source.get('name', 'unknown')}: {e}")
        return []


def parse_html(source: Dict[str, Any]) -> List[NewsItem]:
    """
    Parse HTML page for news items
    
    Args:
        source: Source configuration dict
        
    Returns:
        List of parsed news items
    """
    url = source.get("html_url")
    selector = source.get("html_selector", {})
    if not url or not selector:
        return []

    items: List[NewsItem] = []
    try:
        with httpx.Client(timeout=20.0, headers={"User-Agent": "fap-news/1.0"}) as client:
            response = client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

        root_sel = selector.get("item")
        title_sel = selector.get("title")
        link_sel = selector.get("link")
        summary_sel = selector.get("summary")
        if not root_sel or not title_sel or not link_sel:
            return []

        for node in soup.select(root_sel):
            title_node = node.select_one(title_sel)
            if not title_node:
                continue
            title = _normalize_text(title_node.get_text(" "))

            # Link: support pseudo syntax "a::attr(href)"
            link: str = ""
            if "::attr(" in link_sel:
                css, attr_part = link_sel.split("::attr(", 1)
                attr = attr_part.rstrip(")").strip()
                link_node = node.select_one(css)
                if link_node and link_node.has_attr(attr):
                    link = _normalize_text(link_node.get(attr) or "")
            else:
                link_node = node.select_one(link_sel)
                if link_node and link_node.has_attr("href"):
                    link = _normalize_text(link_node.get("href") or "")

            summary = ""
            if summary_sel:
                summary_node = node.select_one(summary_sel)
                if summary_node:
                    summary = _normalize_text(summary_node.get_text(" "))

            if not (title and link):
                continue

            news_id = _make_id(link)
            items.append(
                NewsItem(
                    id=news_id,
                    title=title,
                    link=link,
                    summary=summary,
                    source=str(source.get("name", "unknown")),
                    published_at=datetime.utcnow().isoformat(),
                    tag=str(source.get("tag", "")),
                )
            )
        
        logger.debug(f"Parsed {len(items)} items from HTML: {source.get('name', 'unknown')}")
        
    except Exception as e:
        logger.warning(f"Failed to parse HTML {source.get('name', 'unknown')}: {e}")
        return []

    return items


def filter_items(
    items: Iterable[NewsItem],
    include_keywords: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None,
    max_age_hours: int = 24,
    max_age_minutes: Optional[int] = None,
) -> List[NewsItem]:
    """
    Filter news items by keywords and age
    
    Args:
        items: Items to filter
        include_keywords: Keywords that must be present
        exclude_keywords: Keywords that must not be present
        max_age_hours: Maximum age in hours
        max_age_minutes: Maximum age in minutes (overrides hours)
        
    Returns:
        Filtered list of items
    """
    include_keywords = [k.lower() for k in (include_keywords or []) if k.strip()]
    exclude_keywords = [k.lower() for k in (exclude_keywords or []) if k.strip()]
    
    # Calculate cutoff time for fresh news
    if max_age_minutes is not None:
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    else:
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    def text_of(item: NewsItem) -> str:
        return f"{item.title} {item.summary}".lower()
    
    def is_recent(item: NewsItem) -> bool:
        try:
            item_time = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
            # Remove timezone info for comparison
            if item_time.tzinfo:
                item_time = item_time.replace(tzinfo=None)
            return item_time >= cutoff_time
        except (ValueError, AttributeError):
            # If we can't parse the date, assume it's recent
            return True

    filtered: List[NewsItem] = []
    for item in items:
        # Filter by date first
        if not is_recent(item):
            continue
            
        # Then filter by keywords
        text = text_of(item)
        if exclude_keywords and any(k in text for k in exclude_keywords):
            continue
        if include_keywords and not any(k in text for k in include_keywords):
            continue
        filtered.append(item)
    
    logger.debug(f"Filtered {len(list(items))} -> {len(filtered)} items")
    return filtered


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file
    
    Args:
        path: Path to config file (optional, uses default if not provided)
        
    Returns:
        Configuration dictionary
    """
    if path:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Use centralized config module
    from config import load_config as load_config_central
    return load_config_central()


def collect_news(config: Dict[str, Any]) -> List[NewsItem]:
    """
    Collect news from all configured sources
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of collected and filtered news items
    """
    all_items: List[NewsItem] = []
    sources = config.get("sources", [])
    
    for src in sources:
        if src.get("rss"):
            items = parse_rss(src)
            all_items.extend(items)
        elif src.get("html_url"):
            items = parse_html(src)
            all_items.extend(items)

    logger.info(f"Collected {len(all_items)} raw items from {len(sources)} sources")

    filters_cfg = config.get("filters", {})
    include_kw = filters_cfg.get("include_keywords", [])
    exclude_kw = filters_cfg.get("exclude_keywords", [])
    max_age_hours = filters_cfg.get("max_age_hours", 24)
    max_age_minutes = filters_cfg.get("max_age_minutes")
    
    filtered = filter_items(all_items, include_kw, exclude_kw, max_age_hours, max_age_minutes)
    logger.info(f"After filtering: {len(filtered)} items")
    
    return filtered

