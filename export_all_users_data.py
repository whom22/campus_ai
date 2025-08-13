import sqlite3
from data_exporter import DataExporter
import pandas as pd
from datetime import datetime

def export_all_users_data(database, output_dir="exports"):
    """导出所有用户数据（管理员功能）"""
    import os

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取所有用户
    conn = sqlite3.connect(database.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    exporter = DataExporter(database)
    exported_count = 0

    for user_id in user_ids:
        try:
            markdown_content = exporter.generate_markdown_report(user_id)
            if markdown_content:
                filename = f"用户数据_{user_id}_{datetime.now().strftime('%Y%m%d')}.md"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                exported_count += 1

        except Exception as e:
            print(f"导出用户 {user_id} 数据失败: {e}")

    return exported_count