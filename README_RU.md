# 📰 FAP News Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg?logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![AI](https://img.shields.io/badge/AI-Groq%20LLaMA-purple.svg)

**Интеллектуальный Telegram-агрегатор новостей с AI-суммаризацией**

[🇺🇸 English](README.md) | [📖 Быстрый старт](QUICKSTART.md) | [🚀 Деплой](DEPLOYMENT.md)

</div>

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 📡 **Мультиисточники** | RSS-фиды, Google News, Telegram-каналы |
| 🤖 **AI-суммаризация** | Умные саммари на базе Groq LLaMA |
| 🚨 **Срочные новости** | Мгновенная публикация breaking news |
| 🧹 **Умная дедупликация** | Фильтрация по семантическому сходству |
| ⚡ **Приоритетная публикация** | Настраиваемые приоритеты источников |
| 📊 **Админ-панель** | Telegram-бот для управления |
| 💾 **Интеллектуальный кэш** | Экономия API-запросов |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     FAP News Bot                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │   RSS   │  │ Google  │  │Telegram │  │  Альтернативные │ │
│  │  Фиды   │  │  News   │  │ Каналы  │  │   источники     │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
│       │            │            │                │          │
│       └────────────┴────────────┴────────────────┘          │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │   Парсер    │                          │
│                    │  и Фильтр   │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │    Умная    │                          │
│                    │Дедупликация │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│            ┌──────────────┴──────────────┐                  │
│            │                             │                  │
│     ┌──────▼──────┐              ┌───────▼───────┐          │
│     │  Проверка   │              │   Анализ      │          │
│     │  срочности  │              │   важности    │          │
│     └──────┬──────┘              └───────┬───────┘          │
│            │                             │                  │
│     ┌──────▼──────┐              ┌───────▼───────┐          │
│     │    Groq     │◄────────────►│   AI Кэш      │          │
│     │     API     │              │   (SQLite)    │          │
│     └──────┬──────┘              └───────────────┘          │
│            │                                                │
│     ┌──────▼──────┐                                         │
│     │  Telegram   │                                         │
│     │    канал    │                                         │
│     └─────────────┘                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Токен Telegram-бота (от [@BotFather](https://t.me/BotFather))
- Groq API ключ (бесплатно на [groq.com](https://console.groq.com))

### Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/fap-news.git
cd fap-news

# Создайте виртуальное окружение
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/Mac

# Установите зависимости
pip install -r requirements.txt

# Настройте конфигурацию
cp config.example.json config.json
# Отредактируйте config.json, добавив ваши токены
```

### Настройка

Отредактируйте `config.json`:

```json
{
  "telegram": {
    "token": "ВАШ_ТОКЕН_БОТА",
    "channel_id": "@ваш_канал"
  },
  "ai_summarization": {
    "enabled": true,
    "api_key": "ВАШ_GROQ_API_KEY"
  },
  "admin": {
    "allowed_user_ids": [123456789]
  }
}
```

### Запуск

```bash
# Запуск основного бота
python bot.py

# Или запуск обоих ботов (основной + админ)
python run_all.py
```

---

## 📦 Структура проекта

```
fap-news/
├── bot.py                    # Основной бот сбора новостей
├── admin_bot.py              # Админ-панель
├── parser.py                 # Парсинг RSS/HTML
├── poster.py                 # Публикация в Telegram
├── db.py                     # Работа с базой данных
├── config.py                 # Управление конфигурацией
├── ai_summarizer.py          # AI-суммаризация (Groq)
├── ai_cache.py               # Кэширование AI-ответов
├── smart_deduplicator.py     # Семантическая дедупликация
├── news_importance_analyzer.py # Оценка важности новостей
├── google_news.py            # Сборщик Google News
├── telegram_channels.py      # Парсер Telegram-каналов
├── alternative_sources.py    # Дополнительные источники
├── config.example.json       # Шаблон конфигурации
├── requirements.txt          # Python-зависимости
├── Dockerfile                # Docker-образ
└── docker-compose.yml        # Docker Compose
```

---

## 📰 Поддерживаемые источники

### RSS-фиды (16+ настроенных)
- BBC, Reuters, Fox News, CNN, NYT
- Washington Post, The Guardian, Financial Times
- RT, ТАСС, РИА Новости
- Al Jazeera, Deutsche Welle, Euronews
- И многие другие...

### Google News
- Тематические ленты (Мир, Политика, Бизнес)
- Пользовательские поисковые запросы

### Telegram-каналы
- BBC Russian, Mash, РИА, ТАСС
- Легко добавить новые каналы

---

## ⚙️ Параметры конфигурации

| Секция | Параметр | Описание |
|--------|----------|----------|
| `telegram` | `token` | Токен бота |
| `telegram` | `channel_id` | ID целевого канала |
| `ai_summarization` | `enabled` | Вкл/выкл AI |
| `ai_summarization` | `api_key` | Ключ Groq API |
| `posting` | `min_delay_minutes` | Мин. интервал между постами |
| `posting` | `max_queue_size` | Размер очереди |
| `source_priority` | `high_priority` | Источники высокого приоритета |
| `deduplication` | `similarity_threshold` | Порог дедупликации (0-1) |

Полный список в [config.example.json](config.example.json).

---

## 🤖 Команды админ-бота

| Команда | Описание |
|---------|----------|
| `/start` | Открыть админ-панель |
| `/admin` | То же, что /start |
| **Кнопки** | |
| 📰 Источники | Управление источниками |
| ⚙️ Фильтры | Настройки фильтрации |
| 📊 Статистика | Просмотр статистики |
| 🔍 Статус | Проверка здоровья бота |

---

## 🐳 Docker-деплой

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

---

## 📊 Производительность

- **Сбор**: ~300-400 новостей за цикл
- **AI-кэширование**: Снижает API-запросы на ~70%
- **Дедупликация**: Фильтрует ~30-50% дубликатов
- **Публикация**: Интервал 1-4 минуты

---

## 🛠️ Разработка

```bash
# Диагностика
python diagnose.py

# Тест отправки
python test_send.py

# Принудительная публикация
python force_post.py
```

---

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE).

---

## 🤝 Вклад в проект

Ваш вклад приветствуется! См. [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📞 Поддержка

- 📖 [FAQ](FAQ.md)
- 🐛 [Issues](https://github.com/yourusername/fap-news/issues)

---

<div align="center">

**Сделано с ❤️ для агрегации новостей**

⭐ Поставьте звезду, если проект полезен!

</div>
