import sqlite3
from datetime import datetime
import json


class Database:
    def __init__(self, db_path="campus_ai.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 用户表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           user_id
                           TEXT
                           PRIMARY
                           KEY,
                           name
                           TEXT,
                           grade
                           TEXT,
                           major
                           TEXT,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # 聊天记录表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS chat_messages
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           user_id
                           TEXT,
                           mode
                           TEXT,
                           role
                           TEXT,
                           content
                           TEXT,
                           timestamp
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # 心情记录表
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS mood_records
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           user_id
                           TEXT,
                           mood
                           TEXT,
                           timestamp
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        conn.commit()
        conn.close()

    def save_user_info(self, user_id, name, grade, major):
        """保存用户信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, name, grade, major)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, grade, major))

        conn.commit()
        conn.close()

    def save_message(self, user_id, mode, role, content):
        """保存聊天消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO chat_messages (user_id, mode, role, content)
                       VALUES (?, ?, ?, ?)
                       ''', (user_id, mode, role, content))

        conn.commit()
        conn.close()

    def save_mood(self, user_id, mood):
        """保存心情记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO mood_records (user_id, mood)
                       VALUES (?, ?)
                       ''', (user_id, mood))

        conn.commit()
        conn.close()

    def get_chat_history(self, user_id, mode, limit=50):
        """获取聊天历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT role, content, timestamp
                       FROM chat_messages
                       WHERE user_id = ? AND mode = ?
                       ORDER BY timestamp DESC
                           LIMIT ?
                       ''', (user_id, mode, limit))

        messages = cursor.fetchall()
        conn.close()

        return messages