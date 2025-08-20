#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间问题诊断脚本
"""

import sys
from data_exporter import DataExporter
from database import Database  # 替换为实际的模块


def run_diagnosis():
    """运行时间诊断"""
    # 初始化
    db = Database()  # 根据实际情况传入参数
    exporter = DataExporter(db)

    # 获取用户ID
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = input("请输入用户ID: ")

    # 运行诊断
    print(f"\n正在诊断用户 {user_id} 的时间问题...\n")
    exporter.debug_check_timestamp_format(user_id)
    exporter.diagnose_time_issue(user_id)

    # 生成报告看看实际效果
    print("\n生成报告测试...")
    report = exporter.generate_markdown_report(user_id)
    if report:
        # 找到包含时间的部分
        lines = report.split('\n')
        for i, line in enumerate(lines):
            if '最近使用' in line or '首次使用' in line:
                print(f"报告中的时间显示: {line}")


if __name__ == "__main__":
    run_diagnosis()