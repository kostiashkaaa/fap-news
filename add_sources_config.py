#!/usr/bin/env python3
"""
Добавляет конфигурации для Google News и Telegram каналов в config.json
"""

import json
import shutil
from pathlib import Path

CONFIG_PATH = Path("config.json")

def add_new_sources_config():
    if not CONFIG_PATH.exists():
        print("❌ config.json не найден!")
        return
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return
    
    modified = False
    
    # Добавляем Google News
    if "google_news" not in config:
        print("➕ Добавляю секцию google_news...")
        config["google_news"] = {
            "enabled": True,
            "language": "ru",
            "country": "RU",
            "topics": ["world", "nation", "business"],
            "search_queries": [
                "Россия Украина",
                "Путин Putin",
                "Зеленский Zelensky",
                "NATO НАТО",
                "санкции sanctions",
                "война war"
            ],
            "max_items_per_source": 15
        }
        modified = True
    
    # Добавляем Telegram каналы
    if "telegram_channels" not in config:
        print("➕ Добавляю секцию telegram_channels...")
        config["telegram_channels"] = {
            "enabled": True,
            "max_posts_per_channel": 10,
            "max_age_hours": 24,
            "channels": [
                {"username": "bbcrussian", "name": "BBC Russian", "tag": "#bbcru", "priority": 3},
                {"username": "breakingmash", "name": "Mash", "tag": "#mash", "priority": 3},
                {"username": "rian_ru", "name": "РИА Новости", "tag": "#ria", "priority": 2},
                {"username": "taborufr", "name": "ТАСС", "tag": "#tass", "priority": 2},
                {"username": "rt_russian", "name": "RT на русском", "tag": "#rt", "priority": 1}
            ]
        }
        modified = True
    
    if modified:
        shutil.copy(CONFIG_PATH, "config.json.bak2")
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Config.json обновлен!")
        print("\n📌 Добавлены новые источники:")
        print("   • Google News (поиск по темам и ключевым словам)")
        print("   • Telegram каналы (BBC, Mash, РИА, ТАСС, RT)")
    else:
        print("✅ Config.json уже содержит все необходимые секции")

if __name__ == "__main__":
    add_new_sources_config()
