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
    
    cursor.execute('''
        CREATE TABLE users(
            user_id BIGINT PRIMARY KEY,      -- 玩家 ID
            spirit_stone BIGINT DEFAULT 0,   -- 靈石數量
            last_draw DATE DEFAULT NULL,     -- 占卜時間（日期）
            last_checkin DATE DEFAULT NULL,  -- 簽到時間（日期）
            level VARCHAR(50) DEFAULT '凡人',          -- 修煉境界 (關聯 `cultivation_levels` 表)
            layer VARCHAR(50) DEFAULT '一層',          -- 修煉層數 (關聯 `cultivation_layers` 表)
            body_level VARCHAR(50) DEFAULT '凡人肉體',     -- 煉體境界 (關聯 `body_levels` 表)
            body_layer VARCHAR(50) DEFAULT '一階',     -- 煉體層數 (關聯 `body_layers` 表)
            attack BIGINT DEFAULT 20,        -- 基礎攻擊力
            health BIGINT DEFAULT 100,       -- 氣血值
            defense BIGINT DEFAULT 10,       -- 防禦力
            cultivation BIGINT DEFAULT 0,    -- 修煉修為
            quench BIGINT DEFAULT 0,         -- 煉體精華
            correct_answers BIGINT DEFAULT 0, -- 問答遊戲答對次數
            crit_rate DECIMAL(5,2) DEFAULT 5.00,  -- 基礎爆擊率（預設 5%）
            crit_damage DECIMAL(5,2) DEFAULT 150.00  -- 基礎爆擊傷害（預設 150%）
        );
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE equipment (
            equip_id INT AUTO_INCREMENT PRIMARY KEY,  -- 裝備 ID
            equip_name VARCHAR(100) UNIQUE,           -- 裝備名稱
            rarity VARCHAR(50) DEFAULT '普通',         -- 稀有度
            category ENUM('武器', '護體法寶', '本命法寶') DEFAULT '武器',  -- 裝備類別
            attack INT DEFAULT 0,                     -- 增加的攻擊力
            defense INT DEFAULT 0,                    -- 增加的防禦力
            health INT DEFAULT 0,                     -- 增加的血量
            crit_rate DECIMAL(5,2) DEFAULT 0.00,      -- 增加的暴擊率 (%)
            crit_damage DECIMAL(5,2) DEFAULT 0.00,    -- 增加的暴擊傷害 (%)
            element ENUM('水', '火', '木', '土', '風', '電', '光', '暗', '無') DEFAULT '無',  -- 屬性類型
            price INT DEFAULT 0,                      -- 售價（0 = 非賣品）
            is_sellable BOOLEAN DEFAULT TRUE          -- 是否可購買
        );
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,  -- 道具 ID
            item_name VARCHAR(100) UNIQUE,           -- 道具名稱
            category ENUM('消耗品', '食材', '材料', '藥材', '任務物品', '特殊', '丹藥') DEFAULT '消耗品',  -- 道具類型
            effect VARCHAR(255) DEFAULT '',          -- 道具效果描述
            max_stack INT DEFAULT 99,                -- 最大堆疊數
            usable_in_battle BOOLEAN DEFAULT FALSE,  -- 是否可在戰鬥中使用
            price INT DEFAULT 0,                     -- 售價（0 = 非賣品）
            is_sellable BOOLEAN DEFAULT TRUE         -- 是否可購買
        );
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE user_equipment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,                      -- 玩家 ID
            equip_id INT,                        -- 關聯 `equipment` 表
            equipped BOOLEAN DEFAULT FALSE,      -- 是否已裝備
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (equip_id) REFERENCES equipment(equip_id) ON DELETE CASCADE
        );
    ''')
    conn.commit()
    
    print("✅ 初始化資料庫完成！")

def get_conn():
    return conn

def get_cursor():
    return cursor
