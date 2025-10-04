#!/usr/bin/env python3
"""
Простой бот для получения вашего Telegram ID
Запустите этот бот, отправьте ему любое сообщение, и он покажет ваш ID
"""

import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
import asyncio

# Загружаем токен из config.json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

TOKEN = config.get('telegram', {}).get('token')
if not TOKEN:
    print("❌ Токен не найден в config.json")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def get_user_id(message: Message):
    """Показывает ID пользователя"""
    user_id = message.from_user.id
    username = message.from_user.username or "нет username"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    response = (
        f"🆔 <b>Ваши данные:</b>\n\n"
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<b>Username:</b> @{username}\n"
        f"<b>Имя:</b> {first_name} {last_name}\n\n"
        f"💡 Добавьте ваш ID <code>{user_id}</code> в config.json в секцию:\n"
        f'<code>"admin": {{"allowed_user_ids": [{user_id}]}}</code>\n\n'
        f"После этого у вас будет доступ к админ панели!"
    )
    
    await message.answer(response, parse_mode="HTML")

async def main():
    print("🤖 Бот для получения ID запущен!")
    print("📝 Отправьте боту любое сообщение, чтобы узнать свой ID")
    print("⏹️  Нажмите Ctrl+C для остановки")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен!")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

