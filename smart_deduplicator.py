#!/usr/bin/env python3
"""
Smart Deduplicator - умная фильтрация дубликатов новостей по смыслу
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
from difflib import SequenceMatcher

from parser import NewsItem

logger = logging.getLogger(__name__)

@dataclass
class SimilarityResult:
    """Результат сравнения новостей"""
    similarity_score: float  # 0-1
    is_duplicate: bool
    reason: str

class SmartDeduplicator:
    """Умный дедупликатор новостей"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.similarity_threshold = config.get("similarity_threshold", 0.7)
        self.title_weight = config.get("title_weight", 0.6)
        self.content_weight = config.get("content_weight", 0.4)
        self.min_content_length = config.get("min_content_length", 20)
        
        # Кэш для быстрого поиска дубликатов
        self._processed_hashes: Set[str] = set()
        self._content_hashes: Dict[str, NewsItem] = {}
    
    def _normalize_text(self, text: str) -> str:
        """Нормализация текста для сравнения"""
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Удаляем знаки препинания для лучшего сравнения
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Извлекает ключевые фразы из текста"""
        normalized = self._normalize_text(text)
        
        # Разбиваем на слова
        words = normalized.split()
        
        # Фильтруем стоп-слова
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'об', 'за', 'при',
            'the', 'and', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'объявил', 'объявила', 'объявили', 'заявил', 'заявила', 'заявили', 'сообщил', 'сообщила', 'сообщили'
        }
        
        # Извлекаем значимые слова (длиннее 2 символов, не стоп-слова)
        key_words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Создаем биграммы и триграммы для лучшего сравнения
        bigrams = []
        trigrams = []
        
        for i in range(len(key_words) - 1):
            bigrams.append(f"{key_words[i]} {key_words[i+1]}")
            
        for i in range(len(key_words) - 2):
            trigrams.append(f"{key_words[i]} {key_words[i+1]} {key_words[i+2]}")
        
        return key_words + bigrams + trigrams
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет схожесть между двумя текстами"""
        if not text1 or not text2:
            return 0.0
        
        # Нормализуем тексты
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Используем SequenceMatcher для базового сравнения
        basic_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Извлекаем ключевые фразы
        phrases1 = set(self._extract_key_phrases(text1))
        phrases2 = set(self._extract_key_phrases(text2))
        
        if not phrases1 or not phrases2:
            return basic_similarity
        
        # Вычисляем пересечение ключевых фраз
        intersection = phrases1.intersection(phrases2)
        union = phrases1.union(phrases2)
        
        phrase_similarity = len(intersection) / len(union) if union else 0.0
        
        # Комбинируем результаты
        combined_similarity = (basic_similarity * 0.3) + (phrase_similarity * 0.7)
        
        return min(combined_similarity, 1.0)
    
    def _generate_content_hash(self, item: NewsItem) -> str:
        """Генерирует хэш контента для быстрого поиска"""
        # Используем нормализованный текст для хэша
        normalized_title = self._normalize_text(item.title)
        normalized_content = self._normalize_text(item.summary or "")
        
        # Создаем хэш из ключевых фраз
        key_phrases = self._extract_key_phrases(f"{normalized_title} {normalized_content}")
        key_phrases_str = " ".join(sorted(key_phrases))
        
        return hashlib.md5(key_phrases_str.encode('utf-8')).hexdigest()[:12]
    
    def find_duplicates(self, items: List[NewsItem]) -> List[SimilarityResult]:
        """
        Находит дубликаты в списке новостей
        
        Args:
            items: Список новостей для проверки
            
        Returns:
            Список результатов сравнения
        """
        results = []
        
        for i, item in enumerate(items):
            if not item.title or len(item.title.strip()) < 5:
                results.append(SimilarityResult(0.0, False, "Слишком короткий заголовок"))
                continue
            
            # Проверяем быстрый хэш-кэш
            content_hash = self._generate_content_hash(item)
            if content_hash in self._processed_hashes:
                results.append(SimilarityResult(1.0, True, "Точный дубликат по хэшу"))
                continue
            
            # Ищем похожие новости
            max_similarity = 0.0
            best_match = None
            
            for j, other_item in enumerate(items):
                if i == j or not other_item.title:
                    continue
                
                # Сравниваем заголовки
                title_similarity = self._calculate_similarity(item.title, other_item.title)
                
                # Сравниваем содержимое (если есть)
                content_similarity = 0.0
                if item.summary and other_item.summary:
                    content_similarity = self._calculate_similarity(item.summary, other_item.summary)
                
                # Вычисляем общую схожесть
                total_similarity = (title_similarity * self.title_weight + 
                                  content_similarity * self.content_weight)
                
                if total_similarity > max_similarity:
                    max_similarity = total_similarity
                    best_match = other_item
            
            # Определяем, является ли дубликатом
            is_duplicate = max_similarity >= self.similarity_threshold
            
            if is_duplicate:
                reason = f"Похож на '{best_match.title[:50]}...' (схожесть: {max_similarity:.2f})"
            else:
                reason = f"Уникальная новость (макс. схожесть: {max_similarity:.2f})"
            
            results.append(SimilarityResult(max_similarity, is_duplicate, reason))
            
            # Добавляем в кэш только если не дубликат
            if not is_duplicate:
                self._processed_hashes.add(content_hash)
                self._content_hashes[content_hash] = item
        
        return results
    
    def filter_duplicates(self, items: List[NewsItem]) -> Tuple[List[NewsItem], List[NewsItem]]:
        """
        Фильтрует дубликаты из списка новостей
        
        Args:
            items: Список новостей
            
        Returns:
            Кортеж (уникальные_новости, дубликаты)
        """
        if not items:
            return [], []
        
        logger.info(f"🔍 Checking {len(items)} items for duplicates...")
        
        results = self.find_duplicates(items)
        
        unique_items = []
        duplicate_items = []
        
        for item, result in zip(items, results):
            if result.is_duplicate:
                duplicate_items.append(item)
                logger.info(f"🚫 DUPLICATE: '{item.title[:50]}...' - {result.reason}")
            else:
                unique_items.append(item)
        
        logger.info(f"✅ Found {len(duplicate_items)} duplicates, {len(unique_items)} unique items")
        
        return unique_items, duplicate_items
    
    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику дедупликатора"""
        return {
            "processed_hashes": len(self._processed_hashes),
            "content_hashes": len(self._content_hashes),
            "similarity_threshold": self.similarity_threshold
        }


def test_deduplicator():
    """Тест дедупликатора"""
    from parser import NewsItem
    
    # Создаем тестовые новости
    items = [
        NewsItem(
            id="1",
            title="Президент США объявил о новых санкциях против России",
            summary="Белый дом ввел дополнительные экономические ограничения",
            link="https://example.com/1",
            source="CNN",
            published_at="2025-01-16T10:00:00Z",
            tag="#cnn"
        ),
        NewsItem(
            id="2", 
            title="США вводят новые санкции против РФ",
            summary="Администрация Байдена объявила о дополнительных мерах",
            link="https://example.com/2",
            source="BBC",
            published_at="2025-01-16T10:05:00Z",
            tag="#bbc"
        ),
        NewsItem(
            id="3",
            title="Курс доллара вырос на 2%",
            summary="Американская валюта укрепилась на мировых рынках",
            link="https://example.com/3",
            source="Reuters",
            published_at="2025-01-16T10:10:00Z",
            tag="#reuters"
        )
    ]
    
    config = {
        "similarity_threshold": 0.6,  # Разумный порог для продакшена
        "title_weight": 0.7,
        "content_weight": 0.3
    }
    
    deduplicator = SmartDeduplicator(config)
    
    # Тестируем сравнение напрямую
    print("=== Тест сравнения ===")
    item1 = items[0]
    item2 = items[1]
    
    similarity = deduplicator._calculate_similarity(item1.title, item2.title)
    print(f"Схожесть '{item1.title}' и '{item2.title}': {similarity:.3f}")
    
    phrases1 = deduplicator._extract_key_phrases(item1.title)
    phrases2 = deduplicator._extract_key_phrases(item2.title)
    print(f"Ключевые фразы 1: {phrases1[:10]}")
    print(f"Ключевые фразы 2: {phrases2[:10]}")
    
    unique, duplicates = deduplicator.filter_duplicates(items)
    
    print(f"\nУникальные: {len(unique)}")
    print(f"Дубликаты: {len(duplicates)}")
    
    for item in unique:
        print(f"✅ {item.title}")
    
    for item in duplicates:
        print(f"🚫 {item.title}")


if __name__ == "__main__":
    test_deduplicator()
