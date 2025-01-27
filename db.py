import mysql.connector
import os

DB_HOST = os.getenv("MYSQLHOST", "mysql.railway.internal")
DB_PORT = os.getenv("MYSQLPORT", "3306")
DB_USER = os.getenv("MYSQLUSER", "root")
DB_PASSWORD = os.getenv("MYSQLPASSWORD", "IebRbauIYseiiwoahmZNbUECpNtoOYpS")
DB_NAME = os.getenv("MYSQLDATABASE", "railway")  # 確保變數名稱一致

print(f"🔍 嘗試連接 MySQL：{DB_HOST}:{DB_PORT}, 使用者: {DB_USER}, 資料庫: {DB_NAME}")

if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
    print("❌ 錯誤：某些 MySQL 環境變數缺失，請確認 Railway Variables 設定。")
    exit(1)

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    print("✅ 成功連接到 MySQL 資料庫！")
except mysql.connector.Error as e:
    print(f"❌ 無法連接 MySQL: {e}")
    exit(1)

def init_db():
    if not conn or not cursor:
        print("❌ MySQL 連線失敗，無法初始化資料庫！")
        return

    cursor.execute("DROP TABLE IF EXISTS inventory;")
    cursor.execute("DROP TABLE IF EXISTS users;")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            spirit_stone INT DEFAULT 0,
            last_draw DATETIME DEFAULT NULL,
            last_checkin DATETIME DEFAULT NULL,
            level VARCHAR(50) DEFAULT '凡人',
            layer VARCHAR(50) DEFAULT '一層',
            body_level VARCHAR(50) DEFAULT '凡人肉體',
            body_layer VARCHAR(50) DEFAULT '一階',
            attack INT DEFAULT 20,
            health INT DEFAULT 100,
            defense INT DEFAULT 10,
            temp_attack INT DEFAULT 0,
            temp_defense INT DEFAULT 0,
            cultivation INT DEFAULT 0,
            quench INT DEFAULT 0,
            correct_answers INT DEFAULT 0
        );
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,                
            item_name VARCHAR(100),
            quantity INT DEFAULT 0,
            effect TEXT,
            use_restriction VARCHAR(50) DEFAULT 'both',
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    ''')
    conn.commit()
    print("✅ 初始化資料庫完成！")

def get_conn():
    return conn

def get_cursor():
    return cursor
