import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sync_bot.db")

TG_TOKEN = os.getenv("BOT_TOKEN")
VK_TOKEN = os.getenv("VK_TOKEN", "")

# ВСЁ ОСТАЛЬНОЕ БЕЗ ИЗМЕНЕНИЙ ↓
VK_GROUP_ID = 234356723
ADMINS = ["nextxb", "yyangpython"]

COOLNESS_WEIGHTS = {
    "обычная": 70,
    "жоская": 29,
    "ИМБОВАЯ": 1
}

CARD_COOLDOWN = 10800

# Все картинки будут искаться в папке проекта
CARDS = [
    {"id": 1, "name": "весёлый Ислам", "coolness": "обычная", "UFCoins": 50, "image_path": "веселый ислам.jpg"},
    {"id": 2, "name": "Джонс с поясом", "coolness": "обычная", "UFCoins": 50, "image_path": "джонс с поясом.jpg"},
    {"id": 3, "name": "качок Джонс", "coolness": "обычная", "UFCoins": 50, "image_path": "качок джонс.jpg"},
    {"id": 4, "name": "Конор в кожанке", "coolness": "обычная", "UFCoins": 50, "image_path": "конор в дубленке.jpg"},
    {"id": 5, "name": "удивленный Ислам", "coolness": "обычная", "UFCoins": 50, "image_path": "удивленный ислам.jpg"},
    {"id": 6, "name": "Хабиб в метрошке", "coolness": "обычная", "UFCoins": 50, "image_path": "хабиб в метрошке.jpg"},
    {"id": 7, "name": "Хабиб в парике", "coolness": "обычная", "UFCoins": 50, "image_path": "хабиб в шапке.jpg"},
    {"id": 8, "name": "Чарльз где-то", "coolness": "обычная", "UFCoins": 50, "image_path": "чарльз где то.jpg"},
    {"id": 9, "name": "Чарльз с пёсиком", "coolness": "обычная", "UFCoins": 50, "image_path": "чарльз с песиком.jpg"},
    {"id": 10, "name": "шеф Конор", "coolness": "обычная", "UFCoins": 50, "image_path": "шеф Конор.jpg"},
    {"id": 11, "name": "Илия на стадике", "coolness": "обычная", "UFCoins": 50, "image_path": "илия на стадике.jpg"},
    {"id": 12, "name": "бизнесмен Арман", "coolness": "обычная", "UFCoins": 50, "image_path": "бизнесмен арман.jpg"},
    {"id": 13, "name": "кричащий Волк", "coolness": "обычная", "UFCoins": 50, "image_path": "кричащий волк.jpg"},
    {"id": 14, "name": "куряга Шон", "coolness": "обычная", "UFCoins": 50, "image_path": "куряга шон.jpg"},
    {"id": 15, "name": "Пётр на трене", "coolness": "обычная", "UFCoins": 50, "image_path": "Пётр на трене.jpg"},
    {"id": 16, "name": "Шара в капюшоне", "coolness": "обычная", "UFCoins": 50, "image_path": "шара в капюшоне.jpg"},
    {"id": 17, "name": "безумный Пэдди", "coolness": "жоская", "UFCoins": 200, "image_path": "безумный пэдди.jpg"},
    {"id": 18, "name": "богатый Конор", "coolness": "жоская", "UFCoins": 200, "image_path": "богатый конор.jpg"},
    {"id": 19, "name": "боец Хасбик", "coolness": "жоская", "UFCoins": 200, "image_path": "боец хасбик.jpg"},
    {"id": 20, "name": "добряк Джастин", "coolness": "жоская", "UFCoins": 200, "image_path": "добряк джастин.jpg"},
    {"id": 21, "name": "Конор с тигром", "coolness": "жоская", "UFCoins": 200, "image_path": "конор с тигром.jpg"},
    {"id": 22, "name": "мимимишный Хабиб", "coolness": "жоская", "UFCoins": 200, "image_path": "мимимишный хабиб.jpg"},
    {"id": 23, "name": "Хабиб на фоне природы", "coolness": "жоская", "UFCoins": 200, "image_path": "хабиб на фоне природы.jpg"},
    {"id": 24, "name": "Хамзат с пушкой", "coolness": "жоская", "UFCoins": 200, "image_path": "хамзат с пушкой.jpg"},
    {"id": 25, "name": "Конор в Самаре", "coolness": "ИМБОВАЯ", "UFCoins": 1000, "image_path": "конор в самаре.jpg"}
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
