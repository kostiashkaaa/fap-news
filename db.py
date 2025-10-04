import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple

DB_FILE = Path(__file__).with_name("fap_news.sqlite3")


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    path = db_path or DB_FILE
    connection = sqlite3.connect(path)
    try:
        yield connection
    finally:
        connection.close()


def init_db(db_path: Optional[Path] = None) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS published (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                published_at TEXT NOT NULL,
                UNIQUE(news_id, source)
            )
            """
        )
        conn.commit()


def mark_published(news_id: str, url: str, source: str, published_at: str, db_path: Optional[Path] = None) -> None:
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


def is_published(news_id: str, source: str, db_path: Optional[Path] = None) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM published WHERE news_id = ? AND source = ? LIMIT 1
            """,
            (news_id, source),
        )
        return cursor.fetchone() is not None


def get_last_published(limit: int = 20, db_path: Optional[Path] = None) -> list[Tuple[str, str, str, str]]:
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
