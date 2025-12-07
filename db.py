#!/usr/bin/env python3
"""
FAP News - Database Module
SQLite database operations with retry logic and proper error handling
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

DB_FILE = Path(__file__).with_name("fap_news.sqlite3")

# Database schema version for future migrations
SCHEMA_VERSION = 1


class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception for connection errors"""
    pass


class DatabaseOperationError(DatabaseError):
    """Exception for operation errors"""
    pass


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """
    Context manager for database connections with proper error handling
    
    Args:
        db_path: Optional path to database file
        
    Yields:
        SQLite connection object
        
    Raises:
        DatabaseConnectionError: If connection fails
    """
    path = db_path or DB_FILE
    connection = None
    try:
        connection = sqlite3.connect(path, timeout=30.0)
        connection.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        connection.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        yield connection
    except sqlite3.OperationalError as e:
        logger.error(f"Database operational error: {e}")
        raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database error: {e}") from e
    finally:
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initialize database with schema
    
    Args:
        db_path: Optional path to database file
        
    Raises:
        DatabaseError: If initialization fails
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Create main table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS published (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(news_id, source)
                )
                """
            )
            
            # Create schema version table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            # Check and update schema version
            cursor.execute("SELECT MAX(version) FROM schema_version")
            current_version = cursor.fetchone()[0] or 0
            
            if current_version < SCHEMA_VERSION:
                # Apply migrations here in the future
                cursor.execute(
                    "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,)
                )
                logger.info(f"Database schema updated to version {SCHEMA_VERSION}")
            
            # Create indexes for better performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_source 
                ON published(news_id, source)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_published_at 
                ON published(published_at)
                """
            )
            
            conn.commit()
            logger.debug("Database initialized successfully")
            
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Failed to initialize database: {e}") from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(sqlite3.OperationalError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def mark_published(
    news_id: str, 
    url: str, 
    source: str, 
    published_at: str, 
    db_path: Optional[Path] = None
) -> bool:
    """
    Mark a news item as published with retry logic
    
    Args:
        news_id: Unique news ID
        url: News URL
        source: News source name
        published_at: Publication timestamp
        db_path: Optional path to database file
        
    Returns:
        True if marked successfully, False if already exists
        
    Raises:
        DatabaseOperationError: If operation fails after retries
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO published (news_id, url, source, published_at)
                VALUES (?, ?, ?, ?)
                """,
                (news_id, url, source, published_at),
            )
            conn.commit()
            
            # Check if row was actually inserted
            if cursor.rowcount > 0:
                logger.debug(f"Marked as published: {news_id[:16]}... from {source}")
                return True
            else:
                logger.debug(f"Already published: {news_id[:16]}... from {source}")
                return False
                
    except DatabaseError:
        raise
    except sqlite3.OperationalError as e:
        logger.warning(f"Operational error marking published (will retry): {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to mark published: {e}")
        raise DatabaseOperationError(f"Failed to mark published: {e}") from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(sqlite3.OperationalError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def is_published(news_id: str, source: str, db_path: Optional[Path] = None) -> bool:
    """
    Check if a news item was already published with retry logic
    
    Args:
        news_id: Unique news ID
        source: News source name
        db_path: Optional path to database file
        
    Returns:
        True if already published, False otherwise
        
    Raises:
        DatabaseOperationError: If operation fails after retries
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM published WHERE news_id = ? AND source = ? LIMIT 1
                """,
                (news_id, source),
            )
            result = cursor.fetchone() is not None
            return result
            
    except DatabaseError:
        raise
    except sqlite3.OperationalError as e:
        logger.warning(f"Operational error checking published (will retry): {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to check published status: {e}")
        raise DatabaseOperationError(f"Failed to check published status: {e}") from e


def get_last_published(
    limit: int = 20, 
    db_path: Optional[Path] = None
) -> List[Tuple[str, str, str, str]]:
    """
    Get last published news items
    
    Args:
        limit: Maximum number of items to return
        db_path: Optional path to database file
        
    Returns:
        List of tuples (news_id, url, source, published_at)
        
    Raises:
        DatabaseOperationError: If operation fails
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT news_id, url, source, published_at
                FROM published
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()
            
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Failed to get last published: {e}")
        raise DatabaseOperationError(f"Failed to get last published: {e}") from e


def get_published_count(db_path: Optional[Path] = None) -> int:
    """
    Get total count of published news items
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        Total count of published items
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM published")
            return cursor.fetchone()[0]
            
    except Exception as e:
        logger.error(f"Failed to get published count: {e}")
        return 0


def cleanup_old_entries(days: int = 30, db_path: Optional[Path] = None) -> int:
    """
    Remove old entries from the database
    
    Args:
        days: Number of days to keep
        db_path: Optional path to database file
        
    Returns:
        Number of deleted entries
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM published 
                WHERE created_at < datetime('now', ?)
                """,
                (f"-{days} days",),
            )
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old entries (older than {days} days)")
            
            return deleted
            
    except Exception as e:
        logger.error(f"Failed to cleanup old entries: {e}")
        return 0


def get_database_stats(db_path: Optional[Path] = None) -> dict:
    """
    Get database statistics
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        Dictionary with database statistics
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Total count
            cursor.execute("SELECT COUNT(*) FROM published")
            total = cursor.fetchone()[0]
            
            # Count by source
            cursor.execute(
                """
                SELECT source, COUNT(*) as count 
                FROM published 
                GROUP BY source 
                ORDER BY count DESC
                """
            )
            by_source = dict(cursor.fetchall())
            
            # Schema version
            cursor.execute("SELECT MAX(version) FROM schema_version")
            schema_version = cursor.fetchone()[0] or 0
            
            # Database file size
            db_file = db_path or DB_FILE
            file_size = db_file.stat().st_size if db_file.exists() else 0
            
            return {
                "total_entries": total,
                "by_source": by_source,
                "schema_version": schema_version,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
            
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            "total_entries": 0,
            "by_source": {},
            "schema_version": 0,
            "file_size_bytes": 0,
            "file_size_mb": 0,
            "error": str(e)
        }
