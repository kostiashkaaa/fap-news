#!/usr/bin/env python3
"""
FAP News - Poster Module
Handles message formatting and Telegram posting with AI summarization
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
from typing import Any, Dict, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
# Note: Translation and summarization handled by AI module (ai_summarizer.py)

from parser import NewsItem

logger = logging.getLogger(__name__)


# AI-powered translation and summarization


def make_hashtag(tag: str) -> str:
    tag = (tag or "").strip()
    if not tag:
        return ""
    if not tag.startswith("#"):
        return f"#{tag}"
    return tag


def clean_text(text: str) -> str:
    """Clean text from HTML tags, extra whitespace and fix encoding"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common RSS artifacts
    text = re.sub(r'utm_source=.*?(&|$)', '', text)
    text = re.sub(r'\?utm_.*', '', text)
    
    return text


def get_source_emoji(source_name: str) -> str:
    """Get emoji for different news sources"""
    source_lower = source_name.lower()
    
    if 'bbc' in source_lower:
        return '🇬🇧'
    elif 'rt' in source_lower or 'russia today' in source_lower:
        return '🇷🇺'
    elif 'lenta' in source_lower:
        return '📰'
    elif 'tass' in source_lower:
        return '📡'
    elif 'ria' in source_lower:
        return '📻'
    elif 'cnn' in source_lower:
        return '🇺🇸'
    elif 'fox' in source_lower:
        return '🦊'
    elif 'reuters' in source_lower:
        return '📈'
    elif 'voa' in source_lower or 'voice of america' in source_lower:
        return '🎙️'
    elif 'politico' in source_lower:
        return '🏛️'
    elif 'global voices' in source_lower:
        return '🌍'
    elif 'new york times' in source_lower or 'nyt' in source_lower:
        return '📰'
    elif 'washington post' in source_lower:
        return '📝'
    elif 'bloomberg' in source_lower:
        return '💰'
    elif 'guardian' in source_lower:
        return '🇬🇧'
    elif 'financial times' in source_lower or 'ft' in source_lower:
        return '💼'
    elif 'euronews' in source_lower:
        return '🇪🇺'
    elif 'deutsche welle' in source_lower or 'dw' in source_lower:
        return '🇩🇪'
    elif 'al jazeera' in source_lower or 'aljazeera' in source_lower:
        return '🏺'
    elif 'france 24' in source_lower:
        return '🇫🇷'
    elif 'south china morning post' in source_lower or 'scmp' in source_lower:
        return '🇭🇰'
    elif 'japan times' in source_lower:
        return '🇯🇵'
    else:
        return '📄'


def format_message(item: NewsItem, ai_summary: Optional[str] = None, is_urgent: bool = False) -> str:
    """Format news item for Telegram message (clean format without emojis)"""
    # Use AI summary if available
    content = clean_text(ai_summary) if ai_summary else ""
    link = item.link
    tag = make_hashtag(item.tag)
    
    # Escape for HTML (except link which will be HTML)
    content = html.escape(content)
    tag = html.escape(tag)

    parts = []
    
    # Add hashtag at the top (with lightning emoji if urgent)
    if tag:
        if is_urgent:
            parts.append(f"⚡{tag}")  # Lightning emoji with hashtag on same line
        else:
            parts.append(tag)
    
    # Add main content (AI summary)
    if content:
        parts.append(content)
    
    # Add source link as HTML link
    if link:
        parts.append(f'<a href="{link}">Читать полностью</a>')
    
    return "\n".join(parts)


async def send_to_telegram(bot_token: str, channel_id: str, text: str) -> None:
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await bot.send_message(chat_id=channel_id, text=text, disable_web_page_preview=True)
    finally:
        await bot.session.close()


async def post_news_item(
    item: NewsItem,
    config: Dict[str, Any],
    bot_token: Optional[str] = None,
    channel_id: Optional[str] = None,
    is_urgent: bool = False,
) -> None:
    # Initialize AI summarizer
    ai_config = config.get("ai_summarization", {})
    if ai_config.get("enabled", False):
        from ai_summarizer import AISummarizer
        summarizer = AISummarizer(ai_config)
    else:
        summarizer = None

    # Create AI summary (which includes translation for international sources)
    ai_summary = None
    if summarizer and summarizer.is_enabled():
        try:
            ai_summary = await summarizer.summarize(
                title=item.title,
                content=item.summary or "",
                link=item.link
            )
            logger.info(f"AI summary created: {len(ai_summary) if ai_summary else 0} chars")
        except Exception as e:
            logger.warning(f"AI summarization failed: {e}")

    # Use AI summary if available, otherwise use original summary only (no title)
    final_summary = ai_summary if ai_summary else (item.summary or "")
    
    message = format_message(item, final_summary, is_urgent=is_urgent)

    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Telegram bot token not provided. Set TELEGRAM_BOT_TOKEN env or pass bot_token.")
    channel = channel_id
    if not channel:
        raise RuntimeError("Telegram channel_id not provided.")

    await send_to_telegram(token, channel, message)
