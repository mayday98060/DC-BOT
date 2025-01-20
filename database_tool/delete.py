import sqlite3

def delete_column(db_name, table_name, column_to_delete):
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if column_to_delete not in column_names:
                print(f"⚠️ 錯誤: 欄位 '{column_to_delete}' 不存在於表 '{table_name}'。")
                return

            remaining_columns = [col for col in column_names if col != column_to_delete]
            remaining_columns_str = ", ".join(remaining_columns)

            cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old;")

            cursor.execute(f"""
                CREATE TABLE {table_name} AS 
                SELECT {remaining_columns_str} FROM {table_name}_old;
            """)

            cursor.execute(f"DROP TABLE {table_name}_old;")

            print(f"✅ 欄位 '{column_to_delete}' 已成功刪除！")

    except sqlite3.Error as e:
        print(f"⚠️ 資料庫錯誤: {e}")

db_name = 'users_data.db' 
table_name = 'users' 
column_to_delete = input("請輸入要刪除的數值名稱：")

delete_column(db_name, table_name, column_to_delete)
