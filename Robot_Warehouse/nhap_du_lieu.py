
import sqlite3

# Đường dẫn database
DB_PATH = r"D:\cơ sở dữ liệu\Robot_Warehouse\warehouse_robot.db"

try:
    conn = sqlite3.connect(DB_PATH)

    # Bật kiểm tra khóa ngoại
    conn.execute("PRAGMA foreign_keys = ON")

    # Kiểm tra trạng thái
    result = conn.execute(
        "PRAGMA foreign_keys"
    ).fetchone()

    print("Kết nối database thành công!")
    print("Foreign Keys:", result[0])

    # Liệt kê các bảng
    tables = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    print("\nDanh sách bảng:")
    for table in tables:
        print("-", table[0])

    conn.close()

except sqlite3.Error as e:
    print("Lỗi:", e)
