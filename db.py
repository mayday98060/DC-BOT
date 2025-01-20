import mysql.connector
import os

DB_HOST = os.getenv("MYSQLHOST", "localhost") 
DB_PORT = os.getenv("MYSQLPORT", "3306")
DB_USER = os.getenv("MYSQLUSER", "root")
DB_PASSWORD = os.getenv("MYSQLPASSWORD", "iclcHuQJdNpHHRFqFvRoZJiznbtRUtoD")
DB_NAME = os.getenv("MYSQLDATABASE", "railway")

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    print("✅ 成功連接到 MySQL 資料庫！")
except mysql.connector.Error as e:
    print(f"❌ 連接 MySQL 失敗: {e}")

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
