# db.py
import sqlite3

# 連線到資料庫（可以改成自己想要的資料庫檔名）
conn = sqlite3.connect('users_data.db')
cursor = conn.cursor()

# 初始化資料表
def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            spirit_stone INTEGER DEFAULT 0,
            last_draw DATETIME DEFAULT NULL,
            last_checkin DATETIME DEFAULT NULL,
            level TEXT DEFAULT '凡人',
            layer TEXT DEFAULT '一層',
            body_level TEXT DEFAULT '凡人肉體',
            body_layer TEXT DEFAULT '一階',
            attack INTEGER DEFAULT 20,
            health INTEGER DEFAULT 100,
            defense INTEGER DEFAULT 10,
            current_health INTEGER DEFAULT 100,
            temp_attack INTEGER DEFAULT 0,
            temp_defense INTEGER DEFAULT 0,
            cultivation INTEGER DEFAULT 0,
            quench INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0
        );
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            quantity INTEGER DEFAULT 0,
            effect TEXT,
            use_restriction TEXT DEFAULT 'both',
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, item_name)
        );
    ''')
    conn.commit()

def get_conn():
    return conn

def get_cursor():
    return cursor
