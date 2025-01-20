import sqlite3
from tabulate import tabulate

def fetch_users():
    try:
        with sqlite3.connect('users_data.db') as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone()
            if not table_exists:
                print("⚠️ 錯誤: 表格 'users' 不存在，請檢查資料庫結構。")
                return

            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            cursor.execute("SELECT * FROM users")
            user_data = cursor.fetchall()

            if not user_data:
                print("📢 表格 'users' 目前沒有任何資料。")
            else:
                print(f"\n📌 用戶總數: {len(user_data)}\n")
                table_data = [dict(zip(column_names, row)) for row in user_data]
                print(tabulate(table_data, headers="keys", tablefmt="grid"))

    except sqlite3.Error as e:
        print(f"⚠️ 資料庫錯誤: {e}")

fetch_users()
