
import json
import shutil
from pathlib import Path

def update_config():
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json не найден, создаю из примера...")
        shutil.copy("config.example.json", "config.json")
        return

    # Загружаем текущий конфиг
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return

    # Определяем новые поля
    source_priority_default = {
        "high_priority": [
            "Fox News", "New York Times World", "Financial Times World",
            "Washington Post World", "The Guardian World", "BBC News Russian",
            "Euronews", "Deutsche Welle", "France 24", "Al Jazeera"
        ],
        "medium_priority": [
            "South China Morning Post", "Japan Times", "Reuters - World News", "CNN Breaking News"
        ],
        "low_priority": [
            "RT Russian", "TASS", "RIA Novosti", "Lenta.ru"
        ],
        "max_sources_per_cycle": 3
    }

    modified = False

    # Добавляем source_priority
    if "source_priority" not in config:
        print("➕ Добавляю секцию source_priority...")
        config["source_priority"] = source_priority_default
        modified = True

    # Добавляем поля в posting
    if "posting" not in config:
        config["posting"] = {}
    
    if "max_queue_size" not in config["posting"]:
        print("➕ Добавляю posting.max_queue_size...")
        config["posting"]["max_queue_size"] = 50
        modified = True
        
    if "max_sources_per_cycle" not in config["posting"]:
        print("➕ Добавляю posting.max_sources_per_cycle...")
        config["posting"]["max_sources_per_cycle"] = 3
        modified = True

    # Сохраняем, если были изменения
    if modified:
        shutil.copy("config.json", "config.json.bak") # Бэкап
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Config.json успешно обновлен (бэкап сохранен в config.json.bak)")
    else:
        print("✅ Config.json уже содержит все необходимые поля")

if __name__ == "__main__":
    update_config()
