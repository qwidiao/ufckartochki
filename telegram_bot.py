# telegram_bot.py
import asyncio
import random
import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters import Text, Command
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import config
from database import Database


class NicknameStates(StatesGroup):
    waiting_for_nickname = State()


class TelegramBot:
    def __init__(self, token: str, db: Database):
        self.bot = Bot(token=token, parse_mode='HTML')
        self.storage = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=self.storage)
        self.db = db
        self.user_cards_pages = {}
        
        self.known_text_commands = {
            "карточка", "карта", "карту", "карт", "боец", "карточку",
            "статистика", "стата", "стат", "статс", "статистику",
            "ник", "никнейм", "помощь", "хелп", "хэлп",
            "топ", "топы", "богачи", "топа", 
            "мои карты", "коллекция", "мой сбор", "бойцы"
        }

        self.register_handlers()

    def register_handlers(self):
        # Команды
        self.dp.register_message_handler(self.start_handler, commands=['start'])
        self.dp.register_message_handler(self.card_handler, commands=['card'])
        self.dp.register_message_handler(self.stats_handler, commands=['stats'])
        self.dp.register_message_handler(self.nick_handler, commands=['nick'])
        self.dp.register_message_handler(self.help_handler, commands=['help'])
        self.dp.register_message_handler(self.tops_handler, commands=['top'])
        self.dp.register_message_handler(self.mycards_handler, commands=['mycards'])
        self.dp.register_message_handler(self.promo_code_handler, commands=['code'])
        self.dp.register_message_handler(self.code_create_handler, commands=['codecreate'])
        self.dp.register_message_handler(self.link_handler, commands=['link'])
        
        # Текстовые команды
        self.dp.register_message_handler(
            self.card_handler, 
            lambda msg: msg.text and msg.text.lower() in ["карточка", "карта", "карту", "карт", "боец", "карточку"]
        )
        self.dp.register_message_handler(
            self.stats_handler,
            lambda msg: msg.text and msg.text.lower() in ["статистика", "стата", "стат", "статс", "статистику"]
        )
        self.dp.register_message_handler(
            self.nick_handler,
            lambda msg: msg.text and msg.text.lower() in ["ник", "никнейм"]
        )
        self.dp.register_message_handler(
            self.help_handler,
            lambda msg: msg.text and msg.text.lower() in ["помощь", "хелп", "хэлп"]
        )
        self.dp.register_message_handler(
            self.tops_handler,
            lambda msg: msg.text and msg.text.lower() in ["топ", "топы", "богачи", "топа"]
        )
        self.dp.register_message_handler(
            self.mycards_handler,
            lambda msg: msg.text and msg.text.lower() in ["мои карты", "коллекция", "мой сбор", "бойцы"]
        )
        
        # Обработчик ввода никнейма (state)
        self.dp.register_message_handler(self.process_nickname_input, state=NicknameStates.waiting_for_nickname)
        
        # Callback handlers
        self.dp.register_callback_query_handler(self.start_game_handler, lambda c: c.data == "start_game")
        self.dp.register_callback_query_handler(self.mycards_next_handler, lambda c: c.data == "mycards_next")
        self.dp.register_callback_query_handler(self.mycards_prev_handler, lambda c: c.data == "mycards_prev")
        self.dp.register_callback_query_handler(self.mycards_close_handler, lambda c: c.data == "mycards_close")
        
        # Обработчик неизвестных сообщений в ЛС
        self.dp.register_message_handler(self.text_handler, lambda msg: msg.chat.type == "private")

    async def link_handler(self, message: types.Message):
        if message.chat.type != "private":
            return await message.reply("<b>❌ команда /link доступна только в личных сообщениях с ботом</b>")
        else:
            return await message.reply('<b>🚀 в разработке</b>')

    async def text_handler(self, message: types.Message):
        text = (message.text or "").lower().strip()
        
        if text in self.known_text_commands:
            return
        
        await message.reply(
            "<b>❌ неизвестная команда</b>\n\n"
            "<i>посмотреть список команд можно с помощью /help</i>"
        )
    
    async def process_nickname_input(self, message: types.Message, state: FSMContext):
        nickname = message.text.strip()
        
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            await state.finish()
            return await message.reply("❌ <b>ошибка - пользователь не найден</b>")
        
        if len(nickname) < 3:
            return await message.reply("❌ <b>слишком короткий никнейм (минимум 3 символа)</b>\n\n✏️ <b>попробуйте еще раз:</b>")
        
        if len(nickname) > 20:
            return await message.reply("❌ <b>слишком длинный никнейм (максимум 20 символов)</b>\n\n✏️ <b>попробуйте еще раз:</b>")
        
        if not nickname.replace('_', '').isalnum():
            return await message.reply("❌ <b>никнейм может содержать только буквы, цифры и подчеркивания</b>\n\n✏️ <b>попробуйте еще раз:</b>")
        
        current_nickname = self.db.get_nickname(db_user[0])
        is_first_nickname = current_nickname is None
        
        success, result_message = self.db.set_nickname(db_user[0], nickname)
        
        if success:
            await state.finish()
            if is_first_nickname:
                user_link = f'<a href="tg://user?id={message.from_user.id}">{nickname}</a>'
                text = f"""😎<b>приятно познакомиться, {user_link}!</b>

🎮 <b>Теперь ты можешь играть!</b>

1️⃣<b>используй команду /card чтобы получить свою первую карточку</b>

⁉️ <b>если тебе понадобавится помощь, напиши /help</b>"""
            else:
                text = f"✅ <b>никнейм успешно изменен</b>\n\n<i>новый ник - {nickname}</i>"
            
            await message.reply(text)
        else:
            await message.reply(f"{result_message}\n\n")

    async def start_handler(self, message: types.Message, state: FSMContext):
        if message.chat.type != "private":
            return await message.reply("<b>❌ эту команду нельзя использовать в чате</b>\n\n<i>используйте ее в личных сообщениях с ботом</i>")

        db_user = self.db.get_user(tg_id=message.from_user.id)
        
        if not db_user:
            db_user = self.db.create_user(
                tg_id=message.from_user.id,
                vk_id=None,
                username=message.from_user.username or f"{message.from_user.first_name} {message.from_user.last_name or ''}"
            )
            
            welcome_text = """<b>🤖 добро пожаловать в бота UFCards</b>

🎴 • получай случайную карточку каждые 3 часа!
💬 • добавляй бота в чат, играть с друзьями круче!
🤑 • собери всю коллекцию и стань самым богатым чуваком!

🆒 <b>начинай игру прямо сейчас</b>

чтобы начать играть в бота, нажмите на кнопку «начать»"""
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="🚀 начать", callback_data="start_game"))
            
            return await message.reply(welcome_text, reply_markup=keyboard)
        
        current_nickname = self.db.get_nickname(db_user[0])
        
        if not current_nickname:
            text = """<b>➡️ чтобы начать играть в бота, тебе нужно придумать никнейм и написать его сообщением ниже</b>

<i>вы всегда сможете изменить свой ник, используя команду /nick</i>"""
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="🚀 начать", callback_data="start_game"))
            
            return await message.reply(text, reply_markup=keyboard)
        
        current_time = int(time.time())
        is_first_start = (current_time - db_user[8]) < 60

        if is_first_start:
            text = f"""<b>🤖 привет, писюн!

🎴 • получай случайную карточку каждые 3 часа!
💬 • добавляй бота в чат, играть с друзьями круче!
🤑 • собери всю коллекцию и стань самым богатым чуваком!</b>

<i>помощь по боту - /help</i>"""
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="🚀 начать", callback_data="start_game"))
            
            return await message.reply(text, reply_markup=keyboard)
        else:
            text = f"""<b>🤖 Привет, {current_nickname}!</b>

<b>🎴 • получай случайную карточку каждые 3 часа!
💬 • добавляй бота в чат, играть с друзьями круче!
🤑 • собери всю коллекцию и стань самым богатым чуваком!</b>

<i>помощь по боту - /help</i>"""
            
            return await message.reply(text)

    async def start_game_handler(self, callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        db_user = self.db.get_user(tg_id=user_id)
        
        if not db_user:
            await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
            return
        
        current_nickname = self.db.get_nickname(db_user[0])
        
        if current_nickname:
            await callback.message.edit_text(
                f"<b>🤖 Привет, {current_nickname}!</b>\n\nИспользуй /card чтобы получить карточку!"
            )
        else:
            text = """<b>📝 напиши свой никнейм:</b>

<i>вы всегда сможете изменить свой ник, используя команду /nick</i>"""
            
            await callback.message.edit_text(text)
            await NicknameStates.waiting_for_nickname.set()
        
        await callback.answer()

    async def help_handler(self, message: types.Message):
        help_text = """<b>❔ помощь по боту</b>

ℹ️ <b>основные команды (работают везде):</b>
/card - получить карточку
/stats - посмотреть свою статистику
/top - топ богачей
/code - активировать промо-код
/help - помощь

🔒 <b>команды только в личных сообщениях:</b>
/nick - установить никнейм
/mycards - посмотреть свои карточки
/link - привязать аккаунт (в разработке)

⛓️ <b>полезные ссылки:</b>
t.me/xxxxx - официальный канал бота
t.me/xxxxx - чоткий чат игроков  
t.me/xxxxxbot - техподдержка

🧠 <b>система карточек:</b>
• Карточку можно получить раз в 3 часа
• 3 крутости: обычная, жоская и ИМБОВАЯ
• Новые карточки дают в 2 раза больше UFCoins"""
        
        await message.reply(help_text)

    async def card_handler(self, message: types.Message):
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            db_user = self.db.create_user(
                tg_id=message.from_user.id,
                vk_id=None,
                username=message.from_user.username or f"{message.from_user.first_name} {message.from_user.last_name or ''}"
            )
            if not db_user:
                return await message.reply("❌ ошибка создания пользователя")
        
        current_nickname = self.db.get_nickname(db_user[0])
        if not current_nickname:
            return await message.reply("❌ <b>сначала установи никнейм командой /start</b>")
        
        can_send, time_remaining = self.db.can_send_card(db_user[0])
        
        if not can_send:
            time_left = self.format_time(time_remaining)
            return await message.reply(f"🆕 <b>новую карточку можно получить через {time_left}</b>")
        
        card = random.choices(
            list(config.COOLNESS_WEIGHTS.keys()),
            weights=list(config.COOLNESS_WEIGHTS.values())
        )[0]
        card = random.choice(config.COOLNESS_CARDS[card])
        
        was_new_card = self.db.add_user_card(db_user[0], card["id"])
        coins_to_add = card["UFCoins"] if was_new_card else card["UFCoins"] // 2
        self.db.add_ufcoins(db_user[0], coins_to_add)
        
        if was_new_card:
            caption = "💥 <b>новая карточка!</b>\n\n"
        else:
            caption = "🔄 <b>повторка...</b>\n\n"
        
        caption += f"<b>название - {card['name']}</b>\n"
        caption += f"<b>крутость - {card['coolness']}</b>\n"
        caption += f"<b>+{coins_to_add} UFCoins</b>\n\n"
        caption += "<i>получить новую карточку можно через 3 часа</i>"
        
        try:
            photo = InputFile(card["image_path"])
            await message.reply_photo(photo, caption=caption)
        except Exception as e:
            await message.reply(f"❌ Ошибка загрузки картинки: {str(e)}")

    async def stats_handler(self, message: types.Message):
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            return await message.reply("<b>❌ пользователь не найден</b>")
        
        current_nickname = self.db.get_nickname(db_user[0])
        if not current_nickname:
            return await message.reply("❌ <b>Сначала установи никнейм командой /start</b>")
        
        cards_count, last_card_time, ufcoins, record_ufcoins, nickname = self.db.get_user_stats(db_user[0])
        can_send, time_remaining = self.db.can_send_card(db_user[0])
        
        display_nick = nickname or f"игрок #{db_user[0]}"
        total_cards = len(config.CARDS)
        progress_percent = int(cards_count / total_cards * 100) if total_cards > 0 else 0
        
        if can_send:
            time_text = "\n❕ <i>новую карточку можно получить прямо сейчас</i>"
        else:
            time_left = self.format_time(time_remaining)
            time_text = f"\n⏰ <i>новую карточку можно получить через {time_left}</i>"
        
        text = f"""👤 <b>{display_nick} | профиль</b>

💰 <b>баланс: {ufcoins} UFCoins</b>
🏆 <b>рекорд: {record_ufcoins} UFCoins</b>
🎴 <b>открыто карточек: {cards_count}</b>
📊 <b>прогресс в боте: {progress_percent}%</b>
{time_text}"""
        
        await message.reply(text)

    async def nick_handler(self, message: types.Message, state: FSMContext):
        if message.chat.type != 'private':
            return await message.reply("❌ <b>эту команду нельзя использовать в чате</b>\n\n<i>используйте ее в личных сообщениях с ботом</i>")
        
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            return await message.reply("❌ пользователь не найден")
            
        current_nickname = self.db.get_nickname(db_user[0])
        
        if current_nickname:
            text = f"<b>текущий никнейм: {current_nickname}</b>\n\n✏️ <i>напишите новый никнейм:</i>"
        else:
            text = "📝 <b>напишите ваш никнейм:</b>\n\n<b>вы всегда сможете изменить свой ник, используя команду /nick</b>"
        
        await NicknameStates.waiting_for_nickname.set()
        await message.reply(text)

    async def tops_handler(self, message: types.Message):
        try:
            top_users = self.db.get_rich_top(10)
            record_holder = self.db.get_record_holder()
            
            if not top_users:
                text = "💸 <b>топ богачей</b>\n\n📊 Пока никто не заработал UFCoins"
            else:
                text = "💸 <b>топ богачей</b>\n\n"
                for i, (nickname, ufcoins) in enumerate(top_users, 1):
                    if i == 1:
                        text += f"<b>🥇 1. {nickname} - {ufcoins} UFCoins\n</b>"
                    elif i == 2:
                        text += f"<b>🥈 2. {nickname} - {ufcoins} UFCoins\n</b>"
                    elif i == 3:
                        text += f"<b>🥉 3. {nickname} - {ufcoins} UFCoins\n</b>"
                    else:
                        text += f"<b>{i}. {nickname} - {ufcoins} UFCoins\n</b>"
            
            if record_holder:
                record_nickname, record_coins = record_holder
                text += f"\n🏆 <i>рекорд по UFCoins - {record_nickname}, {record_coins} UFCoins</i>"
            
            await message.reply(text)
            
        except Exception as e:
            await message.reply("❌ ошибка при получении топа")

    async def mycards_handler(self, message: types.Message):
        if message.chat.type != 'private':
            return await message.reply("❌ <b>эта команда доступна только в личных сообщениях с ботом</b>")
        
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            return await message.reply("❌ пользователь не найден")
            
        user_cards = self.db.get_user_cards(db_user[0])
        
        if not user_cards:
            text = """📚 <b>ваша коллекция карточек</b>

🎴 <b>у вас пока нет карточек</b>

<b>получите первую карточку командой /card</b>"""
            return await message.reply(text)
        
        self.user_cards_pages[message.from_user.id] = {
            'page': 0,
            'cards': user_cards,
            'message_id': None
        }
        
        await self.show_mycards_page(message.from_user.id, 0, message.chat.id)

    async def show_mycards_page(self, user_id: int, page: int, chat_id: int):
        if user_id not in self.user_cards_pages:
            return
        
        user_cards = self.user_cards_pages[user_id]['cards']
        total_cards = len(user_cards)
        total_pages = total_cards
        
        if page >= total_pages:
            page = 0
        if page < 0:
            page = total_pages - 1
        
        self.user_cards_pages[user_id]['page'] = page
        
        current_card = user_cards[page]
        
        text = f"""📚 <b>ваша коллекция карточек</b>

🎴 <b>карточка {page + 1} из {total_pages}</b>
📊 <b>всего карточек: {total_cards}/{len(config.CARDS)}</b>

<b>{current_card['name']}</b>
<b>крутость - {current_card['coolness']}</b>
<b>стоимость - {current_card['UFCoins']} UFCoins</b>"""
        
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton(text="⬅️", callback_data="mycards_prev"),
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="current_page"),
            InlineKeyboardButton(text="➡️", callback_data="mycards_next")
        )
        keyboard.add(InlineKeyboardButton(text="❌ закрыть", callback_data="mycards_close"))
        
        try:
            photo = InputFile(current_card["image_path"])
            
            if self.user_cards_pages[user_id]['message_id']:
                try:
                    await self.bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=self.user_cards_pages[user_id]['message_id'],
                        media=types.InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                        reply_markup=keyboard
                    )
                except:
                    msg = await self.bot.send_photo(chat_id, photo, caption=text, reply_markup=keyboard)
                    self.user_cards_pages[user_id]['message_id'] = msg.message_id
            else:
                msg = await self.bot.send_photo(chat_id, photo, caption=text, reply_markup=keyboard)
                self.user_cards_pages[user_id]['message_id'] = msg.message_id
        except Exception as e:
            await self.bot.send_message(chat_id, f"❌ ошибка загрузки картинки: {str(e)}")

    async def mycards_next_handler(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in self.user_cards_pages:
            return await callback.answer("❌ сначала откройте коллекцию командой /mycards", show_alert=True)
        
        current_page = self.user_cards_pages[user_id]['page']
        total_pages = len(self.user_cards_pages[user_id]['cards'])
        new_page = (current_page + 1) % total_pages
        
        await self.show_mycards_page(user_id, new_page, callback.message.chat.id)
        await callback.answer()

    async def mycards_prev_handler(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in self.user_cards_pages:
            return await callback.answer("❌ сначала откройте коллекцию командой /mycards", show_alert=True)
        
        current_page = self.user_cards_pages[user_id]['page']
        total_pages = len(self.user_cards_pages[user_id]['cards'])
        new_page = (current_page - 1) % total_pages
        
        await self.show_mycards_page(user_id, new_page, callback.message.chat.id)
        await callback.answer()

    async def mycards_close_handler(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id in self.user_cards_pages:
            del self.user_cards_pages[user_id]
        
        await callback.message.delete()
        await callback.answer()

    async def promo_code_handler(self, message: types.Message):
        parts = message.text.split()
        
        if len(parts) > 1:
            code = parts[1]
            db_user = self.db.get_user(tg_id=message.from_user.id)
            if not db_user:
                return await message.reply("❌ пользователь не найден")
                
            success, result = self.db.activate_promo_code(db_user[0], code)
            await message.reply(result)
        else:
            await message.reply("""🔐 <b>напишите код, который хотите использовать:</b>

<i>пример:</i> <code>/code FREE</code>""")

    async def code_create_handler(self, message: types.Message):
        if message.from_user.username not in config.ADMINS and f"@{message.from_user.username}" not in config.ADMINS:
            return await message.reply("❌ недостаточно прав")
        
        parts = message.text.split()
        
        if len(parts) == 4:
            _, code_name, coins_str, activations_str = parts
            try:
                coins = int(coins_str)
                activations = int(activations_str)
                
                success, result = self.db.create_promo_code(
                    code_name, coins, activations, f"@{message.from_user.username}"
                )
                await message.reply(result)
            except ValueError:
                await message.reply("❌ <b>неверный формат. Используйте:</b> <code>/codecreate НАЗВАНИЕ КОЛВО_МОНЕТ КОЛВО_АКТИВАЦИЙ</code>")
        else:
            await message.reply("""📝 <b>введите промокод в формате: НАЗВАНИЕ КОЛВО_МОНЕТ КОЛВО_АКТИВАЦИЙ</b>

<b>пример:</b> <code>/codecreate FREE 100 10</code>""")

    def format_time(self, seconds: int) -> str:
        if seconds <= 0:
            return "0 секунд"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours} час {minutes} мин {secs} сек"
        elif minutes > 0:
            return f"{minutes} мин {secs} сек"
        else:
            return f"{secs} сек"

    def run(self):
        """Запуск бота через executor (для совместимости с Bothost)"""
        print("🤖 Telegram bot starting with executor.start_polling...")
        executor.start_polling(self.dp, skip_updates=True)
