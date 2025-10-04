#!/usr/bin/env python3
"""
News Importance Analyzer - анализ важности новостей для адаптивной длины сводок
"""

import logging
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ImportanceScore:
    """Оценка важности новости"""
    score: float  # 0-1
    category: str  # 'critical', 'high', 'medium', 'low'
    factors: List[str]  # факторы, влияющие на важность

class NewsImportanceAnalyzer:
    """Анализатор важности новостей"""
    
    def __init__(self):
        # Критические ключевые слова (максимальная важность)
        self.critical_keywords = {
            # Россия и Украина - МАКСИМАЛЬНЫЙ ПРИОРИТЕТ
            "россия", "russia", "российский", "russian", "рф", "rf", "путин", "putin",
            "украина", "ukraine", "украинский", "ukrainian", "зеленский", "zelensky",
            "донбасс", "donbass", "донецк", "donetsk", "луганск", "luhansk", "крым", "crimea",
            "херсон", "kherson", "запорожье", "zaporizhzhia", "мариуполь", "mariupol",
            "киев", "kyiv", "киевский", "kiev", "харьков", "kharkiv", "одесса", "odessa",
            "специальная операция", "special operation", "сво", "svo",
            
            # Военные действия
            "война", "war", "военные действия", "military action", "боевые действия", "combat",
            "вторжение", "invasion", "атака", "attack", "удар", "strike", "бомбардировка", "bombing",
            "взрыв", "explosion", "взрывы", "explosions", "терроризм", "terrorism", "террорист", "terrorist",
            
            # Политические кризисы
            "переворот", "coup", "революция", "revolution", "импичмент", "impeachment",
            "отставка", "resignation", "арест", "arrest", "задержание", "detention",
            "санкции", "sanctions", "эмбарго", "embargo", "блокада", "blockade",
            
            # Природные катастрофы
            "землетрясение", "earthquake", "цунами", "tsunami", "наводнение", "flood",
            "ураган", "hurricane", "торнадо", "tornado", "извержение", "eruption",
            "пожар", "fire", "катастрофа", "disaster", "авария", "accident",
            
            # Экономические кризисы
            "крах", "crash", "обвал", "collapse", "дефолт", "default",
            "банкротство", "bankruptcy", "рецессия", "recession", "кризис", "crisis",
            
            # Международные инциденты
            "дипломатический кризис", "diplomatic crisis", "конфликт", "conflict",
            "эскалация", "escalation", "угроза", "threat", "опасность", "danger",
            
            # Технологические кризисы
            "кибератака", "cyberattack", "хакеры", "hackers", "утечка данных", "data breach",
            "отключение", "outage", "сбой", "failure", "взлом", "hack"
        }
        
        # Высокоприоритетные ключевые слова
        self.high_priority_keywords = {
            # Политика
            "президент", "president", "премьер", "prime minister", "министр", "minister",
            "выборы", "election", "elections", "голосование", "voting", "референдум", "referendum",
            "парламент", "parliament", "конгресс", "congress", "сенат", "senate",
            
            # Экономика
            "инфляция", "inflation", "безработица", "unemployment", "валюта", "currency",
            "нефть", "oil", "газ", "gas", "энергетика", "energy", "рынок", "market",
            
            # Международные отношения
            "нато", "nato", "оон", "un", "united nations", "евросоюз", "eu", "european union",
            "саммит", "summit", "переговоры", "negotiations", "дипломатия", "diplomacy",
            
            # Социальные проблемы
            "протесты", "protests", "митинги", "rallies", "демонстрации", "demonstrations",
            "забастовка", "strike", "бунт", "riot", "беспорядки", "unrest"
        }
        
        # Важные имена и организации
        self.important_entities = {
            # Лидеры
            "путин", "putin", "зеленский", "zelenskyy", "zelensky", "байден", "biden",
            "трамп", "trump", "си цзиньпин", "xi jinping", "макрон", "macron",
            "шольц", "scholz", "сунак", "sunak", "лукашенко", "lukashenko",
            
            # Организации
            "кремль", "kremlin", "белый дом", "white house", "пентагон", "pentagon",
            "фсб", "fsb", "цру", "cia", "фбр", "fbi", "нса", "nsa",
            "европарламент", "european parliament", "бундестаг", "bundestag",
            
            # Страны и регионы
            "украина", "ukraine", "россия", "russia", "сша", "usa", "us", "america",
            "китай", "china", "европа", "europe", "нато", "nato", "ес", "eu"
        }
        
        # Числовые индикаторы важности
        self.importance_numbers = {
            "миллион", "million", "миллиард", "billion", "тысяча", "thousand",
            "процент", "percent", "%", "доллар", "dollar", "евро", "euro",
            "рубль", "ruble", "юань", "yuan"
        }
        
        # Фильтр неинтересных американских новостей
        self.uninteresting_us_keywords = {
            # Семейные дела и личная жизнь
            "family", "семья", "wife", "жена", "husband", "муж", "son", "сын", "daughter", "дочь",
            "mother", "мать", "father", "отец", "brother", "брат", "sister", "сестра",
            "wedding", "свадьба", "divorce", "развод", "marriage", "брак",
            
            # Знаменитости и развлечения
            "celebrity", "знаменитость", "actor", "актер", "actress", "актриса", "singer", "певец",
            "movie", "фильм", "tv show", "телешоу", "reality show", "реалити-шоу",
            "oscar", "оскар", "grammy", "грэмми", "award", "награда",
            
            # Спорт (кроме важных событий)
            "basketball", "баскетбол", "football", "футбол", "baseball", "бейсбол", "hockey", "хоккей",
            "nfl", "nba", "mlb", "nhl", "playoff", "плей-офф", "championship", "чемпионат",
            
            # Местные новости США
            "local", "местный", "city council", "городской совет", "mayor", "мэр", "governor", "губернатор",
            "state", "штат", "county", "округ", "district", "район",
            
            # Незначительные преступления
            "robbery", "ограбление", "theft", "кража", "vandalism", "вандализм", "arrest", "арест",
            "suspect", "подозреваемый", "wanted", "разыскивается"
        }
    
    def analyze_importance(self, title: str, content: str) -> ImportanceScore:
        """
        Анализирует важность новости
        
        Args:
            title: Заголовок новости
            content: Содержимое новости
            
        Returns:
            Оценка важности
        """
        full_text = f"{title} {content}".lower()
        factors = []
        score = 0.0
        
        # Проверяем критические ключевые слова
        critical_matches = sum(1 for keyword in self.critical_keywords if keyword in full_text)
        if critical_matches > 0:
            score += 0.5  # Увеличиваем вес критических событий
            factors.append(f"Критические события ({critical_matches} ключевых слов)")
            
            # Дополнительные баллы за множественные критические события
            if critical_matches >= 2:
                score += 0.2
                factors.append("Множественные критические события")
        
        # МАКСИМАЛЬНЫЙ ПРИОРИТЕТ для России и Украины
        ru_ua_keywords = ["россия", "russia", "украина", "ukraine", "путин", "putin", "зеленский", "zelensky", 
                         "донбасс", "donbass", "крым", "crimea", "специальная операция", "special operation"]
        ru_ua_matches = sum(1 for keyword in ru_ua_keywords if keyword in full_text)
        if ru_ua_matches > 0:
            score += 0.4  # Большой бонус за Россию/Украину
            factors.append(f"Россия/Украина ({ru_ua_matches} ключевых слов)")
        
        # Фильтр неинтересных американских новостей
        uninteresting_matches = sum(1 for keyword in self.uninteresting_us_keywords if keyword in full_text)
        if uninteresting_matches >= 3:  # Если много неинтересных слов
            score -= 0.5  # Сильнее снижаем важность
            factors.append(f"Неинтересная американская новость ({uninteresting_matches} слов)")
        
        # Дополнительный фильтр для семейных/личных новостей
        family_keywords = ["family", "семья", "wedding", "свадьба", "divorce", "развод", "anniversary", "годовщина"]
        family_matches = sum(1 for keyword in family_keywords if keyword in full_text)
        if family_matches >= 2:
            score -= 0.3
            factors.append(f"Семейные/личные новости ({family_matches} слов)")
        
        # Проверяем высокоприоритетные ключевые слова
        high_priority_matches = sum(1 for keyword in self.high_priority_keywords if keyword in full_text)
        if high_priority_matches > 0:
            score += 0.3
            factors.append(f"Высокий приоритет ({high_priority_matches} ключевых слов)")
        
        # Проверяем важные сущности
        entity_matches = sum(1 for entity in self.important_entities if entity in full_text)
        if entity_matches > 0:
            score += 0.2
            factors.append(f"Важные персоны/организации ({entity_matches})")
        
        # Проверяем числовые индикаторы
        number_matches = sum(1 for num in self.importance_numbers if num in full_text)
        if number_matches > 0:
            score += 0.1
            factors.append(f"Числовые данные ({number_matches})")
        
        # Дополнительные факторы
        if len(content) > 500:  # Длинный контент = больше информации
            score += 0.1
            factors.append("Объемный контент")
        
        if any(word in full_text for word in ["breaking", "urgent", "срочно", "экстренно"]):
            score += 0.2
            factors.append("Срочная новость")
        
        # Определяем категорию
        if score >= 0.7:
            category = "critical"
        elif score >= 0.5:
            category = "high"
        elif score >= 0.3:
            category = "medium"
        else:
            category = "low"
        
        return ImportanceScore(score=min(score, 1.0), category=category, factors=factors)
    
    def get_adaptive_length(self, importance: ImportanceScore, base_length: int = 500) -> int:
        """
        Определяет адаптивную длину сводки на основе важности
        
        Args:
            importance: Оценка важности
            base_length: Базовая длина
            
        Returns:
            Рекомендуемая длина сводки
        """
        if importance.category == "critical":
            return min(base_length * 2, 1200)  # До 1200 символов для критических новостей
        elif importance.category == "high":
            return min(base_length * 1.5, 900)  # До 900 символов для важных новостей
        elif importance.category == "medium":
            return base_length  # Стандартная длина 500
        else:
            return max(base_length * 0.8, 400)  # Минимум 400 символов для обычных новостей
    
    def should_include_details(self, importance: ImportanceScore) -> bool:
        """Определяет, нужно ли включать детали в сводку"""
        return importance.category in ["critical", "high"]


def test_importance_analyzer():
    """Тест анализатора важности"""
    analyzer = NewsImportanceAnalyzer()
    
    test_cases = [
        ("Взрыв в порту Бейрута: 218 погибших", "В результате взрыва аммиачной селитры в порту Бейрута погибли 218 человек, более 6000 пострадали. Взрыв произошел на складе, где хранились 2750 тонн селитры."),
        ("Курс доллара вырос на 2%", "Американская валюта укрепилась на мировых рынках после заявления ФРС о повышении процентной ставки."),
        ("Путин и Байден провели телефонный разговор", "Президенты России и США обсудили вопросы международной безопасности и двусторонних отношений."),
        ("Новая функция в Instagram", "Социальная сеть добавила возможность создавать истории с музыкой.")
    ]
    
    for title, content in test_cases:
        importance = analyzer.analyze_importance(title, content)
        length = analyzer.get_adaptive_length(importance)
        
        print(f"\nЗаголовок: {title}")
        print(f"Важность: {importance.category} ({importance.score:.2f})")
        print(f"Факторы: {', '.join(importance.factors)}")
        print(f"Рекомендуемая длина: {length} символов")
        print(f"Включать детали: {analyzer.should_include_details(importance)}")


if __name__ == "__main__":
    test_importance_analyzer()
