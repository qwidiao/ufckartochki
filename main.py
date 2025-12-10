# main.py
import asyncio
from database import Database
from telegram_bot import TelegramBot
import config

async def main():
    print("🚀 Starting UFCards Bot...")
    print(f"📁 Database: {config.DB_PATH}")
    
    # Инициализация
    db = Database(config.DB_PATH)
    bot = TelegramBot(config.TG_TOKEN, db)
    
    # Запуск
    print("✅ Bot initialized, starting polling...")
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"💥 Error: {e}")
        raise
