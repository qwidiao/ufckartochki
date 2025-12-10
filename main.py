import asyncio
import time
from database import Database
from telegram_bot import TelegramBot
import config

async def run_telegram_bot():
    try:
        print("🤖 Telegram bot initializing...")
        db = Database(config.DB_PATH)
        tg_bot = TelegramBot(config.TG_TOKEN, db)
        print("✅ Telegram bot successfully initialized!")
        await tg_bot.run()
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")

async def main():
    print("🚀 Starting bot...")
    
    # Запускаем только Telegram бота
    print("🔧 Starting Telegram bot...")
    await run_telegram_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"💥 Critical error: {e}")