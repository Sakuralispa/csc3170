import sqlite3
import os
import sys

DB_PATH = "db/mydb.sqlite"
SCHEMA_PATH = "db_construction/sqlite_schema.sql"

def init_db(force=False):
    # 判断是否存在数据库文件
    db_exists = os.path.exists(DB_PATH)

    if db_exists and not force:
        print(f"⚠️ 数据库文件 '{DB_PATH}' 已存在，未做更改。")
        print("若要重建，请运行：python init_db.py force")
        return

    if db_exists and force:
        os.remove(DB_PATH)
        print(f"✅ 已删除旧数据库 '{DB_PATH}'，准备重新初始化。")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
        c.executescript(sql)

    conn.commit()
    conn.close()

    print("✅ 数据库初始化完成！")

if __name__ == "__main__":
    force_rebuild = len(sys.argv) > 1 and sys.argv[1] == "force"
    init_db(force=force_rebuild)
