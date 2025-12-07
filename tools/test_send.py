#!/usr/bin/env python3
"""Тестовая отправка сообщения в канал"""

import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_send():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    telegram_cfg = config.get("telegram", {})
    token = telegram_cfg.get("token") or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = telegram_cfg.get("channel_id")
    
    print(f"Token: {token[:15]}...")
    print(f"Channel: {channel_id}")
    
    if not token or not channel_id:
        print("❌ Нет токена или channel_id!")
        return
    
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        
        # Проверяем бота
        me = await bot.get_me()
        print(f"✅ Бот: @{me.username}")
        
        # Проверяем канал
        try:
            chat = await bot.get_chat(channel_id)
            print(f"✅ Канал: {chat.title}")
        except Exception as e:
            print(f"❌ Ошибка доступа к каналу: {e}")
            await bot.session.close()
            return
        
        # Проверяем права
        try:
            member = await bot.get_chat_member(channel_id, me.id)
            print(f"✅ Статус бота: {member.status}")
            if member.status not in ['administrator', 'creator']:
                print("❌ Бот НЕ является администратором канала!")
                print("   Пожалуйста, добавьте бота как администратора с правом публикации")
                await bot.session.close()
                return
        except Exception as e:
            print(f"⚠️ Не удалось проверить права: {e}")
        
        # Пробуем отправить тестовое сообщение
        print("\n📤 Отправляю тестовое сообщение...")
        try:
            msg = await bot.send_message(
                chat_id=channel_id,
                text="🧪 <b>Тестовое сообщение FAP News</b>\n\nЕсли вы видите это сообщение, бот работает правильно!"
            )
            print(f"✅ Сообщение отправлено! ID: {msg.message_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            print("\nВозможные причины:")
            print("  • Бот не добавлен в канал")
            print("  • У бота нет прав на публикацию")
            print("  • Неправильный channel_id")
        
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_send())
