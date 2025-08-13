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

    def get_chat_history(self, user_id, mode=None, limit=50):
        """获取聊天历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if mode is None:
            # 获取所有模式的聊天记录
            query = '''
                    SELECT mode, role, content, timestamp
                    FROM chat_messages
                    WHERE user_id = ?
                    ORDER BY timestamp ASC \
                    '''
            params = [user_id]
        else:
            query = '''
                    SELECT mode, role, content, timestamp
                    FROM chat_messages
                    WHERE user_id = ? AND mode = ?
                    ORDER BY timestamp ASC \
                    '''
            params = [user_id, mode]

        if limit:
            query = query.replace('ORDER BY timestamp ASC', 'ORDER BY timestamp DESC LIMIT ?')
            params.append(limit)
            # 如果有限制，需要重新排序
            cursor.execute(query, params)
            messages = cursor.fetchall()
            messages.reverse()  # 重新按时间正序排列
        else:
            cursor.execute(query, params)
            messages = cursor.fetchall()

        conn.close()
        return messages

def get_user_complete_info(self, user_id):
    """获取用户完整信息"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    # 获取用户基本信息
    cursor.execute('''
                   SELECT user_id, name, grade, major, created_at
                   FROM users
                   WHERE user_id = ?
                   ''', (user_id,))

    user_info = cursor.fetchone()
    conn.close()

    if user_info:
        return {
            'user_id': user_info[0],
            'name': user_info[1],
            'grade': user_info[2],
            'major': user_info[3],
            'created_at': user_info[4]
        }
    return None


def get_user_chat_statistics(self, user_id):
    """获取用户聊天统计信息"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    # 统计各模式的聊天次数
    cursor.execute('''
                   SELECT mode, COUNT(*) as count
                   FROM chat_messages
                   WHERE user_id = ? AND role = 'user'
                   GROUP BY mode
                   ''', (user_id,))

    mode_stats = dict(cursor.fetchall())

    # 统计总聊天次数
    cursor.execute('''
                   SELECT COUNT(*) as total_messages
                   FROM chat_messages
                   WHERE user_id = ?
                     AND role = 'user'
                   ''', (user_id,))

    total_messages = cursor.fetchone()[0]

    # 获取首次和最后一次使用时间
    cursor.execute('''
                   SELECT MIN(timestamp) as first_use, MAX(timestamp) as last_use
                   FROM chat_messages
                   WHERE user_id = ?
                   ''', (user_id,))

    time_range = cursor.fetchone()

    conn.close()

    return {
        'total_messages': total_messages,
        'mode_stats': mode_stats,
        'first_use': time_range[0],
        'last_use': time_range[1]
    }


def get_user_mood_records(self, user_id, limit=None):
    """获取用户心情记录"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    query = '''
            SELECT mood, timestamp
            FROM mood_records
            WHERE user_id = ?
            ORDER BY timestamp DESC \
            '''

    params = [user_id]
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    records = cursor.fetchall()
    conn.close()

    return [{'mood': record[0], 'timestamp': record[1]} for record in records]


def export_user_data(self, user_id):
    """导出用户完整数据"""
    # 获取用户基本信息
    user_info = self.get_user_complete_info(user_id)
    if not user_info:
        return None

    # 获取聊天记录
    chat_history = self.get_chat_history(user_id, mode=None, limit=None)  # 获取所有模式的记录

    # 获取统计信息
    stats = self.get_user_chat_statistics(user_id)

    # 获取心情记录
    mood_records = self.get_user_mood_records(user_id)

    return {
        'user_info': user_info,
        'chat_history': chat_history,
        'statistics': stats,
        'mood_records': mood_records
    }
