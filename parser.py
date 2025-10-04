#!/usr/bin/env python3
"""
FAP News - Parser Module
Handles RSS/HTML parsing and news item filtering
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import feedparser
import httpx
from bs4 import BeautifulSoup


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
    import html
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
    rss_url = source.get("rss")
    if not rss_url:
        return []
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
    return items


def parse_html(source: Dict[str, Any]) -> List[NewsItem]:
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
    except Exception:
        # Silently ignore HTML sources errors to keep the job robust
        return []

    return items


def filter_items(
    items: Iterable[NewsItem],
    include_keywords: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None,
    max_age_hours: int = 24,
    max_age_minutes: Optional[int] = None,
) -> List[NewsItem]:
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
    return filtered


def load_config(path: str) -> Dict[str, Any]:
    import json

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_news(config: Dict[str, Any]) -> List[NewsItem]:
    all_items: List[NewsItem] = []
    for src in config.get("sources", []):
        if src.get("rss"):
            all_items.extend(parse_rss(src))
        else:
            all_items.extend(parse_html(src))

    filters_cfg = config.get("filters", {})
    include_kw = filters_cfg.get("include_keywords", [])
    exclude_kw = filters_cfg.get("exclude_keywords", [])
    max_age_hours = filters_cfg.get("max_age_hours", 24)
    max_age_minutes = filters_cfg.get("max_age_minutes")
    
    return filter_items(all_items, include_kw, exclude_kw, max_age_hours, max_age_minutes)
