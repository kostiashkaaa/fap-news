#!/usr/bin/env python3
"""
AI Response Cache - кэширование ИИ-ответов для экономии API вызовов
"""

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class AICache:
    """Кэш для ИИ-ответов с SQLite хранилищем"""
    
    def __init__(self, cache_db_path: Optional[Path] = None):
        self.cache_db_path = cache_db_path or Path(__file__).parent / "ai_cache.sqlite3"
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Инициализация базы данных кэша"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE NOT NULL,
                    response_type TEXT NOT NULL,  -- 'summary', 'urgency', 'freshness'
                    response_content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    source_info TEXT,  -- информация об источнике для отладки
                    UNIQUE(content_hash, response_type)
                )
            """)
            
            # Создаем индекс для быстрого поиска
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash_type 
                ON ai_cache(content_hash, response_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON ai_cache(expires_at)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = sqlite3.connect(self.cache_db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _generate_content_hash(self, title: str, content: str, prompt_type: str = "") -> str:
        """Генерирует хэш для контента"""
        # Нормализуем текст для более точного сравнения
        normalized_text = f"{title.strip().lower()} {content.strip().lower()} {prompt_type}"
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()[:16]
    
    def get_cached_response(self, title: str, content: str, response_type: str) -> Optional[str]:
        """
        Получает кэшированный ответ ИИ
        
        Args:
            title: Заголовок новости
            content: Содержимое новости
            response_type: Тип ответа ('summary', 'urgency', 'freshness')
            
        Returns:
            Кэшированный ответ или None
        """
        content_hash = self._generate_content_hash(title, content, response_type)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response_content, expires_at 
                FROM ai_cache 
                WHERE content_hash = ? AND response_type = ? AND expires_at > ?
            """, (content_hash, response_type, datetime.utcnow().isoformat()))
            
            result = cursor.fetchone()
            if result:
                response_content, expires_at = result
                logger.info(f"🎯 Cache HIT for {response_type}: {title[:30]}...")
                return response_content
            
            logger.debug(f"Cache MISS for {response_type}: {title[:30]}...")
            return None
    
    def cache_response(self, title: str, content: str, response_type: str, 
                      response_content: str, ttl_hours: int = 24, 
                      source_info: str = "") -> None:
        """
        Кэширует ответ ИИ
        
        Args:
            title: Заголовок новости
            content: Содержимое новости
            response_type: Тип ответа
            response_content: Ответ ИИ
            ttl_hours: Время жизни кэша в часах
            source_info: Дополнительная информация об источнике
        """
        content_hash = self._generate_content_hash(title, content, response_type)
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=ttl_hours)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ai_cache 
                (content_hash, response_type, response_content, created_at, expires_at, source_info)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (content_hash, response_type, response_content, 
                  now.isoformat(), expires_at.isoformat(), source_info))
            conn.commit()
            
            logger.info(f"💾 Cached {response_type} response for: {title[:30]}...")
    
    def cleanup_expired(self) -> int:
        """Удаляет устаревшие записи из кэша"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM ai_cache WHERE expires_at <= ?
            """, (datetime.utcnow().isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} expired cache entries")
            
            return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Общее количество записей
            cursor.execute("SELECT COUNT(*) FROM ai_cache")
            total_entries = cursor.fetchone()[0]
            
            # Записи по типам
            cursor.execute("""
                SELECT response_type, COUNT(*) 
                FROM ai_cache 
                GROUP BY response_type
            """)
            by_type = dict(cursor.fetchall())
            
            # Устаревшие записи
            cursor.execute("""
                SELECT COUNT(*) FROM ai_cache WHERE expires_at <= ?
            """, (datetime.utcnow().isoformat(),))
            expired_entries = cursor.fetchone()[0]
            
            return {
                "total_entries": total_entries,
                "by_type": by_type,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries
            }
    
    def clear_cache(self, response_type: Optional[str] = None) -> int:
        """Очищает кэш (полностью или по типу)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if response_type:
                cursor.execute("DELETE FROM ai_cache WHERE response_type = ?", (response_type,))
            else:
                cursor.execute("DELETE FROM ai_cache")
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"🗑️ Cleared {deleted_count} cache entries" + 
                       (f" of type '{response_type}'" if response_type else ""))
            
            return deleted_count


# Глобальный экземпляр кэша
_ai_cache = None

def get_ai_cache() -> AICache:
    """Получает глобальный экземпляр кэша"""
    global _ai_cache
    if _ai_cache is None:
        _ai_cache = AICache()
    return _ai_cache


if __name__ == "__main__":
    # Тестирование кэша
    import logging
    logging.basicConfig(level=logging.INFO)
    
    cache = AICache()
    
    # Тест кэширования
    title = "Test News Title"
    content = "Test news content for caching"
    
    # Кэшируем ответ
    cache.cache_response(title, content, "summary", "Test summary response", ttl_hours=1)
    
    # Получаем из кэша
    cached = cache.get_cached_response(title, content, "summary")
    print(f"Cached response: {cached}")
    
    # Статистика
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")
