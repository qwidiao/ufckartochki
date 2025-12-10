# telegram_bot.py
import random
import time
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import config
from database import Database


class NicknameStates(StatesGroup):
    waiting_for_nickname = State()


class TelegramBot:
    def __init__(self, token: str, db: Database):
        self.bot = Bot(token=token, parse_mode=ParseMode.HTML)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.router = Router()
        self.dp.include_router(self.router)
        self.db = db
        self.user_cards_pages = {}
        
        self.known_text_commands = {
            "карточка", "карта", "карту", "карт", "боец", "карточку",
            "статистика", "стата", "стат", "статс", "статистику",
            "ник", "никнейм", "помощь", "хелп", "хэлп",
            "топ", "топы", "богачи", "топа", 
            "мои карты", "коллекция", "мой сбор", "бойцы"
        }

        self._register_handlers()

    def _register_handlers(self):
        # Обработчик никнейма (state) - должен быть первым
        self.router.message.register(
            self.process_nickname_input,
            NicknameStates.waiting_for_nickname
        )
        
        # Команды
        self.router.message.register(self.start_handler, Command("start"))
        self.router.message.register(self.card_handler, Command("card"))
        self.router.message.register(self.stats_handler, Command("stats"))
        self.router.message.register(self.nick_handler, Command("nick"))
        self.router.message.register(self.help_handler, Command("help"))
        self.router.message.register(self.tops_handler, Command("top"))
        self.router.message.register(self.mycards_handler, Command("mycards"))
        self.router.message.register(self.promo_code_handler, Command("code"))
        self.router.message.register(self.code_create_handler, Command("codecreate"))
        self.router.message.register(self.link_handler, Command("link"))
        
        # Текстовые команды (русские)
        self.router.message.register(
            self.card_handler,
            F.text.lower().in_(["карточка", "карта", "карту", "карт", "боец", "карточку"])
        )
        self.router.message.register(
            self.stats_handler,
            F.text.lower().in_(["статистика", "стата", "стат", "статс", "статистику"])
        )
        self.router.message.register(
            self.nick_handler,
            F.text.lower().in_(["ник", "никнейм"])
        )
        self.router.message.register(
            self.help_handler,
            F.text.lower().in_(["помощь", "хелп", "хэлп"])
        )
        self.router.message.register(
            self.tops_handler,
            F.text.lower().in_(["топ", "топы", "богачи", "топа"])
        )
        self.router.message.register(
            self.mycards_handler,
            F.text.lower().in_(["мои карты", "коллекция", "мой сбор", "бойцы"])
        )
        
        # Callback handlers
        self.router.callback_query.register(self.start_game_handler, F.data == "start_game")
        self.router.callback_query.register(self.mycards_next_handler, F.data == "mycards_next")
        self.router.callback_query.register(self.mycards_prev_handler, F.data == "mycards_prev")
        self.router.callback_query.register(self.mycards_close_handler, F.data == "mycards_close")
        
        # Обработчик неизвестных команд (только в ЛС, без state)
        self.router.message.register(
            self.unknown_handler,
            F.chat.type == "private",
            StateFilter(None)
        )

    async def unknown_handler(self, message: types.Message):
        text = (message.text or "").strip()
        if text.startswith('/'):
            await message.reply(
                "<b>❌ неизвестная команда</b>\n\n"
                "<i>посмотреть список команд можно с помощью /help</i>"
            )

    async def link_handler(self, message: types.Message):
        if message.chat.type != "private":
            return await message.reply("<b>❌ команда /link доступна только в личных сообщениях с ботом</b>")
        return await message.reply('<b>🚀 в разработке</b>')

    async def process_nickname_input(self, message: types.Message, state: FSMContext):
        nickname = message.text.strip()
        
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            await state.clear()
            return await message.reply("❌ <b>ошибка - пользователь не найден</b>")
        
        # Валидация
        if len(nickname) < 3:
            return await message.reply("❌ <b>слишком короткий никнейм (минимум 3 символа)</b>\n\n✏️ <b>попробуйте еще раз:</b>")
        
        if len(nickname) > 20:
            return await message.reply("❌ <b>слишком длинный никнейм (максимум 20 символов)</b>\n\n✏️ <b>попробуйте еще раз:</b>")
        
        if not nickname.replace('_', '').replace(' ', '').isalnum():
            return await message.reply("❌ <b>никнейм может содержать только буквы, цифры и подчеркивания</b>\n\n✏️ <b>попробуйте еще раз:</b>")
        
        current_nickname = self.db.get_nickname(db_user[0])
        is_first_nickname = current_nickname is None
        
        success, result_message = self.db.set_nickname(db_user[0], nickname)
        
        if success:
            await state.clear()
            if is_first_nickname:
                user_link = f'<a href="tg://user?id={message.from_user.id}">{nickname}</a>'
                text = f"""😎<b>приятно познакомиться, {user_link}!</b>

🎮 <b>Теперь ты можешь играть!</b>

1️⃣<b>используй команду /card чтобы получить свою первую карточку</b>

⁉️ <b>если тебе понадобится помощь, напиши /help</b>"""
            else:
                text = f"✅ <b>никнейм успешно изменен</b>\n\n<i>новый ник - {nickname}</i>"
            
            await message.reply(text)
        else:
            await message.reply(result_message)

    async def start_handler(self, message: types.Message, state: FSMContext):
        # Сбрасываем state если есть
        await state.clear()
        
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
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 начать", callback_data="start_game")]
            ])
            
            return await message.reply(welcome_text, reply_markup=keyboard)
        
        current_nickname = self.db.get_nickname(db_user[0])
        
        if not current_nickname:
            text = """<b>➡️ чтобы начать играть в бота, тебе нужно придумать никнейм</b>

<i>нажми кнопку ниже, чтобы продолжить</i>"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 начать", callback_data="start_game")]
            ])
            
            return await message.reply(text, reply_markup=keyboard)
        
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
            db_user = self.db.create_user(
                tg_id=user_id,
                vk_id=None,
                username=callback.from_user.username or callback.from_user.first_name
            )
        
        if not db_user:
            await callback.answer("❌ Ошибка: не удалось создать пользователя", show_alert=True)
            return
        
        current_nickname = self.db.get_nickname(db_user[0])
        
        if current_nickname:
            await callback.message.edit_text(
                f"<b>🤖 Привет, {current_nickname}!</b>\n\nИспользуй /card чтобы получить карточку!"
            )
        else:
            text = """<b>📝 напиши свой никнейм:</b>

<i>ты всегда сможешь изменить его командой /nick</i>"""
            
            await callback.message.edit_text(text)
            await state.set_state(NicknameStates.waiting_for_nickname)
        
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
        
        # Выбор карточки по весам
        coolness = random.choices(
            list(config.COOLNESS_WEIGHTS.keys()),
            weights=list(config.COOLNESS_WEIGHTS.values())
        )[0]
        card = random.choice(config.COOLNESS_CARDS[coolness])
        
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
            photo = FSInputFile(card["image_path"])
            await message.reply_photo(photo, caption=caption)
        except Exception as e:
            await message.reply(f"❌ Ошибка загрузки картинки: {str(e)}\n\nПуть: {card['image_path']}")

    async def stats_handler(self, message: types.Message):
        db_user = self.db.get_user(tg_id=message.from_user.id)
        if not db_user:
            return await message.reply("<b>❌ пользователь не найден. Напиши /start</b>")
        
        current_nickname = self.db.get_nickname(db_user[0])
        if not current_nickname:
            return await message.reply("❌ <b>сначала установи никнейм командой /start</b>")
        
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
            return await message.reply("❌ пользователь не найден. Напиши /start")
            
        current_nickname = self.db.get_nickname(db_user[0])
        
        if current_nickname:
            text = f"<b>текущий никнейм: {current_nickname}</b>\n\n✏️ <i>напишите новый никнейм:</i>"
        else:
            text = "📝 <b>напишите ваш никнейм:</b>"
        
        await state.set_state(NicknameStates.waiting_for_nickname)
        await message.reply(text)

    async def tops_handler(self, message: types.Message):
        try:
            top_users = self.db.get_rich_top(10)
            record_holder = self.db.get_record_holder()
            
            if not top_users:
                text = "💸 <b>топ богачей</b>\n\n📊 Пока никто не заработал UFCoins"
            else:
                text = "💸 <b>топ богачей</b>\n\n"
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                
                for i, (nickname, ufcoins) in enumerate(top_users, 1):
                    medal = medals.get(i, f"{i}.")
                    text += f"<b>{medal} {nickname} - {ufcoins} UFCoins</b>\n"
            
            if record_holder:
                record_nickname, record_coins = record_holder
                text += f"\n🏆 <i>рекорд по UFCoins - {record_nickname}, {record_coins} UFCoins</i>"
            
            await message.reply(text)
            
        except Exception as e:
            await message.reply(f"❌ ошибка при получении топа: {e}")

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
        
        await self._show_mycards_page(message.from_user.id, 0, message.chat.id)

    async def _show_mycards_page(self, user_id: int, page: int, chat_id: int):
        if user_id not in self.user_cards_pages:
            return
        
        data = self.user_cards_pages[user_id]
        user_cards = data['cards']
        total_cards = len(user_cards)
        
        # Циклическая навигация
        page = page % total_cards
        data['page'] = page
        
        current_card = user_cards[page]
        
        text = f"""📚 <b>ваша коллекция карточек</b>

🎴 <b>карточка {page + 1} из {total_cards}</b>
📊 <b>всего карточек: {total_cards}/{len(config.CARDS)}</b>

<b>{current_card['name']}</b>
<b>крутость - {current_card['coolness']}</b>
<b>стоимость - {current_card['UFCoins']} UFCoins</b>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="mycards_prev"),
                InlineKeyboardButton(text=f"{page + 1}/{total_cards}", callback_data="noop"),
                InlineKeyboardButton(text="➡️", callback_data="mycards_next")
            ],
            [InlineKeyboardButton(text="❌ закрыть", callback_data="mycards_close")]
        ])
        
        try:
            photo = FSInputFile(current_card["image_path"])
            
            if data['message_id']:
                try:
                    await self.bot.delete_message(chat_id, data['message_id'])
                except:
                    pass
            
            msg = await self.bot.send_photo(chat_id, photo, caption=text, reply_markup=keyboard)
            data['message_id'] = msg.message_id
            
        except Exception as e:
            await self.bot.send_message(chat_id, f"❌ ошибка загрузки картинки: {str(e)}")

    async def mycards_next_handler(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in self.user_cards_pages:
            return await callback.answer("❌ Используй /mycards", show_alert=True)
        
        current_page = self.user_cards_pages[user_id]['page']
        await self._show_mycards_page(user_id, current_page + 1, callback.message.chat.id)
        await callback.answer()

    async def mycards_prev_handler(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in self.user_cards_pages:
            return await callback.answer("❌ Используй /mycards", show_alert=True)
        
        current_page = self.user_cards_pages[user_id]['page']
        await self._show_mycards_page(user_id, current_page - 1, callback.message.chat.id)
        await callback.answer()

    async def mycards_close_handler(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id in self.user_cards_pages:
            del self.user_cards_pages[user_id]
        
        await callback.message.delete()
        await callback.answer()

    async def promo_code_handler(self, message: types.Message):
        parts = message.text.split(maxsplit=1)
        
        if len(parts) > 1:
            code = parts[1].strip()
            db_user = self.db.get_user(tg_id=message.from_user.id)
            if not db_user:
                return await message.reply("❌ пользователь не найден")
                
            success, result = self.db.activate_promo_code(db_user[0], code)
            await message.reply(result)
        else:
            await message.reply("""🔐 <b>напишите код, который хотите использовать:</b>

<i>пример:</i> <code>/code FREE</code>""")

    async def code_create_handler(self, message: types.Message):
        username = message.from_user.username or ""
        if username not in config.ADMINS and f"@{username}" not in config.ADMINS:
            return await message.reply("❌ недостаточно прав")
        
        parts = message.text.split()
        
        if len(parts) == 4:
            _, code_name, coins_str, activations_str = parts
            try:
                coins = int(coins_str)
                activations = int(activations_str)
                
                success, result = self.db.create_promo_code(
                    code_name, coins, activations, f"@{username}"
                )
                await message.reply(result)
            except ValueError:
                await message.reply("❌ <b>неверный формат</b>\n\n<code>/codecreate КОД МОНЕТЫ АКТИВАЦИИ</code>")
        else:
            await message.reply("""📝 <b>создание промокода:</b>

<code>/codecreate FREE 100 10</code>

<i>создаст код FREE на 100 монет с 10 активациями</i>""")

    def format_time(self, seconds: int) -> str:
        if seconds <= 0:
            return "0 сек"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours} ч")
        if minutes > 0:
            parts.append(f"{minutes} мин")
        if secs > 0 and hours == 0:
            parts.append(f"{secs} сек")
        
        return " ".join(parts)

    async def run(self):
        """Запуск бота через polling"""
        print("🤖 Starting bot with dp.start_polling...")
        await self.dp.start_polling(self.bot)
