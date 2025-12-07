
import json
import os

CONFIG_PATH = "config.json"
ADMIN_ID = 560315335

def add_admin_id():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Файл {CONFIG_PATH} не найден!")
        return

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Убедимся, что секция admin существует
        if "admin" not in config:
            config["admin"] = {}
        
        # Убедимся, что список allowed_user_ids существует
        if "allowed_user_ids" not in config["admin"]:
            config["admin"]["allowed_user_ids"] = []
        
        # Добавляем ID, если его там нет
        if ADMIN_ID not in config["admin"]["allowed_user_ids"]:
            config["admin"]["allowed_user_ids"].append(ADMIN_ID)
            
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ ID {ADMIN_ID} успешно добавлен в админы!")
        else:
            print(f"ℹ️ ID {ADMIN_ID} уже есть в списке админов.")
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении конфига: {e}")

if __name__ == "__main__":
    add_admin_id()
