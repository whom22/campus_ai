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


    def get_users_by_profile(self, name, grade, major):
        """根据姓名、年级、专业查找所有匹配的用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 先查看users表中的所有数据（调试用）
            cursor.execute('SELECT user_id, name, grade, major FROM users')
            all_users = cursor.fetchall()
            print(f"数据库中所有用户: {all_users}")  # 调试信息

            # 精确匹配查询
            cursor.execute('''
                           SELECT user_id, name, grade, major, created_at
                           FROM users
                           WHERE TRIM(name) = TRIM(?)
                             AND TRIM(grade) = TRIM(?)
                             AND TRIM(major) = TRIM(?)
                           ''', (name, grade, major))

            users = cursor.fetchall()
            print(f"查询条件: name='{name}', grade='{grade}', major='{major}'")  # 调试信息
            print(f"匹配结果: {users}")  # 调试信息

            conn.close()

            return [{
                'user_id': user[0],
                'name': user[1],
                'grade': user[2],
                'major': user[3],
                'created_at': user[4]
            } for user in users]

        except Exception as e:
            print(f"查询相同用户信息失败: {e}")
            return []


    def export_users_data_by_profile(self, name, grade, major):
        """导出所有具有相同姓名、年级、专业的用户数据"""
        try:
            # 获取所有匹配的用户
            matching_users = self.get_users_by_profile(name, grade, major)

            if not matching_users:
                return None

            all_users_data = []

            for user_info in matching_users:
                user_id = user_info['user_id']

                # 获取该用户的聊天记录
                chat_history = self.get_chat_history(user_id, mode=None, limit=None)

                # 获取统计信息
                stats = self.get_user_chat_statistics(user_id)

                # 获取心情记录
                mood_records = self.get_user_mood_records(user_id)

                all_users_data.append({
                    'user_info': user_info,
                    'chat_history': chat_history,
                    'statistics': stats,
                    'mood_records': mood_records
                })

            return all_users_data

        except Exception as e:
            print(f"导出用户组数据失败: {e}")
            return None

    def get_user_mood_history_by_profile(self, name, grade, major, limit=None):
        """
        获取该用户的所有历史心情记录（通过姓名、年级、专业匹配）
        注意：同一个人可能有多个user_id（重复注册），这里获取所有匹配的记录作为个人历史
        Args:
            name: 姓名
            grade: 年级
            major: 专业
            limit: 限制记录数量
        Returns:
            该用户的所有心情记录列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取该用户的所有user_id（可能因重复注册有多个）
            cursor.execute('''
                           SELECT user_id
                           FROM users
                           WHERE name = ?
                             AND grade = ?
                             AND major = ?
                           ''', (name, grade, major))
            user_ids = [row[0] for row in cursor.fetchall()]

            if not user_ids:
                conn.close()
                return []

            # 构建IN子句获取该用户的所有心情记录
            placeholders = ','.join(['?' for _ in user_ids])

            query = f'''
                SELECT u.user_id, m.mood, m.timestamp
                FROM mood_records m
                JOIN users u ON m.user_id = u.user_id
                WHERE m.user_id IN ({placeholders})
                ORDER BY m.timestamp DESC
            '''

            params = user_ids
            if limit:
                query += ' LIMIT ?'
                params.append(limit)

            cursor.execute(query, params)
            records = cursor.fetchall()
            conn.close()

            # 转换为字典格式
            result = []
            for record in records:
                result.append({
                    'user_id': record[0],
                    'mood': record[1],
                    'timestamp': record[2]
                })

            return result

        except Exception as e:
            print(f"获取用户心情历史失败: {e}")
            return []

    def analyze_personal_mood_trends(self, name, grade, major):
        """
        分析该用户的个人心情变化趋势
        Args:
            name: 姓名
            grade: 年级
            major: 专业
        Returns:
            个人情绪分析结果字典
        """
        try:
            records = self.get_user_mood_history_by_profile(name, grade, major)

            if not records:
                return {
                    'total_records': 0,
                    'mood_distribution': {},
                    'recent_trend': '无历史数据',
                    'user_count': 0
                }

            # 统计心情分布
            mood_count = {}
            user_ids = set()

            for record in records:
                mood = record['mood']
                user_ids.add(record['user_id'])
                mood_count[mood] = mood_count.get(mood, 0) + 1

            # 分析最近趋势（最近10条记录）
            recent_records = records[:10]
            recent_moods = [r['mood'] for r in recent_records]

            # 简单的个人趋势分析
            positive_moods = ['😄 很好', '🙂 不错']
            negative_moods = ['😞 很差', '😕 不太好']

            recent_positive = sum(1 for mood in recent_moods if mood in positive_moods)
            recent_negative = sum(1 for mood in recent_moods if mood in negative_moods)

            if recent_positive > recent_negative:
                trend = '情绪向好'
            elif recent_negative > recent_positive:
                trend = '需要关注'
            else:
                trend = '情绪平稳'

            return {
                'total_records': len(records),
                'mood_distribution': mood_count,
                'recent_trend': trend,
                'user_count': len(user_ids),  # 该用户的账号数量
                'recent_moods': recent_moods[:5]  # 最近5条记录
            }

        except Exception as e:
            print(f"分析个人心情趋势失败: {e}")
            return {
                'total_records': 0,
                'mood_distribution': {},
                'recent_trend': '分析失败',
                'user_count': 0
            }