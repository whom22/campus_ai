#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI校园助手 - 数据导出模块
用于导出用户聊天记录和个人信息为Markdown格式
"""

import io
import base64
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any


class DataExporter:
    """数据导出工具类"""

    def __init__(self, database):
        """
        初始化数据导出器

        Args:
            database: Database实例
        """
        self.db = database

    def format_timestamp(self, timestamp_str: str) -> str:
        """
        格式化时间戳为中文日期格式

        Args:
            timestamp_str: 时间戳字符串

        Returns:
            格式化后的日期字符串
        """
        try:
            # 尝试不同的时间格式
            formats = [
                '%Y-%m-%d %H:%M:%S.%f',  # 带微秒
                '%Y-%m-%d %H:%M:%S',  # 标准格式
                '%Y-%m-%dT%H:%M:%S',  # ISO格式
                '%Y-%m-%dT%H:%M:%S.%f',  # ISO带微秒
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.strftime('%Y年%m月%d日 %H:%M:%S')
                except ValueError:
                    continue

            # 如果都不匹配，尝试解析ISO格式
            if 'T' in timestamp_str:
                timestamp_str = timestamp_str.replace('Z', '+00:00')
                dt = datetime.fromisoformat(timestamp_str.split('+')[0])
                return dt.strftime('%Y年%m月%d日 %H:%M:%S')

            return timestamp_str

        except Exception as e:
            print(f"时间戳格式化失败: {e}")
            return timestamp_str

    def generate_markdown_report(self, user_id: str) -> Optional[str]:
        """
        生成Markdown格式的用户数据报告

        Args:
            user_id: 用户ID

        Returns:
            Markdown格式的报告内容，如果无数据返回None
        """
        try:
            # 导出用户数据
            data = self._export_user_data(user_id)
            if not data:
                return None

            user_info = data['user_info']
            chat_history = data['chat_history']
            stats = data['statistics']
            mood_records = data['mood_records']

            # 生成Markdown内容
            markdown_content = self._build_markdown_content(
                user_info, chat_history, stats, mood_records
            )

            return markdown_content

        except Exception as e:
            print(f"生成Markdown报告失败: {e}")
            return None

    def _export_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        导出用户完整数据

        Args:
            user_id: 用户ID

        Returns:
            包含用户所有数据的字典
        """
        try:
            # 获取用户基本信息
            user_info = self._get_user_complete_info(user_id)
            if not user_info:
                return None

            # 获取聊天记录
            chat_history = self._get_complete_chat_history(user_id)

            # 获取统计信息
            stats = self._get_user_chat_statistics(user_id)

            # 获取心情记录
            mood_records = self._get_user_mood_records(user_id)

            return {
                'user_info': user_info,
                'chat_history': chat_history,
                'statistics': stats,
                'mood_records': mood_records
            }

        except Exception as e:
            print(f"导出用户数据失败: {e}")
            return None

    def _get_user_complete_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户完整信息"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

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

        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None

    def _get_user_chat_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户聊天统计信息"""
        try:
            conn = sqlite3.connect(self.db.db_path)
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

        except Exception as e:
            print(f"获取用户统计信息失败: {e}")
            return {
                'total_messages': 0,
                'mode_stats': {},
                'first_use': None,
                'last_use': None
            }

    def _get_user_mood_records(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取用户心情记录"""
        try:
            conn = sqlite3.connect(self.db.db_path)
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

        except Exception as e:
            print(f"获取心情记录失败: {e}")
            return []

    def _get_complete_chat_history(self, user_id: str) -> List[tuple]:
        """获取用户完整聊天历史"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT mode, role, content, timestamp
                           FROM chat_messages
                           WHERE user_id = ?
                           ORDER BY timestamp ASC
                           ''', (user_id,))

            messages = cursor.fetchall()
            conn.close()

            return messages

        except Exception as e:
            print(f"获取聊天历史失败: {e}")
            return []

    def _build_markdown_content(self, user_info: Dict, chat_history: List,
                                stats: Dict, mood_records: List) -> str:
        """
        构建Markdown内容

        Args:
            user_info: 用户基本信息
            chat_history: 聊天记录
            stats: 统计信息
            mood_records: 心情记录

        Returns:
            完整的Markdown内容
        """
        lines = []

        # 标题和基本信息
        lines.extend([
            "# 🎓 AI校园助手 - 个人数据报告",
            "",
            f"**导出时间:** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "---",
            ""
        ])

        # 用户基本信息
        self._add_user_info_section(lines, user_info)

        # 使用统计
        self._add_statistics_section(lines, stats, mood_records)

        lines.extend(["---", ""])

        # 聊天记录
        self._add_chat_history_section(lines, chat_history)

        # 心情记录详情
        if mood_records:
            self._add_mood_records_section(lines, mood_records)

        # 页脚
        lines.extend([
            "---",
            "",
            "*本报告由AI校园助手自动生成*",
            "",
            "🎓 感谢您使用AI校园助手，祝您学习进步，身心健康！"
        ])

        return '\n'.join(lines)

    def _add_user_info_section(self, lines: List[str], user_info: Dict):
        """添加用户信息部分"""
        lines.extend([
            "## 👤 用户信息",
            "",
            "| 项目 | 信息 |",
            "|------|------|",
            f"| **用户ID** | `{user_info['user_id']}` |",
            f"| **姓名** | {user_info['name'] or '未填写'} |",
            f"| **年级** | {user_info['grade'] or '未填写'} |",
            f"| **专业** | {user_info['major'] or '未填写'} |",
            f"| **注册时间** | {self.format_timestamp(user_info['created_at']) if user_info['created_at'] else '未知'} |",
            ""
        ])

    def _add_statistics_section(self, lines: List[str], stats: Dict, mood_records: List):
        """添加统计信息部分"""
        lines.extend([
            "## 📊 使用统计",
            "",
            f"- **总对话次数:** {stats['total_messages']} 次",
            f"- **首次使用:** {self.format_timestamp(stats['first_use']) if stats['first_use'] else '未知'}",
            f"- **最近使用:** {self.format_timestamp(stats['last_use']) if stats['last_use'] else '未知'}",
            ""
        ])

        # 各模式使用情况
        if stats['mode_stats']:
            lines.extend([
                "### 📈 各模式使用情况",
                ""
            ])
            for mode, count in stats['mode_stats'].items():
                mode_emoji = "🎯" if mode == "学业规划" else "💚"
                lines.append(f"- {mode_emoji} **{mode}:** {count} 次对话")
            lines.append("")

        # 心情记录统计
        if mood_records:
            lines.extend([
                "### 😊 心情记录统计",
                "",
                f"- **记录次数:** {len(mood_records)} 次"
            ])

            # 心情分布统计
            mood_count = {}
            for record in mood_records:
                mood = record['mood']
                mood_count[mood] = mood_count.get(mood, 0) + 1

            if mood_count:
                lines.append("- **心情分布:**")
                for mood, count in sorted(mood_count.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"  - {mood}: {count} 次")
            lines.append("")

    def _add_chat_history_section(self, lines: List[str], chat_history: List):
        """添加聊天记录部分"""
        lines.extend([
            "## 💬 聊天记录",
            ""
        ])

        if not chat_history:
            lines.append("暂无聊天记录。")
            return

        current_mode = None
        conversation_count = 0

        for mode, role, content, timestamp in chat_history:
            # 检查是否切换了模式
            if mode != current_mode:
                if current_mode is not None:
                    lines.append("")
                current_mode = mode
                mode_emoji = "🎯" if mode == "学业规划" else "💚"
                lines.extend([
                    f"### {mode_emoji} {mode}模式",
                    ""
                ])
                conversation_count = 0

            # 如果是用户消息，开始新的对话
            if role == "user":
                conversation_count += 1
                lines.extend([
                    f"#### 对话 {conversation_count}",
                    "",
                    f"**时间:** {self.format_timestamp(timestamp)}",
                    ""
                ])

            # 添加消息内容
            role_display = "👤 **用户**" if role == "user" else "🤖 **AI助手**"
            lines.extend([
                f"{role_display}:",
                ""
            ])

            # 处理多行内容
            content_lines = content.strip().split('\n')
            for content_line in content_lines:
                if content_line.strip():
                    lines.append(content_line)
                else:
                    lines.append("")

            lines.append("")

    def _add_mood_records_section(self, lines: List[str], mood_records: List):
        """添加心情记录详情部分"""
        lines.extend([
            "---",
            "",
            "## 😊 心情记录详情",
            ""
        ])

        # 限制显示最近50条记录
        display_records = mood_records[:50]

        for i, record in enumerate(display_records, 1):
            lines.extend([
                f"### 记录 {i}",
                "",
                f"- **心情:** {record['mood']}",
                f"- **时间:** {self.format_timestamp(record['timestamp'])}",
                ""
            ])

        if len(mood_records) > 50:
            lines.extend([
                f"*注：仅显示最近50条记录，共有{len(mood_records)}条心情记录*",
                ""
            ])

    def create_download_link(self, content: str, filename: str) -> str:
        """
        创建文件下载链接

        Args:
            content: 文件内容
            filename: 文件名

        Returns:
            HTML下载链接
        """
        try:
            b64 = base64.b64encode(content.encode('utf-8')).decode()
            href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}">📥 点击下载</a>'
            return href
        except Exception as e:
            print(f"创建下载链接失败: {e}")
            return "下载链接生成失败"

    def get_export_statistics(self, markdown_content: str) -> Dict[str, Any]:
        """
        获取导出文件的统计信息

        Args:
            markdown_content: Markdown内容

        Returns:
            统计信息字典
        """
        if not markdown_content:
            return {}

        lines = markdown_content.split('\n')

        return {
            'total_lines': len(lines),
            'total_characters': len(markdown_content),
            'total_words': len(markdown_content.split()),
            'file_size_kb': round(len(markdown_content.encode('utf-8')) / 1024, 2)
        }


def main():
    """测试函数"""
    print("DataExporter模块测试")
    # 这里可以添加测试代码


if __name__ == "__main__":
    main()