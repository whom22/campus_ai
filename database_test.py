import sqlite3


def view_database():
    conn = sqlite3.connect('campus_ai.db')
    cursor = conn.cursor()

    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("数据库中的表：", tables)

    # 查看用户数据
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print("用户数据：", users)

    # 查看聊天记录
    cursor.execute("SELECT * FROM chat_messages LIMIT 5")
    messages = cursor.fetchall()
    print("最近的聊天记录：", messages)

    conn.close()


if __name__ == "__main__":
    view_database()