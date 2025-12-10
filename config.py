import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sync_bot.db")

TG_TOKEN = os.getenv("BOT_TOKEN")  # ← будет из bothost
VK_TOKEN = os.getenv("VK_TOKEN", "")  # ← будет из bothost

# ВСЁ ОСТАЛЬНОЕ БЕЗ ИЗМЕНЕНИЙ ↓
VK_GROUP_ID = 234356723
ADMINS = ["nextxb", "yyangpython"]

COOLNESS_WEIGHTS = {
    "обычная": 70,
    "жоская": 29,
    "ИМБОВАЯ": 1
}

CARD_COOLDOWN = 5

# Все картинки будут искаться в папке проекта
CARDS = [
    {"id": 1, "name": "весёлый Ислам", "coolness": "обычная", "UFCoins": 50, "image_path": "веселый ислам.jpg"},
    # ... все остальные карточки без изменений
]

# Преобразуем относительные пути в абсолютные
for card in CARDS:
    card["image_path"] = os.path.join(BASE_DIR, card["image_path"])

CARDS_DICT = {card["id"]: card for card in CARDS}
COOLNESS_CARDS = {
    "обычная": [c for c in CARDS if c["coolness"] == "обычная"],
    "жоская": [c for c in CARDS if c["coolness"] == "жоская"],
    "ИМБОВАЯ": [c for c in CARDS if c["coolness"] == "ИМБОВАЯ"]
}
