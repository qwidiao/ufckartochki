# main.py
from database import Database
from telegram_bot import TelegramBot
import config

def main():
    print("🚀 Starting bot...")
    
    db = Database(config.DB_PATH)
    tg_bot = TelegramBot(config.TG_TOKEN, db)
    
    print("🔧 Starting Telegram bot with executor...")
    tg_bot.run()  # Использует executor.start_polling внутри

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"💥 Critical error: {e}")
