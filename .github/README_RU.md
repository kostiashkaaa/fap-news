# 🗞️ FAP News — Умный новостной агрегатор для Telegram

[English](../README.md) | **Русский**

Интеллектуальный Telegram-бот, который автоматически собирает, переводит, суммирует и публикует новости из множества международных источников, используя AI-анализ.

## ✨ Возможности

### 🤖 **AI-интеллект**
- **Умная суммаризация**: Использует Groq AI (LLaMA 3.1) для создания кратких информативных сводок
- **Определение срочности**: Автоматически выявляет важные новости для немедленной публикации
- **Анализ свежести**: Фильтрует старые новости
- **Оценка важности**: Адаптирует длину сводки в зависимости от значимости новости
- **Умная дедупликация**: Семантический анализ для избежания дубликатов

### 📰 **Многоисточниковая агрегация**
- Поддержка RSS из 15+ крупных новостных источников (BBC, CNN, Reuters, NYT, Guardian и др.)
- Альтернативные источники: Reddit, Hacker News, GitHub Trending
- Поддержка русских и международных новостей
- Настраиваемые приоритеты источников

### 🎯 **Продвинутая фильтрация**
- Фильтрация по ключевым словам (включение/исключение)
- Фильтрация по возрасту новости
- Умный контент-анализ для избежания нерелевантных новостей

### 🚀 **Автоматизация**
- Запланированный сбор новостей (настраиваемые интервалы)
- Публикация через очередь с умными задержками
- Автоматический перевод на русский
- Встроенное кэширование для экономии API-запросов

### 🛠️ **Админ-панель**
- Управление через Telegram
- Динамическое управление источниками
- Статистика в реальном времени
- Простая конфигурация

## 📋 Требования

- Python 3.11 или выше
- Telegram Bot Token ([получить у @BotFather](https://t.me/botfather))
- Groq API ключ (опционально, [получить бесплатно](https://console.groq.com/))

## 🚀 Быстрый старт

См. [QUICKSTART.md](../QUICKSTART.md) для установки за 5 минут!

### Краткая инструкция:

```bash
# Клонировать репозиторий
git clone https://github.com/yourusername/fap-news.git
cd fap-news

# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Установить зависимости
pip install -r requirements.txt

# Настроить бота
python setup.py

# Запустить бота
python bot.py
```

## 📖 Полная документация

- 📚 [README на английском](../README.md) - Полная документация
- ⚡ [QUICKSTART](../QUICKSTART.md) - Быстрый старт
- ❓ [FAQ](../FAQ.md) - Частые вопросы
- 🚀 [DEPLOYMENT](../DEPLOYMENT.md) - Гайд по развёртыванию
- 🤝 [CONTRIBUTING](../CONTRIBUTING.md) - Как внести вклад
- 🔒 [SECURITY](../SECURITY.md) - Безопасность

## 🎯 Основные команды

```bash
# Запустить главный бот
python bot.py

# Запустить админ-панель
python admin_bot.py

# Запустить оба бота
python run_all.py
```

## ⚙️ Конфигурация

### Минимальная конфигурация (только RSS, без AI):

```json
{
  "telegram": {
    "token": "ВАШ_ТОКЕН",
    "channel_id": "@ваш_канал"
  },
  "ai_summarization": {
    "enabled": false
  }
}
```

### Полная конфигурация (с AI):

```json
{
  "telegram": {
    "token": "ВАШ_ТОКЕН",
    "channel_id": "@ваш_канал"
  },
  "ai_summarization": {
    "enabled": true,
    "api_key": "ВАШ_GROQ_КЛЮЧ"
  },
  "filters": {
    "include_keywords": ["Украина", "Россия", "США"],
    "max_age_hours": 24
  }
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

## 🤝 Вклад в проект

Мы приветствуем вклад в проект! См. [CONTRIBUTING.md](../CONTRIBUTING.md) для деталей.

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](../LICENSE) для деталей.

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot фреймворк
- [Groq](https://groq.com/) - Быстрый AI inference
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS парсинг
- Всем open source контрибьюторам

## 📧 Контакты

- Создайте [Issue](https://github.com/yourusername/fap-news/issues) для багов или фич
- [Discussions](https://github.com/yourusername/fap-news/discussions) для вопросов

## ⭐ Поддержка

Если проект вам полезен, пожалуйста:
- Поставьте ⭐ на GitHub
- Поделитесь с другими
- Внесите улучшения

---

**Создано с ❤️ для open source сообщества**
