import sqlite3
import time
from typing import Tuple, Optional, List
from functools import lru_cache
import config

class Database:
    def __init__(self, path: str = config.DB_PATH):
        self.path = path
        self.init_db()

    def get_conn(self):
        conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE,
                vk_id INTEGER UNIQUE,
                username TEXT,
                nickname TEXT UNIQUE,
                ufcoins INTEGER DEFAULT 0,
                record_ufcoins INTEGER DEFAULT 0,
                last_card_time INTEGER DEFAULT 0,
                last_activity INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            );

            CREATE TABLE IF NOT EXISTS user_cards (
                user_id INTEGER,
                card_id INTEGER,
                PRIMARY KEY (user_id, card_id)
            );

            CREATE TABLE IF NOT EXISTS promo_codes (
                code_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                coins INTEGER,
                max_activations INTEGER,
                current_activations INTEGER DEFAULT 0,
                created_by TEXT,
                created_at INTEGER,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS user_promo_codes (
                user_id INTEGER,
                code_id INTEGER,
                activated_at INTEGER,
                PRIMARY KEY (user_id, code_id)
            );
        ''')
        columns_to_add = [
            "last_card_time INTEGER DEFAULT 0",
            "last_activity INTEGER DEFAULT 0"
        ]
        
        for column_def in columns_to_add:
            try:
                column_name = column_def.split()[0]
                cur.execute(f"SELECT {column_name} FROM users LIMIT 1")
            except:
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {column_def}")
                except:
                    pass
        
        conn.commit()
        conn.close()

    @lru_cache(maxsize=10000)
    def get_user(self, tg_id: Optional[int] = None, vk_id: Optional[int] = None):
        conn = self.get_conn()
        cur = conn.cursor()
        if tg_id:
            cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        elif vk_id:
            cur.execute("SELECT * FROM users WHERE vk_id = ?", (vk_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def create_user(self, tg_id=None, vk_id=None, username="Unknown"):
        conn = self.get_conn()
        cur = conn.cursor()
        current_time = int(time.time())
        try:
            cur.execute(
                "INSERT OR IGNORE INTO users (tg_id, vk_id, username, created_at, last_activity) VALUES (?, ?, ?, ?, ?)", 
                (tg_id, vk_id, username, current_time, current_time)
            )
            conn.commit()
            user_id = cur.lastrowid
            conn.close()
            self.get_user.cache_clear()
            return self.get_user(tg_id=tg_id, vk_id=vk_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            conn.close()
            return None

    def get_nickname(self, user_id: int) -> Optional[str]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT nickname FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

    def set_nickname(self, user_id: int, nickname: str) -> Tuple[bool, str]:
        conn = self.get_conn()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM users WHERE LOWER(nickname) = LOWER(?) AND user_id != ?", (nickname, user_id))
            if cur.fetchone():
                conn.close()
                return False, "<b>❌ этот никнейм уже занят\n\n✏️ напишите новый никнейм:</b>"
            
            cur.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (nickname, user_id))
            conn.commit()
            conn.close()
            self.get_user.cache_clear()
            return True, "<b>✅ никнейм успешно установлен</b>"
        except Exception as e:
            conn.close()
            return False, f"<b>❌ Ошибка: {str(e)}</b>"

    def can_send_card(self, user_id: int) -> Tuple[bool, int]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_card_time FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row or not row[0] or row[0] == 0:
            return True, 0
            
        current_time = int(time.time())
        last_card_time = row[0]
        remaining = config.CARD_COOLDOWN - (current_time - last_card_time)
        
        return (remaining <= 0, max(0, remaining))

    def add_user_card(self, user_id: int, card_id: int) -> bool:
        conn = self.get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM user_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
        exists = cur.fetchone()
        
        if not exists:
            cur.execute("INSERT INTO user_cards (user_id, card_id) VALUES (?, ?)", (user_id, card_id))
        
        current_time = int(time.time())
        cur.execute("UPDATE users SET last_card_time = ? WHERE user_id = ?", (current_time, user_id))
        
        conn.commit()
        conn.close()
        self.get_user.cache_clear()
        return not exists

    def add_ufcoins(self, user_id: int, amount: int):
        conn = self.get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE users SET ufcoins = ufcoins + ?, record_ufcoins = MAX(record_ufcoins, ufcoins + ?) WHERE user_id = ?", 
                (amount, amount, user_id)
            )
            conn.commit()
            conn.close()
            self.get_user.cache_clear()
        except Exception as e:
            print(f"Error adding UFCoins: {e}")
            conn.close()

    def get_user_stats(self, user_id: int):
        conn = self.get_conn()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT 
                (SELECT COUNT(*) FROM user_cards WHERE user_id = u.user_id) as cards_count,
                u.last_card_time,
                u.ufcoins,
                u.record_ufcoins,
                u.nickname,
                u.last_activity
            FROM users u 
            WHERE u.user_id = ?
        ''', (user_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return 0, 0, 0, 0, None, 0
            
        cards_count, last_card_time, ufcoins, record_ufcoins, nickname, last_activity = row
        return cards_count, last_card_time, ufcoins, record_ufcoins, nickname

    def get_user_cards(self, user_id: int) -> List[dict]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT card_id FROM user_cards WHERE user_id = ?", (user_id,))
        
        cards = []
        for (card_id,) in cur.fetchall():
            if card_id in config.CARDS_DICT:
                cards.append(config.CARDS_DICT[card_id])
        
        conn.close()
        return cards

    def get_rich_top(self, limit: int = 10):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT nickname, ufcoins FROM users WHERE nickname IS NOT NULL ORDER BY ufcoins DESC LIMIT ?", 
            (limit,)
        )
        
        top = []
        for row in cur.fetchall():
            nickname, ufcoins = row
            top.append((nickname or "<b>Аноним</b>", ufcoins))
        
        conn.close()
        return top

    def get_record_holder(self):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT nickname, record_ufcoins FROM users WHERE nickname IS NOT NULL ORDER BY record_ufcoins DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return row if row and row[0] else None

    def create_promo_code(self, code: str, coins: int, activations: int, created_by: str) -> Tuple[bool, str]:
        conn = self.get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO promo_codes (code, coins, max_activations, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
                (code.upper(), coins, activations, created_by, int(time.time()))
            )
            conn.commit()
            conn.close()
            return True, f"<b>✅ Код {code.upper()} создан!\n\n💰 {coins} UFCoins\n🎫 {activations} активаций</b>"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "<b>❌ промокод уже существует</b>"
        except Exception as e:
            conn.close()
            return False, f"<b>❌ Ошибка: {str(e)}</b>"

    def activate_promo_code(self, user_id: int, code: str) -> Tuple[bool, str]:
        conn = self.get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT code_id, coins, max_activations, current_activations FROM promo_codes WHERE code = ? AND is_active = 1", 
                (code.upper(),)
            )
            data = cur.fetchone()
            
            if not data:
                conn.close()
                return False, "<b>❌ код не найден или неактивен</b>"
                
            code_id, coins, max_act, curr_act = data
            
            if curr_act >= max_act:
                conn.close()
                return False, "<b>❌ лимит активаций исчерпан</b>"
            
            cur.execute("SELECT 1 FROM user_promo_codes WHERE user_id = ? AND code_id = ?", (user_id, code_id))
            if cur.fetchone():
                conn.close()
                return False, "<b>❌ вы уже активировали этот код</b>"

            current_time = int(time.time())
            cur.execute(
                "INSERT INTO user_promo_codes (user_id, code_id, activated_at) VALUES (?, ?, ?)", 
                (user_id, code_id, current_time)
            )
            cur.execute(
                "UPDATE promo_codes SET current_activations = current_activations + 1 WHERE code_id = ?", 
                (code_id,)
            )
            cur.execute(
                "UPDATE users SET ufcoins = ufcoins + ?, record_ufcoins = MAX(record_ufcoins, ufcoins + ?) WHERE user_id = ?", 
                (coins, coins, user_id)
            )
            
            conn.commit()
            conn.close()
            self.get_user.cache_clear()
            return True, f"<b>✅ код активирован!\n\n💳 +{coins} UFCoins</b>"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"<b>❌ ошибка активации: {str(e)}</b>"

    def update_user_activity(self, user_id: int):
        conn = self.get_conn()
        cur = conn.cursor()
        current_time = int(time.time())
        cur.execute("UPDATE users SET last_activity = ? WHERE user_id = ?", (current_time, user_id))
        conn.commit()
        conn.close()
        self.get_user.cache_clear()