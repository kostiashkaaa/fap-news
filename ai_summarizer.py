import asyncio
import logging
import os
import re
from typing import Optional
from groq import Groq

from ai_cache import get_ai_cache
from news_importance_analyzer import NewsImportanceAnalyzer

logger = logging.getLogger(__name__)

def truncate_by_sentences(text: str, max_length: int) -> str:
    """Truncate text by complete sentences, not by characters"""
    if len(text) <= max_length:
        return text
    
    # Find all sentence endings
    sentences = re.split(r'[.!?]+', text)
    result = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Add sentence ending back
        if sentence and not sentence.endswith(('.', '!', '?')):
            sentence += '.'
        
        # Check if adding this sentence would exceed max_length
        if len(result + sentence + ' ') > max_length:
            break
            
        result += sentence + ' '
    
    return result.strip()

class AISummarizer:
    """AI-powered news summarizer using Groq API"""
    
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)
        self.provider = config.get("provider", "groq")
        self.model_name = config.get("model", "llama-3.1-8b-instant")
        self.max_length = config.get("max_summary_length", 200)
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 256)
        
        # Rate limiting settings
        rate_limit_cfg = config.get("rate_limit", {})
        self.delay_between_calls = rate_limit_cfg.get("delay_between_calls", 0.5)
        
        # Cache settings
        self.cache_enabled = config.get("cache_enabled", True)
        self.cache_ttl_hours = config.get("cache_ttl_hours", 24)
        self.cache = get_ai_cache() if self.cache_enabled else None
        
        # Importance analyzer
        self.importance_analyzer = NewsImportanceAnalyzer()
        
        # Initialize Groq client
        api_key = config.get("api_key") or os.getenv("GROQ_API_KEY")
        
        if not api_key and self.enabled:
            logger.warning("Groq API key not found. AI summarization will be disabled.")
            self.enabled = False
        
        if self.enabled and api_key:
            self.client = Groq(api_key=api_key)
        else:
            self.client = None
    
    async def _call_groq_api(self, prompt: str) -> Optional[str]:
        """Call Groq API with rate limiting"""
        try:
            # Добавляем задержку для избежания rate limit
            await asyncio.sleep(self.delay_between_calls)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный редактор новостей. Переводи на русский язык и создавай краткие, информативные сводки. Сохраняй все важные детали: имена, места, даты, цифры."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            if response.choices and response.choices[0].message.content:
                summary = response.choices[0].message.content.strip()
                # Truncate by complete sentences, not by characters
                summary = truncate_by_sentences(summary, self.max_length)
                logger.info(f"Groq summary created: {len(summary)} chars")
                return summary
            else:
                logger.warning("Groq returned empty response")
                return None
                
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                logger.warning(f"Groq rate limit hit, waiting 5 seconds: {e}")
                await asyncio.sleep(5)
                return None
            else:
                logger.error(f"Groq API error: {e}")
                return None

    async def summarize(self, title: str, content: str, link: str) -> Optional[str]:
        """
        Create AI-powered summary of news content using Groq API with caching
        
        Args:
            title: News title
            content: News content/description
            link: Link to original article
            
        Returns:
            Summarized content or None if failed
        """
        if not self.enabled or not self.client:
            return None
        
        # Проверяем кэш
        if self.cache:
            cached_summary = self.cache.get_cached_response(title, content, "summary")
            if cached_summary:
                return cached_summary
        
        # Анализируем важность новости
        importance = self.importance_analyzer.analyze_importance(title, content)
        adaptive_length = self.importance_analyzer.get_adaptive_length(importance, self.max_length)
        include_details = self.importance_analyzer.should_include_details(importance)
        
        logger.info(f"📊 News importance: {importance.category} (score: {importance.score:.2f}), length: {adaptive_length}")
        
        # Создаем адаптивный промпт для статей в стиле Varlamov News
        if importance.category == "critical":
            length_instruction = f"Создай ПОЛНУЮ СТАТЬЮ до {adaptive_length} символов с ВСЕМИ деталями"
            detail_instruction = "Включи ВСЕ важные детали: имена, места, даты, цифры, организации, контекст событий, причины, последствия, историю вопроса, мнения экспертов"
        elif importance.category == "high":
            length_instruction = f"Создай РАЗВЕРНУТУЮ СТАТЬЮ до {adaptive_length} символов"
            detail_instruction = "Включи ключевые детали: имена, места, даты, цифры, основные факты, контекст, последствия"
        else:
            length_instruction = f"Создай ИНФОРМАТИВНУЮ СТАТЬЮ до {adaptive_length} символов"
            detail_instruction = "Включи основную информацию, важные детали и контекст"
        
        prompt = f"""Ты профессиональный журналист в стиле Varlamov News. Твоя задача - перевести новость на русский язык и создать ПОЛНУЮ СТАТЬЮ.

ПРАВИЛА:
1. ВСЕГДА переводи на русский язык - никакого английского текста
2. {length_instruction}
3. {detail_instruction}
4. Пиши простым, понятным языком как в Varlamov News
5. НЕ используй заголовки - сразу начинай с сути новости
6. НЕ используй форматирование ** или другие символы
7. НЕ начинай с упоминания страны (Великобритания:, США:, и т.д.)
8. Создай ПОЛНУЮ СТАТЬЮ - люди должны прочитать всю новость в Telegram
9. Структурируй информацию логично: что произошло, почему, какие последствия
10. Включи ВСЕ важные детали из оригинальной новости
11. Добавь контекст и объяснения для лучшего понимания
12. ОБЯЗАТЕЛЬНО используй абзацы - разделяй текст на 2-3 абзаца
13. Между абзацами делай пустую строку для лучшей читаемости
14. Первый абзац - краткое изложение, остальные - детали

ВАЖНОСТЬ НОВОСТИ: {importance.category.upper()} (факторы: {', '.join(importance.factors)})

Заголовок: {title}
Описание: {content}
Ссылка: {link}

Создай ПОЛНУЮ СТАТЬЮ в стиле Varlamov News на русском языке с правильными абзацами:"""
        
        summary = await self._call_groq_api(prompt)
        
        # Проверяем качество сводки
        if not summary or len(summary.strip()) < 10:
            logger.warning(f"Poor quality summary (length: {len(summary) if summary else 0}), retrying...")
            
            # Повторный запрос с более строгими инструкциями
            retry_prompt = f"""СРОЧНО! Создай качественную СТАТЬЮ в стиле Varlamov News на русском языке. 

ТРЕБОВАНИЯ:
- Минимум 200 символов
- Только русский язык
- Полные предложения
- Вся важная информация
- БЕЗ заголовков - сразу с сути
- НЕ начинай с упоминания страны
- ОБЯЗАТЕЛЬНО раздели на 2-3 абзаца
- Между абзацами делай пустую строку
- Первый абзац - краткое изложение
- Остальные абзацы - детали и контекст

Заголовок: {title}
Описание: {content}

Статья на русском с абзацами:"""
            
            summary = await self._call_groq_api(retry_prompt)
            
            if not summary or len(summary.strip()) < 10:
                logger.error(f"Failed to create quality summary for: {title[:50]}...")
                # Возвращаем простой перевод заголовка как fallback без упоминания страны
                simple_title = title.replace("UK", "Великобритания").replace("watchdog", "надзорный орган").replace("cuts", "снижает").replace("productivity", "производительность").replace("forecast", "прогноз").replace("worsening", "усугубляя").replace("budget", "бюджетный").replace("deficit", "дефицит")
                summary = simple_title
        
        # Проверяем на английский язык в сводке
        if summary and self._contains_english(summary):
            logger.warning(f"Summary contains English text, retrying translation...")
            
            # Повторный запрос с акцентом на перевод
            translation_prompt = f"""ПЕРЕВЕДИ ЭТУ НОВОСТЬ НА РУССКИЙ ЯЗЫК! Никакого английского текста!

Заголовок: {title}
Описание: {content}

Переведи и создай ПОЛНУЮ СТАТЬЮ в стиле Varlamov News ТОЛЬКО на русском языке:
- НЕ начинай с упоминания страны
- Сразу с сути новости
- ОБЯЗАТЕЛЬНО раздели на 2-3 абзаца
- Между абзацами делай пустую строку
- Первый абзац - краткое изложение, остальные - детали"""
            
            summary = await self._call_groq_api(translation_prompt)
            
            if summary and self._contains_english(summary):
                logger.error(f"Failed to translate summary properly, using fallback")
                # Создаем простой перевод заголовка без упоминания страны
                simple_title = title.replace("UK", "Великобритания").replace("watchdog", "надзорный орган").replace("cuts", "снижает").replace("productivity", "производительность").replace("forecast", "прогноз").replace("worsening", "усугубляя").replace("budget", "бюджетный").replace("deficit", "дефицит")
                summary = simple_title
        
        # Постобработка: удаляем лишнее форматирование
        if summary:
            summary = self._clean_formatting(summary)
        
        # Кэшируем результат
        if summary and self.cache:
            self.cache.cache_response(
                title, content, "summary", summary, 
                ttl_hours=self.cache_ttl_hours,
                source_info=f"link:{link}"
            )
        
        return summary

    async def check_urgency(self, title: str, content: str) -> bool:
        """
        Check if news is urgent and should be posted immediately with caching
        
        Args:
            title: News title
            content: News content/description
            
        Returns:
            True if news is urgent, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        # Проверяем кэш
        if self.cache:
            cached_result = self.cache.get_cached_response(title, content, "urgency")
            if cached_result:
                return cached_result.lower() == "true"
        
        # Ключевые слова для срочных новостей
        urgency_keywords = [
            # Критические события
            "взрыв", "взрывы", "взорвался", "взорвались", "explosion", "explosions", "bomb", "bombs",
            "стрельба", "стреляют", "shooting", "gunfire", "attack", "attacks", "terrorist", "terrorism",
            "убийство", "убит", "убиты", "murder", "killed", "death", "deaths", "casualties",
            "авария", "катастрофа", "крушение", "crash", "accident", "disaster", "emergency",
            
            # Военные действия
            "война", "war", "военные действия", "military action", "боевые действия", "combat",
            "нападение", "attack", "атака", "strike", "удар", "bombing", "бомбардировка",
            "вторжение", "invasion", "оккупация", "occupation", "блокада", "blockade",
            
            # Политические кризисы
            "переворот", "coup", "революция", "revolution", "мятеж", "rebellion", "восстание", "uprising",
            "отставка", "resignation", "импичмент", "impeachment", "арест", "arrest", "задержание",
            "санкции", "sanctions", "эмбарго", "embargo", "блокировка", "blockade",
            
            # Природные катастрофы
            "землетрясение", "earthquake", "цунами", "tsunami", "наводнение", "flood", "пожар", "fire",
            "ураган", "hurricane", "торнадо", "tornado", "извержение", "eruption",
            
            # Технологические кризисы
            "кибератака", "cyberattack", "хакеры", "hackers", "утечка данных", "data breach",
            "отключение", "outage", "сбой", "failure", "кризис", "crisis",
            
            # Экономические кризисы
            "крах", "crash", "обвал", "collapse", "дефолт", "default", "банкротство", "bankruptcy",
            "рецессия", "recession", "депрессия", "depression", "инфляция", "inflation",
            
            # Международные инциденты
            "дипломатический кризис", "diplomatic crisis", "конфликт", "conflict", "эскалация", "escalation",
            "угроза", "threat", "предупреждение", "warning", "опасность", "danger"
        ]
        
        # Объединяем заголовок и контент для анализа
        full_text = f"{title} {content}".lower()
        
        # Проверяем наличие ключевых слов
        for keyword in urgency_keywords:
            if keyword.lower() in full_text:
                logger.info(f"Urgent news detected: keyword '{keyword}' found in '{title[:50]}...'")
                # Кэшируем результат
                if self.cache:
                    self.cache.cache_response(title, content, "urgency", "true", ttl_hours=self.cache_ttl_hours)
                return True
        
        # Дополнительная проверка через ИИ для сложных случаев
        try:
            urgency_prompt = f"""Проанализируй эту новость и определи, является ли она СРОЧНОЙ и требует немедленной публикации.

Критерии срочности:
- Критические события (взрывы, атаки, катастрофы)
- Военные действия и конфликты
- Политические кризисы и перевороты
- Природные катастрофы
- Технологические кризисы
- Экономические кризисы
- Международные инциденты

Заголовок: {title}
Описание: {content}

Ответь только "ДА" если новость срочная, или "НЕТ" если обычная:"""
            
            response = await self._call_groq_api(urgency_prompt)
            is_urgent = response and "ДА" in response.upper()
            
            # Кэшируем результат
            if self.cache:
                self.cache.cache_response(
                    title, content, "urgency", 
                    "true" if is_urgent else "false", 
                    ttl_hours=self.cache_ttl_hours
                )
            
            if is_urgent:
                logger.info(f"AI detected urgent news: '{title[:50]}...'")
                return True
                
        except Exception as e:
            logger.warning(f"AI urgency check failed: {e}")
        
        return False

    async def check_news_freshness(self, title: str, content: str, max_age_minutes: int = 120) -> bool:
        """
        Check if news is fresh enough to be published with caching
        
        Args:
            title: News title
            content: News content/description
            max_age_minutes: Maximum age in minutes (default 120 = 2 hours)
            
        Returns:
            True if news is fresh enough, False otherwise
        """
        if not self.enabled or not self.client:
            return True  # If AI is not available, assume news is fresh
        
        # Проверяем кэш
        if self.cache:
            cached_result = self.cache.get_cached_response(title, content, "freshness")
            if cached_result:
                return cached_result.lower() == "true"
        
        # Ключевые слова для определения времени
        time_keywords = [
            # Время
            "час", "часа", "часов", "hour", "hours", "минут", "минуты", "minute", "minutes",
            "сегодня", "today", "вчера", "yesterday", "завтра", "tomorrow",
            "утром", "morning", "днем", "afternoon", "вечером", "evening", "ночью", "night",
            "сейчас", "now", "только что", "just now", "недавно", "recently",
            
            # Даты
            "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря",
            "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
            "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            
            # Числа (для времени)
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24",
            "30", "45", "60", "90", "120", "180", "240", "300", "360", "480", "720", "1440"
        ]
        
        # Объединяем заголовок и контент для анализа
        full_text = f"{title} {content}".lower()
        
        # Проверяем наличие временных указаний
        has_time_reference = any(keyword in full_text for keyword in time_keywords)
        
        if not has_time_reference:
            # Если нет временных указаний, считаем новость свежей
            if self.cache:
                self.cache.cache_response(title, content, "freshness", "true", ttl_hours=self.cache_ttl_hours)
            return True
        
        # Дополнительная проверка через ИИ для определения свежести
        try:
            freshness_prompt = f"""Проанализируй эту новость и определи, является ли она СВЕЖЕЙ (опубликована не более {max_age_minutes} минут назад).

Критерии свежести:
- Новость должна быть актуальной и недавней
- Если есть указания на время (часы, минуты, "сегодня", "сейчас", "только что") - учитывай их
- Если новость старая (вчера, на прошлой неделе, месяц назад) - она НЕ свежая
- Если нет четких временных указаний, но новость выглядит актуальной - считай свежей

Заголовок: {title}
Описание: {content}

ВАЖНО: Ответь ТОЛЬКО одним словом: "ДА" или "НЕТ". Никаких дополнительных объяснений."""
            
            response = await self._call_groq_api(freshness_prompt)
            is_fresh = True  # По умолчанию считаем свежей
            
            if response:
                response_upper = response.upper().strip()
                if "НЕТ" in response_upper or "NO" in response_upper:
                    logger.info(f"Old news detected: '{title[:50]}...' - AI says it's not fresh")
                    is_fresh = False
                elif "ДА" in response_upper or "YES" in response_upper:
                    logger.info(f"Fresh news confirmed: '{title[:50]}...' - AI says it's fresh")
                    is_fresh = True
                else:
                    # Если ответ неясный, считаем новость свежей
                    logger.info(f"Unclear freshness response for '{title[:50]}...': '{response}' - assuming fresh")
                    is_fresh = True
            
            # Кэшируем результат
            if self.cache:
                self.cache.cache_response(
                    title, content, "freshness", 
                    "true" if is_fresh else "false", 
                    ttl_hours=self.cache_ttl_hours
                )
            
            return is_fresh
                
        except Exception as e:
            logger.warning(f"AI freshness check failed: {e}")
        
        # Если ИИ не смог определить, считаем новость свежей
        return True
    
    def _contains_english(self, text: str) -> bool:
        """Проверяет, содержит ли текст английские слова"""
        if not text:
            return False
        
        # Простая проверка на английские слова
        english_words = [
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'a', 'an', 'news', 'breaking', 'urgent', 'update', 'report', 'says', 'said', 'told',
            'according', 'source', 'sources', 'official', 'government', 'president', 'minister',
            'military', 'police', 'security', 'attack', 'war', 'conflict', 'crisis', 'emergency',
            'amazon', 'prime', 'deal', 'days', 'big', 'deals', 'members', 'access', 'midnight',
            'october', 'company', 'expects', 'biggest', 'shopping', 'event', 'year', 'discounts',
            'select', 'items', 'electronics', 'home', 'goods', 'fashion', 'categories',
            'obr', 'uk', 'watchdog', 'productivity', 'forecast', 'budget', 'deficit', 'responsibility',
            'office', 'downgraded', 'growth', 'economy', 'expects', 'revision', 'implications',
            'public', 'finances', 'expansion', 'revenues', 'warned', 'anticipated', 'pressure',
            'government', 'spending', 'plans', 'downgrade', 'reflects', 'ongoing', 'challenges',
            'brexit', 'disruptions', 'skills', 'shortages', 'weak', 'business', 'investment',
            'fbi', 'investigating', 'discord', 'chats', 'suspected', 'assassin', 'charlie', 'kirk',
            'significantly', 'connection', 'probe', 'expanded', 'estimates', 'agents', 'examining',
            'communications', 'servers', 'investigation', 'authorities', 'discovered', 'threats',
            'private', 'rooms', 'enforcement', 'officials', 'monitoring', 'discussions', 'identified',
            'numerous', 'individuals', 'involved', 'planning', 'discussing', 'potential', 'violence',
            'stone', 'skimming', 'contest', 'scotland', 'infiltrated', 'cheaters', 'championships',
            'tournament', 'picturesque', 'town', 'pitlochry', 'attracts', 'competitors', 'attempt',
            'skip', 'stones', 'water', 'maximum', 'distance', 'marred', 'allegations', 'violations',
            'winner', 'admitted', 'noticing', 'suspiciously', 'perfect', 'champion', 'stated',
            'considering', 'stricter', 'regulations', 'future', 'competitions'
        ]
        
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if word in text_lower)
        
        # Если больше 1 английского слова - считаем, что есть английский текст
        return english_count > 1
    
    def _clean_formatting(self, text: str) -> str:
        """Очищает текст от лишнего форматирования и улучшает читаемость"""
        if not text:
            return text
        
        # Удаляем ** форматирование
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # Удаляем другие markdown форматирования
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # *курсив*
        text = re.sub(r'_(.*?)_', r'\1', text)   # _подчеркивание_
        text = re.sub(r'`(.*?)`', r'\1', text)   # `код`
        
        # Удаляем упоминания стран в начале
        text = re.sub(r'^(Великобритания|США|Шотландия|Новость из \w+):\s*', '', text, flags=re.IGNORECASE)
        
        # Улучшаем форматирование абзацев
        # Заменяем множественные переносы строк на двойные
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Убираем лишние пробелы, но сохраняем структуру абзацев
        text = re.sub(r'[ \t]+', ' ', text)  # Множественные пробелы в один
        text = re.sub(r'\n ', '\n', text)    # Пробелы в начале строк
        
        # Если текст слишком длинный и нет абзацев, попробуем разделить
        if len(text) > 200 and '\n\n' not in text:
            # Ищем точки, за которыми идет заглавная буква
            sentences = re.split(r'\.\s+([А-ЯЁ])', text)
            if len(sentences) > 2:
                # Собираем предложения в абзацы
                result = sentences[0] + '.'
                for i in range(1, len(sentences), 2):
                    if i + 1 < len(sentences):
                        result += '\n\n' + sentences[i] + sentences[i + 1] + '.'
                text = result
        
        return text.strip()
    
    def is_enabled(self) -> bool:
        """Check if AI summarization is enabled and configured"""
        return self.enabled and self.client is not None


async def test_summarizer():
    """Test the AI summarizer"""
    # Load config from file
    import json
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            full_config = json.load(f)
        config = full_config.get("ai_summarization", {})
    except Exception:
        config = {
            "enabled": True,
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "max_summary_length": 200,
            "api_key": os.getenv("GROQ_API_KEY")
        }
    
    summarizer = AISummarizer(config)
    
    if not summarizer.is_enabled():
        print("❌ AI summarizer is not enabled or configured")
        print("💡 Get free API key at: https://console.groq.com/")
        return
    
    # Test with sample news
    title = "Pro-Palestine protesters halt the Vuelta a España final stage in Madrid"
    content = "Pro-Palestinian protesters disrupted the final stage of the Vuelta a España on Sunday, forcing cyclists to stop with around 50 kilometres remaining on the Madrid course."
    link = "http://www.euronews.com/video/2025/09/15/pro-palestine-protesters-halt-the-vuelta-a-espana-final-stage-in-madrid"
    
    summary = await summarizer.summarize(title, content, link)
    
    if summary:
        print(f"✅ AI Summary: {summary}")
    else:
        print("❌ Failed to create summary")


if __name__ == "__main__":
    # Test the summarizer
    asyncio.run(test_summarizer())