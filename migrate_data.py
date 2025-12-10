import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def migrate_all_data():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO user_card_history (user_id, card_id, received_time)
            SELECT user_id, last_card_id, last_card_time 
            FROM user_last_card 
            WHERE last_card_id > 0 AND last_card_time > 0
        ''')
        
        migrated_count = cursor.rowcount
        conn.commit()
        
        print(f"migrate data  len {migrated_count} ")
        
        cursor.execute('SELECT COUNT(*) FROM user_card_history')
        total_history = cursor.fetchone()[0]
        print(f"len total history: {total_history}")
        cursor.execute('''
            SELECT u.user_id, u.tg_id, u.vk_id, COUNT(DISTINCT uch.card_id) as card_count
            FROM users u
            LEFT JOIN user_card_history uch ON u.user_id = uch.user_id
            GROUP BY u.user_id
        ''')
        
        users = cursor.fetchall()
        print("\nstats player:")
        for user in users:
            print(f"User ID: {user[0]}, TG: {user[1]}, VK: {user[2]}, Карточек: {user[3]}")
            
    except Exception as e:
        print(f"error migrate: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("start migrate data")
    migrate_all_data()