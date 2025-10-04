# 🗞️ FAP News — AI-Powered Telegram Новостной Агрегатор

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**[English](README.md) | Русский**

Интеллектуальный Telegram-бот, который автоматически собирает, переводит, суммирует и публикует новости из множества международных источников, используя AI-анализ.

## ✨ Возможности

### 🤖 **AI-интеллект**
- **Умная суммаризация**: Использует Groq AI (LLaMA 3.1) для создания кратких информативных сводок
- **Определение срочности**: Автоматически выявляет breaking news для немедленной публикации
- **Анализ свежести**: Фильтрует старые новости, публикует только актуальные
- **Оценка важности**: Адаптирует длину сводки в зависимости от значимости новости
- **Умная дедупликация**: Семантический анализ для избежания дубликатов

### 📰 **Многоисточниковая Агрегация**
- Поддержка RSS из 15+ крупных новостных источников (BBC, CNN, Reuters, NYT, Guardian и др.)
- Альтернативные источники: Reddit, Hacker News, GitHub Trending
- Поддержка русских и международных новостей
- Настраиваемые приоритеты источников

### 🎯 **Продвинутая Фильтрация**
- Фильтрация по ключевым словам (включение/исключение)
- Фильтрация по возрасту новости (настраиваемое временное окно)
- Умный контент-анализ для избежания нерелевантных новостей

### 🚀 **Автоматизация**
- Запланированный сбор новостей (настраиваемые интервалы)
- Публикация через очередь с умными задержками
- Автоматический перевод на русский язык
- Встроенное кэширование для экономии API-запросов

### 🛠️ **Админ-Панель**
- Управление через Telegram
- Динамическое управление источниками
- Статистика в реальном времени
- Простая конфигурация

## 📋 Требования

- Python 3.11 или выше
- Telegram Bot Token ([получить у @BotFather](https://t.me/botfather))
- Groq API ключ (опционально, [получить бесплатно](https://console.groq.com/))

## 🚀 Быстрый Старт

### 1. Клонировать Репозиторий

```bash
git clone https://github.com/kostiashkaaa/fap-news.git
cd fap-news
```

### 2. Создать Виртуальное Окружение

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Установить Зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить Бота

#### Вариант А: Через Переменные Окружения

Создайте файл `.env`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
ADMIN_USER_ID=ваш_telegram_user_id
GROQ_API_KEY=ваш_groq_api_ключ  # Опционально
```

#### Вариант Б: Через config.json

Скопируйте пример конфигурации:

```bash
cp config.example.json config.json
```

Отредактируйте `config.json` и добавьте свои данные:

```json
{
  "telegram": {
    "token": "ВАШ_ТОКЕН_БОТА",
    "channel_id": "@ваш_канал"
  },
  "ai_summarization": {
    "enabled": true,
    "api_key": "ВАШ_GROQ_КЛЮЧ"
  },
  "admin": {
    "allowed_user_ids": [ВАШ_USER_ID]
  }
}
```

**Чтобы узнать свой Telegram User ID:**
- Напишите [@userinfobot](https://t.me/userinfobot) в Telegram

### 5. Запустить Бота

```bash
# Главный бот (сбор и публикация новостей)
python bot.py

# Админ-панель (в отдельном терминале)
python admin_bot.py
```

## 📖 Подробная Документация

### Настройки Конфигурации

#### Telegram
```json
"telegram": {
  "token": "ВАШ_ТОКЕН_БОТА",
  "channel_id": "@ваш_канал_или_chat_id"
}
```

#### Источники Новостей
Вы можете добавлять RSS-каналы или HTML источники:

```json
"sources": [
  {
    "name": "Название Источника",
    "tag": "#тег_источника",
    "rss": "https://example.com/rss",
    "priority": 1  // 1=высший, 3=низший приоритет
  }
]
```

#### Фильтры
```json
"filters": {
  "include_keywords": ["Украина", "Россия", "США"],  // Только эти темы
  "exclude_keywords": ["спорт", "знаменитости"],     // Пропустить эти
  "max_age_hours": 24,                                // Игнорировать старые новости
  "max_age_minutes": 120                              // Альтернативное ограничение по времени
}
```

#### AI Суммаризация
```json
"ai_summarization": {
  "enabled": true,
  "provider": "groq",
  "api_key": "ВАШ_API_КЛЮЧ",
  "model": "llama-3.1-8b-instant",
  "max_summary_length": 500,
  "cache_enabled": true  // Экономия API запросов
}
```

#### Расписание Публикаций
```json
"scheduler": {
  "interval_minutes": 10  // Проверка новостей каждые 10 минут
},
"posting": {
  "min_delay_minutes": 1,  // Минимальное время между постами
  "max_delay_minutes": 4   // Максимальное время между постами
}
```

### Команды Администратора

Запустите админ-бота и отправьте `/admin` или `/start` для доступа:

- 📰 **Управление Источниками**: Добавление/удаление новостных источников
- ⚙️ **Настройки Фильтров**: Просмотр текущих фильтров
- 📊 **Статистика**: Просмотр статистики публикаций

### Структура Проекта

```
fap-news/
├── bot.py                        # Главный бот (сбор и публикация)
├── admin_bot.py                  # Админ-панель
├── parser.py                     # Парсинг RSS/HTML
├── poster.py                     # Форматирование и публикация в Telegram
├── ai_summarizer.py              # AI суммаризация
├── smart_deduplicator.py         # Обнаружение дубликатов
├── news_importance_analyzer.py   # Оценка важности новостей
├── alternative_sources.py        # Reddit, HN, GitHub интеграция
├── ai_cache.py                   # Кэширование AI ответов
├── db.py                         # SQLite база данных
├── config.json                   # Основная конфигурация
├── requirements.txt              # Python зависимости
└── README.md                     # Документация
```

## 🔧 Продвинутые Функции

### Умная Дедупликация

Бот использует семантический анализ для обнаружения дубликатов:

```json
"deduplication": {
  "enabled": true,
  "similarity_threshold": 0.7,  // 0-1, выше = строже
  "title_weight": 0.6,           // Важность схожести заголовков
  "content_weight": 0.4          // Важность схожести содержания
}
```

### Альтернативные Источники Новостей

Включите дополнительные источники помимо RSS:

```json
"alternative_sources": {
  "reddit": {
    "enabled": true,
    "subreddits": ["worldnews", "news", "politics"]
  },
  "newsapi": {
    "enabled": false,
    "api_key": "ВАШ_NEWSAPI_КЛЮЧ"
  }
}
```

### Кэширование AI

Снижает затраты на API запросы:

```json
"ai_summarization": {
  "cache_enabled": true,
  "cache_ttl_hours": 24  // Время жизни кэша
}
```

## 🐳 Docker

```bash
# Создать .env файл
cp env.example.txt .env
# Отредактировать .env

# Создать config.json
cp config.example.json config.json
# Отредактировать config.json

# Запустить через Docker Compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## 🤝 Вклад в Проект

Мы приветствуем вклад в проект! См. [CONTRIBUTING.md](CONTRIBUTING.md) для деталей по:
- Вкладу в код
- Улучшению документации
- Отчётам об ошибках
- Предложениям функций
- Переводам

## 🐛 Устранение Неполадок

### Бот не публикует сообщения
- Проверьте токен бота в `config.json` или `.env`
- Убедитесь что бот является администратором канала
- Проверьте логи в консоли на наличие ошибок

### AI суммаризация не работает
- Проверьте правильность Groq API ключа
- Проверьте [статус Groq](https://status.groq.com/)
- Проверьте лимиты использования в конфигурации

### Отсутствуют зависимости
```bash
pip install -r requirements.txt --upgrade
```

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot фреймворк
- [Groq](https://groq.com/) - Быстрый AI inference
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS парсинг
- Всем open source контрибьюторам

## 📧 Контакты

- Создайте [Issue](https://github.com/kostiashkaaa/fap-news/issues) для багов или новых функций
- [Discussions](https://github.com/kostiashkaaa/fap-news/discussions) для вопросов

## ⭐ Поддержка

Если проект вам полезен, пожалуйста:
- Поставьте ⭐ на GitHub
- Поделитесь с друзьями
- Внесите свой вклад в улучшения

---

**Создано с ❤️ для open source сообщества**

## 📚 Дополнительная Документация

- ⚡ [Быстрый Старт](QUICKSTART.md) - Запуск за 5 минут
- ❓ [FAQ](FAQ.md) - Частые вопросы и ответы
- 🚀 [Развёртывание](DEPLOYMENT.md) - Гайд по развёртыванию на VPS/Cloud
- 🤝 [Вклад в Проект](CONTRIBUTING.md) - Как помочь проекту
- 🔒 [Безопасность](SECURITY.md) - Рекомендации по безопасности
