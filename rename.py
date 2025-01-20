import sqlite3

conn = sqlite3.connect('users_data.db')
cursor = conn.cursor()

old_column_name = input("請輸入要修改的列名：").strip().lower()
new_column_name = input("請輸入新的列名：").strip().lower()

cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
column_names = [column[1].lower() for column in columns]

if old_column_name not in column_names:
    print(f"錯誤：欄位 '{old_column_name}' 不存在！")
    conn.close()
    exit()

if old_column_name == "user_id":
    print("錯誤：不允許修改主鍵 'user_id'！")
    conn.close()
    exit()

if new_column_name in column_names:
    print(f"錯誤：新欄位名稱 '{new_column_name}' 已經存在！")
    conn.close()
    exit()

try:
    alter_query = f"ALTER TABLE users RENAME COLUMN {old_column_name} TO {new_column_name};"
    cursor.execute(alter_query)
    conn.commit()
    print(f"✅ 成功將 '{old_column_name}' 修改為 '{new_column_name}'。")
except Exception as e:
    print(f"⚠️ 修改失敗：{e}")
finally:
    conn.close()
