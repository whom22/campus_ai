import streamlit as st
import os
from ai_client import QianfanChat
from database import Database
from prompts import ACADEMIC_PROMPT, MENTAL_HEALTH_PROMPT
import time
import base64
import sqlite3
from data_exporter import DataExporter
import pandas as pd
from datetime import datetime
from file_processor import FileProcessor, create_file_upload_section
from prompts import format_file_context, FILE_ANALYSIS_PROMPT
from prompts import STRESS_ANALYSIS_PROMPT

# 页面配置
st.set_page_config(
    page_title="AI校园助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏Streamlit的默认UI元素
hide_streamlit_style = """
<style>
/* 保持现有的基础隐藏规则 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 精确隐藏Deploy按钮 - 提高特异性 */
div[data-testid="stAppDeployButton"] {
    display: none !important;
    visibility: hidden !important;
}

/* 精确隐藏主菜单三点按钮 - 提高特异性 */
span[data-testid="stMainMenu"] {
    display: none !important;
    visibility: hidden !important;
}

/* 隐藏整个工具栏动作区域 */
div[data-testid="stToolbarActions"] {
    display: none !important;
}

/* 确保侧边栏控制图标保持可见 */
[data-testid="stIconMaterial"] {
    display: inline-block !important;
    visibility: visible !important;
}

/* 强制隐藏顶部工具栏但保留侧边栏控制 */
.st-emotion-cache-1j22a0y > div.st-emotion-cache-scp8yw {
    display: none !important;
}

/* 保留侧边栏展开控制按钮 */
button[data-testid="baseButton-headerNoPadding"] {
    display: block !important;
    visibility: visible !important;
}
/* 隐藏聊天输入容器 */
.input-container {
    display: none !important;
    visibility: hidden !important;
}
</style>
"""

# 立即应用CSS隐藏样式
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ✅ 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
if "mode" not in st.session_state:
    st.session_state.mode = "学业规划"
# 🔧 新增：输入框控制
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False
# 🔧 新增：用户信息存储到session state
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_grade" not in st.session_state:
    st.session_state.user_grade = "大一"
if "user_major" not in st.session_state:
    st.session_state.user_major = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
if "mode" not in st.session_state:
    st.session_state.mode = "学业规划"
# 🔧 新增：追踪上一次的模式状态
if "previous_mode" not in st.session_state:
    st.session_state.previous_mode = "学业规划"

# 初始化
db = Database()
data_exporter = DataExporter(db)
ai_client = QianfanChat()

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

# 主题CSS函数
def get_theme_css():
    """获取紫色渐变主题CSS"""
    return f"""
<style>
/* 主标题样式 */
.main-header {{
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2rem;
    padding: 1rem 0;
}}

/* 工具按钮样式 */
.stButton > button {{
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 0.6rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
    width: 100%;
}}

.stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}}

/* 模式切换样式 */
.mode-indicator {{
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    text-align: center;
    font-weight: 600;
    margin-bottom: 1rem;
}}

/* 渐变背景 */
.stApp {{
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}}

/* 侧边栏美化 */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #f8f9ff 0%, #e6e9ff 100%) !important;
}}

/* ✅ 优化后的聊天输入区域样式 */
.input-container {{
    background: rgba(255, 255, 255, 0.95) !important;
    margin: 20px 0 !important;
    padding: 15px !important;
    border-radius: 25px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    border: 2px solid #e1e5e9 !important;
}}

/* ✅ 紧凑的文件上传器样式 */
.input-container .stFileUploader {{
    margin-bottom: 0 !important;
}}

.input-container .stFileUploader > div {{
    border: 2px dashed #667eea !important;
    border-radius: 12px !important;
    padding: 6px 8px !important;
    background: rgba(102, 126, 234, 0.05) !important;
    transition: all 0.3s ease !important;
    min-height: 45px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}

.input-container .stFileUploader > div:hover {{
    border-color: #764ba2 !important;
    background: rgba(102, 126, 234, 0.1) !important;
    transform: translateY(-1px) !important;
}}

/* ✅ 文件上传按钮样式 */
.input-container .stFileUploader button {{
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    min-height: 35px !important;
    width: 100% !important;
}}

.input-container .stFileUploader button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3) !important;
}}

/* ✅ 隐藏文件上传的多余文字 */
.input-container .stFileUploader small {{
    display: none !important;
}}

.input-container .stFileUploader div[data-testid="stFileUploaderDropzone"] {{
    padding: 4px !important;
}}

/* 输入框样式优化 */
.input-container .stTextInput > div > div {{
    background: transparent !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: none !important;
}}

.input-container .stTextInput input {{
    background: transparent !important;
    border: none !important;
    color: #333 !important;
    font-size: 16px !important;
    padding: 12px 20px !important;
    height: 45px !important;
}}

.input-container .stTextInput input:focus {{
    outline: none !important;
    box-shadow: none !important;
}}

/* 发送按钮样式 */
.input-container .stButton > button {{
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 12px 20px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
    height: 45px !important;
    font-size: 16px !important;
}}

.input-container .stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4) !important;
}}

/* ✅ 确保三个按钮高度一致 */
.input-container > div {{
    align-items: center !important;
}}

.input-container > div > div {{
    display: flex !important;
    align-items: center !important;
    height: 45px !important;
}}

/* 其他样式保持不变... */
.info-card {{
    background: white;
    padding: 1.5rem;
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #667eea;
    margin: 1rem 0;
}}

.success-message {{
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    font-weight: 600;
}}

</style>
"""


# 🔧 简化的呼吸练习CSS - 只保留核心动画
def get_breathing_exercise_css():
    """获取呼吸练习专用CSS，只保留核心动画"""
    return """
    <style>
        /* 呼吸练习容器 */
        .breathing-exercise-container {
            background: rgba(255, 255, 255, 0.98);
            padding: 2.5rem 1rem;
            border-radius: 20px;
            margin: 1.5rem 0;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        /* 呼吸圆圈 - 核心动画 */
        .breathing-circle {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            margin: 1.5rem auto;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            animation: breathingAnimation 19s ease-in-out infinite;
            transform-origin: center center;
            background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
            box-shadow: 0 6px 24px rgba(76, 175, 80, 0.4);
        }

        /* 呼吸动画关键帧 */
        @keyframes breathingAnimation {
            0% { 
                transform: scale(0.8);
                background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
                box-shadow: 0 6px 24px rgba(76, 175, 80, 0.4);
            }
            21% { 
                transform: scale(1.4);
                background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
                box-shadow: 0 12px 40px rgba(76, 175, 80, 0.6);
            }
            22% {
                background: linear-gradient(135deg, #FF9800 0%, #FFA726 100%);
                box-shadow: 0 12px 40px rgba(255, 152, 0, 0.6);
            }
            57% { 
                transform: scale(1.4);
                background: linear-gradient(135deg, #FF9800 0%, #FFA726 100%);
                box-shadow: 0 12px 40px rgba(255, 152, 0, 0.6);
            }
            58% {
                background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%);
                box-shadow: 0 12px 40px rgba(33, 150, 243, 0.6);
            }
            100% { 
                transform: scale(0.8);
                background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%);
                box-shadow: 0 6px 24px rgba(33, 150, 243, 0.4);
            }
        }

        /* 文字指导容器 */
        .breathing-text-container {
            position: relative;
            height: 80px;
            margin: 2rem 0;
            font-size: 1.4rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(247, 250, 252, 0.8);
            border-radius: 15px;
            padding: 1rem;
        }

        /* 阶段文字样式 */
        .phase-text {
            position: absolute;
            width: 100%;
            text-align: center;
            opacity: 0;
            transition: opacity 0.5s ease-in-out;
            font-family: 'Microsoft YaHei', sans-serif;
            letter-spacing: 0.5px;
            font-size: 1.3rem;
            font-weight: 700;
        }

        .inhale-phase {
            color: #2E7D32;
            animation: showInhaleText 19s infinite;
        }

        .hold-phase {
            color: #E65100;
            animation: showHoldText 19s infinite;
        }

        .exhale-phase {
            color: #1565C0;
            animation: showExhaleText 19s infinite;
        }

        /* 文字显示动画 */
        @keyframes showInhaleText {
            0%, 20% { opacity: 1; }
            21%, 100% { opacity: 0; }
        }

        @keyframes showHoldText {
            0%, 20% { opacity: 0; }
            21%, 57% { opacity: 1; }
            58%, 100% { opacity: 0; }
        }

        @keyframes showExhaleText {
            0%, 57% { opacity: 0; }
            58%, 99% { opacity: 1; }
            100% { opacity: 0; }
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .breathing-circle {
                width: 110px;
                height: 110px;
                font-size: 2rem;
            }
            .breathing-text-container {
                font-size: 1.1rem;
                height: 70px;
                padding: 0.8rem;
            }
            .phase-text {
                font-size: 1.1rem;
            }
        }
    </style>
    """


# 应用主题CSS
st.markdown(get_theme_css(), unsafe_allow_html=True)

# 🎭 主标题
st.markdown("""
<div class="main-header">
    🎓 AI校园助手
    <div style="font-size: 1rem; color: #666; margin-top: 0.5rem;">
        您的专属学业与心理健康顾问
    </div>
</div>
""", unsafe_allow_html=True)

# 🔧 侧边栏
with st.sidebar:
    st.markdown("### 👤 个人信息")

    # 🔧 用户信息输入，绑定到session state
    name = st.text_input(
        "📝 姓名",
        value=st.session_state.user_name,
        key="user_name_input",
        placeholder="请输入您的姓名"
    )

    grade = st.selectbox(
        "🎯 年级",
        ["大一", "大二", "大三", "大四", "研究生"],
        index=["大一", "大二", "大三", "大四", "研究生"].index(st.session_state.user_grade),
        key="user_grade_input",
        help="选择您当前的年级"
    )

    major = st.text_input(
        "🎓 专业",
        value=st.session_state.user_major,
        key="user_major_input",
        placeholder="请输入您的专业"
    )

    # 🔧 修复：实时更新session state
    if name != st.session_state.user_name:
        st.session_state.user_name = name
        if name:  # 只有当名字不为空时才保存
            db.save_user_info(st.session_state.user_id, name, grade, major)

    if grade != st.session_state.user_grade:
        st.session_state.user_grade = grade
        if st.session_state.user_name:  # 确保有姓名时才保存
            db.save_user_info(st.session_state.user_id, st.session_state.user_name, grade, major)

    if major != st.session_state.user_major:
        st.session_state.user_major = major
        if st.session_state.user_name:  # 确保有姓名时才保存
            db.save_user_info(st.session_state.user_id, st.session_state.user_name, grade, major)

    if st.button("💾 保存信息", use_container_width=True):
        if name and major:
            db.save_user_info(st.session_state.user_id, name, grade, major)
            st.success("✅ 信息已保存！")
        else:
            st.warning("⚠️ 请填写完整信息")

    st.divider()

    # 功能选择
    st.markdown("### 🛠️ 功能选择")
    mode = st.radio(
        "选择助手模式",
        ["🎯 学业规划", "💚 心理健康"],
        key="assistant_mode",
        help="选择您需要的服务类型"
    )

    # 🔧 优化的模式更新逻辑 - 检测模式变化并自动清空聊天记录
    current_mode = "学业规划" if "🎯 学业规划" in mode else "心理健康"

    # 检测模式是否发生变化
    if current_mode != st.session_state.previous_mode:
        # 模式发生变化，清空聊天记录
        st.session_state.messages = []

        # 更新模式状态
        st.session_state.mode = current_mode
        st.session_state.previous_mode = current_mode

        # 显示模式切换提示信息
        st.success(f"✅ 已切换到{current_mode}模式，聊天记录已清空")

        # 刷新页面以应用变化
        st.rerun()
    else:
        # 模式未变化，仅更新当前模式（防止意外情况）
        st.session_state.mode = current_mode

    # 清空对话
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.success("✅ 对话记录已清空")
        st.rerun()

    # 统计信息
    st.divider()
    st.markdown("### 📊 使用统计")
    st.metric("💬 对话次数", len(st.session_state.messages) // 2 if st.session_state.messages else 0)
    st.metric("🎯 当前模式", st.session_state.mode)

    # 🔧 设置菜单
    st.divider()
    st.markdown("### ⚙️ 设置选项")

    with st.expander("🔧 系统设置"):

        # 字体大小设置
        font_size = st.slider(
            "📝 字体大小",
            min_value=12,
            max_value=20,
            value=16,
            help="调整界面字体大小",
            key="font_size_slider"  # 添加唯一键
        )

        # 动画效果设置
        enable_animation = st.checkbox(
            "✨ 启用动画效果",
            value=True,
            help="开启或关闭界面动画",
            key="animation_checkbox"  # 添加唯一键
        )

        # 数据管理 - 修复：移除columns布局，改为垂直布局
        st.markdown("#### 📊 数据管理")

        # 导出数据功能
        if st.button("📁 导出数据", use_container_width=True, key="export_data_btn"):
            # 检查用户是否填写了基本信息
            if not st.session_state.user_name or not st.session_state.user_grade or not st.session_state.user_major:
                st.warning("⚠️ 请先填写完整的个人信息（姓名、年级、专业）才能导出数据")
            else:
                # 设置导出状态为激活
                st.session_state.export_mode_active = True

        # 只有在导出模式激活时才显示选择界面
        if st.session_state.get('export_mode_active', False):
            st.markdown("### 📊 选择导出方式")

            # 显示当前用户信息
            st.info(
                f"当前用户信息：{st.session_state.user_name} | {st.session_state.user_grade} | {st.session_state.user_major}")

            # 初始化导出选项状态
            if 'export_option' not in st.session_state:
                st.session_state.export_option = "📄 仅导出我的数据"

            # 导出方式选择 - 使用session_state保持状态
            export_option = st.radio(
                "请选择导出方式：",
                ["📄 仅导出我的数据", "👥 导出所有相同信息用户的数据"],
                index=0 if st.session_state.export_option == "📄 仅导出我的数据" else 1,
                key="export_option_selection"
            )

            # 更新session_state中的选项
            st.session_state.export_option = export_option

            # 显示选项说明
            if export_option == "📄 仅导出我的数据":
                st.write("✅ 将只导出您当前账户的聊天记录和数据")
            else:
                st.write("✅ 将导出数据库中所有姓名、年级、专业相同用户的数据")
                st.warning("⚠️ 此操作可能包含多个用户的数据，请确认后再执行")

            # 执行导出按钮
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.button("🚀 开始导出", use_container_width=True, type="primary", key="start_export_btn"):
                    with st.spinner("📊 正在生成数据报告..."):
                        try:
                            # 获取当前用户信息
                            current_name = st.session_state.user_name
                            current_grade = st.session_state.user_grade
                            current_major = st.session_state.user_major

                            if st.session_state.export_option == "📄 仅导出我的数据":
                                if st.session_state.user_name and st.session_state.user_grade and st.session_state.user_major:
                                    # 先保存当前session信息到数据库
                                    db.save_user_info(
                                        st.session_state.user_id,
                                        st.session_state.user_name,
                                        st.session_state.user_grade,
                                        st.session_state.user_major
                                    )

                                # 原有的单用户导出逻辑
                                markdown_content = data_exporter.generate_markdown_report(st.session_state.user_id)

                                if markdown_content:
                                    # 生成文件名
                                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"个人数据报告_{current_name}_{current_time}.md"

                                    st.success("✅ 个人数据报告生成成功！")

                                    # 提供下载
                                    st.download_button(
                                        label="📥 下载个人报告",
                                        data=markdown_content,
                                        file_name=filename,
                                        mime="text/markdown",
                                        use_container_width=True,
                                        key="download_personal_report"
                                    )

                                    # 统计信息
                                    lines_count = len(markdown_content.split('\n'))
                                    chars_count = len(markdown_content)
                                    st.caption(f"📋 报告包含 {lines_count} 行，{chars_count} 个字符")
                                else:
                                    st.warning("⚠️ 暂无个人数据可导出，请先使用AI校园助手进行对话")

                            else:  # 批量导出相同信息用户的数据
                                if st.session_state.user_name and st.session_state.user_grade and st.session_state.user_major:
                                    db.save_user_info(
                                        st.session_state.user_id,
                                        st.session_state.user_name,
                                        st.session_state.user_grade,
                                        st.session_state.user_major
                                    )

                                # 新的批量导出逻辑
                                st.info(
                                    f"🔍 正在查找所有姓名为'{current_name}'、年级为'{current_grade}'、专业为'{current_major}'的用户...")

                                # 生成批量报告
                                markdown_content = data_exporter.generate_group_markdown_report(
                                    current_name, current_grade, current_major
                                )

                                if markdown_content:
                                    # 查找匹配用户数量
                                    matching_users = db.get_users_by_profile(current_name, current_grade, current_major)
                                    user_count = len(matching_users)

                                    # 生成文件名
                                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"批量数据报告_{current_name}_{current_grade}_{current_major}_{user_count}用户_{current_time}.md"

                                    st.success(f"✅ 批量数据报告生成成功！共找到 {user_count} 个匹配用户")

                                    # 显示匹配用户列表
                                    if user_count > 1:
                                        st.markdown(f"#### 📋 匹配的 {user_count} 个用户详情")
                                        # 创建一个可折叠的详情区域
                                        show_details = st.checkbox(f"显示 {user_count} 个用户的详细信息",
                                                                   key="show_user_details")

                                        if show_details:
                                            # 使用表格形式显示用户信息
                                            user_data = []
                                            for i, user in enumerate(matching_users, 1):
                                                reg_time = user['created_at'] if user['created_at'] else '未知'
                                                user_data.append({
                                                    "序号": i,
                                                    "用户ID": user['user_id'],
                                                    "注册时间": reg_time
                                                })

                                            # 使用DataFrame显示
                                            import pandas as pd

                                            df = pd.DataFrame(user_data)
                                            st.dataframe(df, use_container_width=True, hide_index=True)

                                    # 提供下载
                                    st.download_button(
                                        label=f"📥 下载批量报告 ({user_count}个用户)",
                                        data=markdown_content,
                                        file_name=filename,
                                        mime="text/markdown",
                                        use_container_width=True,
                                        key="download_batch_report"
                                    )

                                    # 统计信息
                                    lines_count = len(markdown_content.split('\n'))
                                    chars_count = len(markdown_content)
                                    st.caption(f"📋 批量报告包含 {lines_count} 行，{chars_count} 个字符")

                                else:
                                    st.warning(
                                        f"⚠️ 未找到姓名为'{current_name}'、年级为'{current_grade}'、专业为'{current_major}'的用户数据")

                        except Exception as e:
                            st.error(f"❌ 导出失败: {str(e)}")

            with col2:
                if st.button("❌ 取消导出", use_container_width=True, key="cancel_export_btn"):
                    # 重置导出状态
                    st.session_state.export_mode_active = False
                    st.session_state.export_option = "📄 仅导出我的数据"
                    st.success("✅ 已取消导出操作")
                    st.rerun()

            with col3:
                # 显示帮助信息
                if st.button("❓ 帮助", use_container_width=True, key="export_help_btn"):
                    st.info("""
                    **导出说明：**

                    📄 **仅导出我的数据**
                    - 只导出当前用户的聊天记录、心情记录等数据
                    - 适合个人使用和备份

                    👥 **导出所有相同信息用户的数据**  
                    - 导出数据库中姓名、年级、专业完全相同的所有用户数据
                    - 适合班级或小组数据分析
                    - 包含多个用户的汇总统计信息
                    """)

        # 如果不在导出模式，添加分隔符（保持原有代码结构）
        if not st.session_state.get('export_mode_active', False):
            st.markdown("---")

        # 清空数据功能
        if st.button("🗑️ 清空数据", use_container_width=True, key="clear_data_btn"):
            # 初始化确认状态
            if 'confirm_clear_data' not in st.session_state:
                st.session_state.confirm_clear_data = False

            if not st.session_state.confirm_clear_data:
                # 显示警告信息
                st.warning("⚠️ 此操作将永久删除您的所有数据！")
                st.markdown("""
                **将被删除的数据：**
                - 所有聊天记录
                - 所有心情记录
                - 个人使用统计
                """)

                # 垂直排列确认按钮
                if st.button("⚠️ 确认清空", key="confirm_clear_yes",
                             type="secondary", use_container_width=True):
                    st.session_state.confirm_clear_data = True
                    st.rerun()

                if st.button("❌ 取消操作", key="confirm_clear_no",
                             use_container_width=True):
                    st.session_state.confirm_clear_data = False
                    st.info("✅ 已取消清空操作")
            else:
                # 执行清空操作
                try:
                    import sqlite3
                    import time

                    # 显示执行中状态
                    with st.spinner("🗑️ 正在清空数据..."):
                        # 清空数据库中的用户数据
                        conn = sqlite3.connect(db.db_path)
                        cursor = conn.cursor()

                        # 删除当前用户的所有记录
                        cursor.execute('DELETE FROM chat_messages WHERE user_id = ?',
                                       (st.session_state.user_id,))
                        cursor.execute('DELETE FROM mood_records WHERE user_id = ?',
                                       (st.session_state.user_id,))

                        # 获取删除的记录数
                        deleted_messages = cursor.rowcount

                        conn.commit()
                        conn.close()

                        # 清空session state
                        st.session_state.messages = []
                        st.session_state.confirm_clear_data = False

                        st.success(f"✅ 数据清空完成！共删除 {deleted_messages} 条记录")
                        st.balloons()

                        # 延迟后刷新页面
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ 清空数据失败: {str(e)}")
                    st.session_state.confirm_clear_data = False

        if st.sidebar.checkbox("🔧 管理员模式", key="admin_mode"):
            admin_password = st.sidebar.text_input("管理员密码", type="password", key="admin_pwd")

            if admin_password == "wu13437414662":  # 管理员密码
                st.sidebar.success("✅ 管理员权限验证成功")

                if st.sidebar.button("📥 批量导出所有用户数据", key="batch_export"):
                    with st.spinner("🔄 正在批量导出用户数据..."):
                        try:
                            export_dir = f"batch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            count = export_all_users_data(db, export_dir)

                            st.success(f"✅ 批量导出完成！成功导出 {count} 个用户的数据")
                            st.info(f"📁 文件保存在: {export_dir} 文件夹中")

                        except Exception as e:
                            st.error(f"❌ 批量导出失败: {e}")

            elif admin_password:
                st.sidebar.error("❌ 管理员密码错误")
    # 帮助信息
    with st.expander("❓ 帮助信息"):
        st.markdown("""
        **使用指南：**
        1. 🏷️ 先填写个人信息
        2. 🎯 选择助手模式
        3. 💬 开始对话交流
        4. 🚀 使用快速工具

        **快捷键：**
        - `Enter` 发送消息
        - `Shift + Enter` 换行

        **技术支持：** support@ai-campus.com
        """)

    # 关于信息
    with st.expander("ℹ️ 关于"):
        st.markdown("""
        **AI校园助手 v1.0**

        🤖 基于先进AI技术  
        🎓 专为大学生设计  
        🔒 隐私安全保护  

        © 2024 AI校园助手团队
        """)

# 主界面
col1, col2 = st.columns([3, 2])  # 调整比例，给聊天区域更多空间

with col1:
    # 模式指示器 - 显示当前模式和状态
    mode_emoji = "🎯" if st.session_state.mode == "学业规划" else "💚"
    st.markdown(f"""
    <div class="mode-indicator">
        {mode_emoji} {st.session_state.mode}助手
        <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.2rem;">
            模式专用对话环境
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 显示当前上传文件状态
    if hasattr(st.session_state, 'uploaded_file_content') and st.session_state.uploaded_file_content:
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%); 
                        padding: 0.5rem 1rem; border-radius: 10px; margin-bottom: 1rem;">
                📎 <strong>已上传文件:</strong> {st.session_state.uploaded_file_content['file_name']}
                <span style="float: right; color: #666; font-size: 0.9rem;">点击右侧工具管理文件</span>
            </div>
            """, unsafe_allow_html=True)

    # 显示历史消息
    chat_container = st.container()
    with chat_container:
        if st.session_state.messages:
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        else:
            # 优化的欢迎消息 - 根据当前模式显示
            welcome_content = {
                "学业规划": {
                    "emoji": "🎓",
                    "features": "📚 制定学习计划 📈 提高学习效率 🎯 规划职业发展",
                    "description": "学业规划专家"
                },
                "心理健康": {
                    "emoji": "💚",
                    "features": "😌 情绪调节 💪 压力管理 🧘 心理健康指导",
                    "description": "心理健康顾问"
                }
            }

            current_welcome = welcome_content[st.session_state.mode]

            st.info(f"""
            {current_welcome["emoji"]} 欢迎使用AI校园助手！

            我是您的{current_welcome["description"]}，可以帮助您：

            {current_welcome["features"]}

            请在下方输入您的问题开始对话吧！
            """)

with col2:
    st.markdown("### 🚀 快速工具")

    if st.session_state.mode == "学业规划":
        # 学业规划工具
        with st.expander("📋 快速生成", expanded=True):
            # 🔧 修改：改为左右结构的按钮布局
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("📅 周计划", use_container_width=True, key="quick_week_plan"):
                    # 🔧 修改：生成内容并添加到聊天记录中
                    with st.spinner("🤖 AI正在为您生成周计划..."):
                        try:
                            plan_prompt = f"你是一个专业的学业规划师。请为{st.session_state.user_grade}{st.session_state.user_major}专业的学生生成一份详细的周学习计划，使用markdown格式，包含具体的时间安排、学习目标和注意事项。"
                            plan_content = ai_client.chat(plan_prompt, "请为我生成本周学习计划")

                            # 添加用户请求到聊天记录
                            st.session_state.messages.append({
                                "role": "user",
                                "content": "📅 请为我生成本周学习计划"
                            })

                            # 添加AI回复到聊天记录
                            formatted_plan = f"## 📅 本周学习计划\n\n{plan_content}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": formatted_plan
                            })

                            # 保存到数据库
                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            "📅 请为我生成本周学习计划")
                            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                            formatted_plan)

                            st.success("✅ 周计划已生成，请查看左侧对话框")
                            st.rerun()

                        except Exception as e:
                            st.error(f"生成周计划时出错：{str(e)}")

            with col_btn2:
                if st.button("💡 学习方法", use_container_width=True, key="quick_study_method"):
                    # 🔧 修改：生成内容并添加到聊天记录中
                    with st.spinner("🤖 AI正在为您推荐学习方法..."):
                        try:
                            method_prompt = f"你是一个学习方法专家。请为{st.session_state.user_major}专业的{st.session_state.user_grade}学生推荐高效的学习方法，使用markdown格式输出，包含具体的学习技巧和实施建议。"
                            method_content = ai_client.chat(method_prompt,
                                                            f"推荐适合{st.session_state.user_major}专业的学习方法")

                            # 添加用户请求到聊天记录
                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"💡 请推荐适合{st.session_state.user_major}专业的学习方法"
                            })

                            # 添加AI回复到聊天记录
                            formatted_methods = f"## 💡 学习方法推荐\n\n{method_content}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": formatted_methods
                            })

                            # 保存到数据库
                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            f"💡 请推荐适合{st.session_state.user_major}专业的学习方法")
                            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                            formatted_methods)

                            st.success("✅ 学习方法已生成，请查看左侧对话框")
                            st.rerun()

                        except Exception as e:
                            st.error(f"生成学习方法时出错：{str(e)}")

        # 🔧 新增：更多快速工具选项
        with st.expander("🎯 更多工具"):
            # 可以添加更多快速工具
            col_tool1, col_tool2 = st.columns(2)

            with col_tool1:
                if st.button("📊 学习分析", use_container_width=True, key="quick_analysis"):
                    with st.spinner("🤖 AI正在分析您的学习情况..."):
                        try:
                            analysis_prompt = f"请作为学业分析师，为{st.session_state.user_grade}{st.session_state.user_major}专业的学生提供学习情况分析和改进建议。"
                            analysis_content = ai_client.chat(analysis_prompt, "请分析我的学习情况并提供改进建议")

                            st.session_state.messages.append({
                                "role": "user",
                                "content": "📊 请分析我的学习情况并提供改进建议"
                            })

                            formatted_analysis = f"## 📊 学习情况分析\n\n{analysis_content}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": formatted_analysis
                            })

                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            "📊 请分析我的学习情况并提供改进建议")
                            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                            formatted_analysis)

                            st.success("✅ 学习分析已生成，请查看左侧对话框")
                            st.rerun()

                        except Exception as e:
                            st.error(f"生成学习分析时出错：{str(e)}")

            with col_tool2:
                if st.button("🎓 职业规划", use_container_width=True, key="quick_career"):
                    with st.spinner("🤖 AI正在为您规划职业发展..."):
                        try:
                            career_prompt = f"请作为职业规划师，为{st.session_state.user_grade}{st.session_state.user_major}专业的学生提供职业发展规划和建议。"
                            career_content = ai_client.chat(career_prompt, "请为我提供职业发展规划建议")

                            st.session_state.messages.append({
                                "role": "user",
                                "content": "🎓 请为我提供职业发展规划建议"
                            })

                            formatted_career = f"## 🎓 职业发展规划\n\n{career_content}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": formatted_career
                            })

                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            "🎓 请为我提供职业发展规划建议")
                            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                            formatted_career)

                            st.success("✅ 职业规划已生成，请查看左侧对话框")
                            st.rerun()

                        except Exception as e:
                            st.error(f"生成职业规划时出错：{str(e)}")

        # 学习资源
        with st.expander("📚 学习资源"):
            st.markdown("""
            **推荐资源：**
            - 📖 [慕课网](https://www.imooc.com/) - 在线课程平台
            - 📝 [知网](https://www.cnki.net/) - 学术论文数据库  
            - 🎥 [B站](https://www.bilibili.com/) - 教学视频
            - 👥 [CSDN](https://www.csdn.net/) - 技术学习社群
            - 📚 [豆瓣读书](https://book.douban.com/) - 专业书籍推荐
            """)

    else:  # 心理健康模式
        # 心情记录
        with st.expander("😊 心情记录", expanded=True):
            mood = st.select_slider(
                "今天的心情如何？",
                options=["😞 很差", "😕 不太好", "😐 一般", "🙂 不错", "😄 很好"],
                help="记录您的心情有助于了解情绪变化"
            )

            if st.button("💾 记录心情", use_container_width=True, key="save_mood"):
                try:
                    db.save_mood(st.session_state.user_id, mood)
                    # 同时添加到聊天记录中
                    mood_message = f"我今天的心情是：{mood}"
                    st.session_state.messages.append({
                        "role": "user",
                        "content": mood_message
                    })

                    # AI回复
                    response = "感谢您分享今天的心情。记录情绪是很好的自我觉察习惯，有助于了解自己的情绪模式。如果您想聊聊今天的感受，我很乐意倾听。"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })

                    db.save_message(st.session_state.user_id, st.session_state.mode, "user", mood_message)
                    db.save_message(st.session_state.user_id, st.session_state.mode, "assistant", response)

                    st.success("✅ 心情已记录，AI回复请查看左侧对话框")
                    st.rerun()

                except Exception as e:
                    st.error(f"记录心情时出错：{str(e)}")

        # 🔧 快速心理支持工具
        with st.expander("💚 快速支持"):
            col_support1, col_support2 = st.columns(2)

            with col_support1:
                if st.button("🌈 情绪分析", use_container_width=True, key="quick_emotion"):
                    # 检查用户是否填写了完整信息
                    if not st.session_state.user_name or not st.session_state.user_grade or not st.session_state.user_major:
                        st.warning("⚠️ 请先填写完整的个人信息（姓名、年级、专业）才能进行情绪分析")
                    else:
                        with st.spinner("🤖 AI正在分析您的情绪数据..."):
                            try:
                                # 获取同名用户的心情记录和趋势分析
                                current_name = st.session_state.user_name
                                current_grade = st.session_state.user_grade
                                current_major = st.session_state.user_major

                                # 获取历史心情数据
                                mood_records = db.get_user_mood_history_by_profile(current_name, current_grade,
                                                                              current_major)
                                trend_analysis = db.analyze_personal_mood_trends(current_name, current_grade, current_major)

                                if not mood_records:
                                    # 如果没有历史数据，提供一般性建议
                                    emotion_content = ai_client.chat(
                                        "请作为心理健康顾问，为没有历史情绪数据的用户提供情绪分析指导。",
                                        f"请为{current_grade}{current_major}专业的学生提供情绪健康建议"
                                    )
                                    analysis_title = "## 🌈 情绪健康指导"
                                    data_info = "暂无历史情绪数据，以下是基于您的专业和年级的一般性建议："
                                else:
                                    # 构建详细的心情记录文本
                                    detailed_records_text = ""
                                    for i, record in enumerate(mood_records[:20], 1):  # 最近20条记录
                                        from datetime import datetime

                                        try:
                                            # 尝试格式化时间戳
                                            if record['timestamp']:
                                                dt = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                                                formatted_time = dt.strftime('%Y年%m月%d日 %H:%M')
                                            else:
                                                formatted_time = '时间未知'
                                        except:
                                            formatted_time = record['timestamp']

                                        detailed_records_text += f"{i}. {record['mood']} - {formatted_time} (用户ID: {record['user_id'][:8]}...)\n"

                                    # 使用专门的情绪分析提示
                                    from prompts import EMOTION_ANALYSIS_PROMPT

                                    emotion_prompt = EMOTION_ANALYSIS_PROMPT.format(
                                        name=current_name,
                                        grade=current_grade,
                                        major=current_major,
                                        user_count=trend_analysis['user_count'],
                                        total_records=trend_analysis['total_records'],
                                        mood_distribution=trend_analysis['mood_distribution'],
                                        recent_trend=trend_analysis['recent_trend'],
                                        recent_moods=trend_analysis.get('recent_moods', []),
                                        detailed_records=detailed_records_text,
                                        user_question="请帮我分析当前的情绪状态并提供个性化建议"
                                    )

                                    emotion_content = ai_client.chat(emotion_prompt, "请基于历史数据分析我的情绪状态")
                                    analysis_title = "## 🌈 基于历史数据的情绪分析报告"
                                    data_info = f"✅ 已分析 {trend_analysis['user_count']} 个用户的 {trend_analysis['total_records']} 条心情记录"

                                # 添加到聊天记录
                                user_message = "🌈 请帮我分析当前的情绪状态并提供调节建议"
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": user_message
                                })

                                # 格式化AI回复
                                formatted_emotion = f"{analysis_title}\n\n**数据概况：** {data_info}\n\n{emotion_content}"
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": formatted_emotion
                                })

                                # 保存到数据库
                                db.save_message(st.session_state.user_id, st.session_state.mode, "user", user_message)
                                db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                                formatted_emotion)

                                st.success("✅ 情绪分析已生成，请查看左侧对话框")
                                st.rerun()

                            except Exception as e:
                                st.error(f"生成情绪分析时出错：{str(e)}")

            with col_support2:
                if st.button("💪 压力管理", use_container_width=True, key="quick_stress"):
                    # 检查用户是否填写了完整信息
                    if not st.session_state.user_name or not st.session_state.user_grade or not st.session_state.user_major:
                        st.warning("⚠️ 请先填写完整的个人信息（姓名、年级、专业）才能进行压力分析")
                    else:
                        with st.spinner("🤖 AI正在分析您的压力状态..."):
                            try:
                                # 获取用户信息
                                current_name = st.session_state.user_name
                                current_grade = st.session_state.user_grade
                                current_major = st.session_state.user_major

                                # 获取历史心情数据
                                mood_records = db.get_user_mood_history_by_profile(current_name, current_grade,
                                                                                   current_major)
                                trend_analysis = db.analyze_personal_mood_trends(current_name, current_grade,
                                                                                 current_major)

                                if not mood_records:
                                    # 如果没有历史数据，提供基于专业的一般性压力管理建议
                                    stress_content = ai_client.chat(
                                        f"请作为压力管理专家，为{current_grade}{current_major}专业的学生提供专业相关的压力管理建议。",
                                        f"请为{current_grade}{current_major}专业的学生提供针对性的压力管理技巧和方法"
                                    )
                                    analysis_title = "## 💪 专业压力管理指导"
                                    data_info = f"基于{current_grade}{current_major}专业特点的压力管理建议："
                                else:
                                    # 构建详细的心情记录文本
                                    detailed_records_text = ""
                                    for i, record in enumerate(mood_records[:20], 1):  # 最近20条记录
                                        try:
                                            # 尝试格式化时间戳
                                            if record['timestamp']:
                                                dt = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                                                formatted_time = dt.strftime('%Y年%m月%d日 %H:%M')
                                            else:
                                                formatted_time = '时间未知'
                                        except Exception:
                                            formatted_time = record['timestamp'] if record['timestamp'] else '时间未知'

                                        detailed_records_text += f"{i}. {record['mood']} - {formatted_time} (用户ID: {record['user_id'][:8]}...)\n"

                                    # 使用专门的压力分析提示
                                    from prompts import STRESS_ANALYSIS_PROMPT

                                    stress_prompt = STRESS_ANALYSIS_PROMPT.format(
                                        name=current_name,
                                        grade=current_grade,
                                        major=current_major,
                                        user_count=trend_analysis['user_count'],
                                        total_records=trend_analysis['total_records'],
                                        mood_distribution=trend_analysis['mood_distribution'],
                                        recent_trend=trend_analysis['recent_trend'],
                                        recent_moods=trend_analysis.get('recent_moods', []),
                                        detailed_records=detailed_records_text,
                                        user_question="请基于我的历史情绪数据分析我的压力状态并提供管理建议"
                                    )

                                    stress_content = ai_client.chat(stress_prompt,
                                                                    "请基于历史数据分析我的压力状态并提供管理建议")
                                    analysis_title = "## 💪 基于历史数据的个人压力分析"
                                    data_info = f"✅ 已分析 {trend_analysis['user_count']} 个账号的 {trend_analysis['total_records']} 条心情记录"

                                # 添加到聊天记录
                                user_message = "💪 请为我提供有效的压力管理技巧和方法"
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": user_message
                                })

                                # 格式化AI回复
                                formatted_stress = f"{analysis_title}\n\n**数据概况：** {data_info}\n\n{stress_content}"
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": formatted_stress
                                })

                                # 保存到数据库
                                db.save_message(st.session_state.user_id, st.session_state.mode, "user", user_message)
                                db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                                formatted_stress)

                                st.success("✅ 压力管理建议已生成，请查看左侧对话框")
                                st.rerun()

                            except Exception as e:
                                st.error(f"生成压力管理建议时出错：{str(e)}")

        # 🔧 放松技巧
        with st.expander("🧘 放松技巧"):
            # 🔧 初始化呼吸练习相关状态
            if "breathing_panel_active" not in st.session_state:
                st.session_state.breathing_panel_active = False
            if "breathing_exercise_active" not in st.session_state:
                st.session_state.breathing_exercise_active = False
            if "show_video" not in st.session_state:
                st.session_state.show_video = False

            # 🔧 呼吸练习CSS
            st.markdown(get_breathing_exercise_css(), unsafe_allow_html=True)

            # 呼吸练习主入口按钮
            if st.button("🌬️ 呼吸练习", use_container_width=True, type="primary"):
                st.session_state.breathing_panel_active = True
                st.session_state.breathing_exercise_active = False
                st.session_state.show_video = False
                st.rerun()

            # 🔧 修复的呼吸练习面板渲染
            if st.session_state.breathing_panel_active:

                if st.session_state.show_video:
                    # 🔧 视频播放界面
                    st.markdown("#### 📺 呼吸练习指导视频")

                    video_path = "breath.mp4"

                    try:
                        if os.path.exists(video_path):
                            st.video(video_path)
                        else:
                            st.warning("⚠️ 视频文件未找到，显示在线资源")

                            # 提供在线视频资源
                            st.markdown("""
                            <div class="breathing-instruction-card">
                                <h5 style="color: #667eea; margin: 0 0 1rem 0;">🎥 在线指导资源</h5>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                                    <a href="https://www.youtube.com/watch?v=YRPh_GaiL8s" target="_blank" 
                                       style="text-decoration: none; color: #667eea; font-weight: 600; display: block; 
                                              padding: 12px; background: white; border-radius: 8px; 
                                              box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                                        🌐 YouTube 呼吸练习
                                    </a>
                                    <a href="https://www.bilibili.com/video/BV1xx411c7uD" target="_blank" 
                                       style="text-decoration: none; color: #667eea; font-weight: 600; display: block; 
                                              padding: 12px; background: white; border-radius: 8px; 
                                              box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                                        📺 B站 冥想教程
                                    </a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"❌ 视频播放出错：{str(e)}")

                    # 返回按钮
                    if st.button("🔙 返回练习选项", use_container_width=True, key="back_from_video"):
                        st.session_state.show_video = False
                        st.rerun()

                elif not st.session_state.breathing_exercise_active:
                    # 🔧 练习说明界面
                    st.markdown("""
                    <div class="breathing-instruction-card">
                        <h4 style="color: #667eea; margin: 0 0 1rem 0; font-size: 1.4rem;">🍃 4-7-8呼吸法</h4>
                        <p style="margin: 0.5rem 0; color: #555; line-height: 1.7; font-size: 1rem;">
                            这是一种科学验证的放松技巧，通过调节呼吸节奏来激活副交感神经系统，
                            有效缓解压力、焦虑，并改善睡眠质量。建议练习3-5个周期。
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # 🔧 简化的练习步骤说明
                    st.markdown("""
                    <div class="breathing-instruction-card">
                        <h4 style="color: #667eea; margin: 0 0 1rem 0;">🍃 4-7-8呼吸法</h4>
                        <p style="color: #555; line-height: 1.7; margin-bottom: 1.5rem;">
                            科学验证的放松技巧，有效缓解压力和焦虑。建议练习3-5个周期。
                        </p>
                        <div style="display: flex; justify-content: space-around; gap: 1rem;">
                            <div style="text-align: center; flex: 1;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💨</div>
                                <div style="font-weight: 700; color: #4CAF50;">吸气 4秒</div>
                                <div style="font-size: 0.9rem; color: #666;">鼻子吸气</div>
                            </div>
                            <div style="text-align: center; flex: 1;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⏸️</div>
                                <div style="font-weight: 700; color: #FF9800;">屏息 7秒</div>
                                <div style="font-size: 0.9rem; color: #666;">保持呼吸</div>
                            </div>
                            <div style="text-align: center; flex: 1;">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💨</div>
                                <div style="font-weight: 700; color: #2196F3;">呼气 8秒</div>
                                <div style="font-size: 0.9rem; color: #666;">嘴巴呼气</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 🔧 修复的控制按钮
                    col_start, col_video, col_close = st.columns(3)
                    with col_start:
                        if st.button("⏰ 开始引导练习", use_container_width=True, key="start_breathing_guide",
                                     type="primary"):
                            st.session_state.breathing_exercise_active = True
                            st.rerun()
                    with col_video:
                        if st.button("📺 观看指导视频", use_container_width=True, key="show_video_btn"):
                            st.session_state.show_video = True
                            st.rerun()
                    with col_close:
                        if st.button("❌ 关闭练习", use_container_width=True, key="close_breathing_panel"):
                            st.session_state.breathing_panel_active = False
                            st.session_state.breathing_exercise_active = False
                            st.session_state.show_video = False
                            st.rerun()
                else:
                    # 🔧 最简化的呼吸练习界面 - 纯动画
                    st.markdown("### 🧘‍♀️ 正在进行呼吸练习")
                    st.info("跟随下方动画进行 4-7-8 呼吸法：绿色扩大时吸气4秒 → 橙色保持时屏息7秒 → 蓝色缩小时呼气8秒")

                    # 🔧 纯动画区域 - 移除所有可能冲突的HTML
                    st.markdown("""
                    <div style="background: rgba(255, 255, 255, 0.98); padding: 3rem 1rem; border-radius: 20px; 
                                margin: 1.5rem 0; text-align: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);">
                        <div class="breathing-circle"></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 🔧 简化的练习指导
                    st.markdown("**练习要点：** 鼻子吸气4秒 → 保持呼吸7秒 → 嘴巴呼气8秒，重复3-5个周期即可。")

                    # 🔧 修复的控制按钮区域
                    col_finish, col_back = st.columns(2)
                    with col_finish:
                        if st.button("✅ 完成练习", use_container_width=True, key="finish_breathing", type="primary"):
                            st.session_state.breathing_exercise_active = False
                            st.session_state.breathing_panel_active = False
                            st.success("🎉 练习完成！希望您感到更加放松和平静。")
                            st.balloons()
                            st.rerun()
                    with col_back:
                        if st.button("🔙 返回说明", use_container_width=True, key="back_to_instructions"):
                            st.session_state.breathing_exercise_active = False
                            st.rerun()

            if "meditation_active" not in st.session_state:
                st.session_state.meditation_active = False

            # 🔧 正念冥想按钮 - 改为状态控制
            if st.button("💭 正念冥想", use_container_width=True):
                st.session_state.meditation_active = True
                st.rerun()

            # 🔧 正念冥想界面 - 类似呼吸练习的状态管理
            if st.session_state.meditation_active:
                # 🔧 简化的冥想说明界面
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(79, 172, 254, 0.08) 0%, rgba(0, 242, 254, 0.08) 100%);
                            border: 1px solid rgba(79, 172, 254, 0.2); border-radius: 15px; 
                            padding: 1.5rem; margin: 1rem 0;">
                    <h4 style="color: #4facfe; margin: 0 0 1rem 0;">🧘 5分钟正念冥想</h4>
                    <p style="color: #555; line-height: 1.7; margin-bottom: 1.5rem;">
                        科学验证的心理放松技巧，有效缓解压力和焦虑，提升专注力。建议每日练习5-10分钟。
                    </p>
                    <div style="display: flex; justify-content: space-around; gap: 1rem; flex-wrap: wrap;">
                        <div style="text-align: center; flex: 1; min-width: 100px;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🪑</div>
                            <div style="font-weight: 700; color: #4facfe;">舒适坐姿</div>
                            <div style="font-size: 0.9rem; color: #666;">脊背挺直</div>
                        </div>
                        <div style="text-align: center; flex: 1; min-width: 100px;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">👁️</div>
                            <div style="font-weight: 700; color: #00d4aa;">轻闭双眼</div>
                            <div style="font-size: 0.9rem; color: #666;">或轻柔凝视</div>
                        </div>
                        <div style="text-align: center; flex: 1; min-width: 100px;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌬️</div>
                            <div style="font-weight: 700; color: #ff6b6b;">专注呼吸</div>
                            <div style="font-size: 0.9rem; color: #666;">感受气息</div>
                        </div>
                        <div style="text-align: center; flex: 1; min-width: 100px;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧠</div>
                            <div style="font-weight: 700; color: #ffa726;">观察思绪</div>
                            <div style="font-size: 0.9rem; color: #666;">不评判接纳</div>
                        </div>
                        <div style="text-align: center; flex: 1; min-width: 100px;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                            <div style="font-weight: 700; color: #9c27b0;">温和回归</div>
                            <div style="font-size: 0.9rem; color: #666;">回到呼吸</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 添加冥想资源链接
                st.markdown("#### 🎵 冥想辅助资源")
                col_med1, col_med2 = st.columns(2)

                meditation_resources = [
                    ("🎧 引导冥想", "https://www.bilibili.com/video/BV1AG4y167xD/"),
                    ("🌊 自然声音", "https://soundvery.com/")
                ]

                for i, (resource_name, resource_link) in enumerate(meditation_resources):
                    with [col_med1, col_med2][i]:
                        if st.button(resource_name, use_container_width=True, key=f"meditation_resource_{i}"):
                            st.success(f"✅ 正在打开{resource_name}")
                            st.markdown(f"""
                            <div style="background: #e3f2fd; padding: 12px; border-radius: 8px; text-align: center; margin: 8px 0;">
                                <a href="{resource_link}" target="_blank" 
                                   style="color: #1976d2; text-decoration: none; font-weight: bold; font-size: 16px;">
                                    🔗 点击访问 {resource_name}
                                </a>
                                <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                    链接：{resource_link}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                # 🔧 添加关闭按钮
                if st.button("❌ 关闭冥想", use_container_width=True, key="close_meditation"):
                    st.session_state.meditation_active = False
                    st.rerun()


        # 心理健康资源
        with st.expander("📞 求助资源"):
            st.markdown("### 🏥 华南农业大学心理健康服务")
            st.markdown("""
            **校园心理健康中心**
            - 📍 地址：广州市天河区华南农业大学华山活动中心三楼
            """)

            st.divider()

            st.markdown("### 📱 国家级心理援助热线")
            st.markdown("""
            **24小时专业心理援助**
            - 📞 **12356** - 全国统一心理援助热线（国家卫生健康委官方）
            - 📞 **400-161-9995** - 青少年心理健康专线
            - 🆘 **120** - 紧急心理危机救助电话
            """)

            st.divider()

            st.markdown("### 🌐 官方在线心理健康平台")
            st.markdown("""
            **权威心理健康资源**
            - 🏛️ [国家心理健康网](https://www.cnnmh.cn/) - 国家官方心理健康信息平台
            - 🔬 [国家心理健康防治中心](https://ncmhc.org.cn/) - 权威心理健康科普与服务
            - 📚 [中国心理学会](http://www.cpsbeijing.org/) - 专业心理学术组织平台
            - 👥 **校园心理健康社团** - 联系各学院心理委员或辅导员参与
            """)

            st.divider()

            st.markdown("### 🏥 专业心理治疗机构")
            st.markdown("""
            **广州地区三甲医院心理科**
            - 🏥 中山大学附属第三医院精神心理科
            - 🧠 广州医科大学附属脑科医院  
            - 💊 南方医科大学南方医院心理科
            - 💡 **就医建议：** 严重心理问题请及时就医，可通过校医院转诊获得专业指导
            """)

            # 紧急情况提醒保持原有的突出显示效果
            st.markdown("---")
            st.error("""
            🚨 **紧急心理危机处理指南**

            如遇紧急心理危机，请立即采取以下行动：
            1. 拨打 120 急救电话
            2. 联系校园安保：020-85280131  
            3. 通知家人或朋友陪同

            💝 **重要提醒：** 生命宝贵，任何困难都有解决方案，请勇敢寻求帮助！
            """)

    # 文件相关工具
    if hasattr(st.session_state, 'uploaded_file_content') and st.session_state.uploaded_file_content:
        with st.expander("📎 文件相关工具", expanded=True):
            col_file1, col_file2 = st.columns(2)

            with col_file1:
                if st.button("📊 重新分析文件", use_container_width=True, key="reanalyze_file"):
                    file_info = st.session_state.uploaded_file_content
                    file_analysis_prompt = FILE_ANALYSIS_PROMPT.format(
                        file_name=file_info['file_name'],
                        file_type=file_info.get('file_type', '未知'),
                        content=file_info['content'][:2000]
                    )

                    with st.spinner("🔍 重新分析文件..."):
                        try:
                            analysis = ai_client.chat(file_analysis_prompt, "请重新分析这个文件")

                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"📊 请重新分析文件：{file_info['file_name']}"
                            })
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"## 📊 文件重新分析报告\n\n{analysis}"
                            })

                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            f"📊 请重新分析文件：{file_info['file_name']}")
                            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                            f"## 📊 文件重新分析报告\n\n{analysis}")

                            st.rerun()
                        except Exception as e:
                            st.error(f"重新分析失败：{str(e)}")

            with col_file2:
                if st.button("🗑 清除文件", use_container_width=True, key="clear_file"):
                    if 'uploaded_file_content' in st.session_state:
                        del st.session_state.uploaded_file_content
                    st.success("✅ 文件已清除")
                    st.rerun()

# 🔧 新增：模式特定的CSS样式优化
def get_mode_specific_css():
    """根据当前模式返回特定的CSS样式"""
    if st.session_state.mode == "学业规划":
        return """
        <style>
        .mode-indicator {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-left: 4px solid #4CAF50;
        }
        </style>
        """
    else:  # 心理健康模式
        return """
        <style>
        .mode-indicator {
            background: linear-gradient(90deg, #ffecd2 0%, #fcb69f 100%);
            color: #8B4513;
            border-left: 4px solid #FF6B6B;
        }
        </style>
        """

# 应用模式特定样式
st.markdown(get_mode_specific_css(), unsafe_allow_html=True)

# 🔧 消息处理函数
def process_user_message(message_content):
    """处理用户消息的独立函数 - 支持文件上下文"""
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": message_content})

    # 获取AI响应
    with st.spinner("🤖 AI正在思考中..."):
        try:
            # 获取文件上下文
            file_context = ""
            if hasattr(st.session_state, 'uploaded_file_content') and st.session_state.uploaded_file_content:
                file_context = format_file_context(st.session_state.uploaded_file_content)

            # 根据模式选择prompt，使用session state中的用户信息
            if st.session_state.mode == "学业规划":
                system_prompt = ACADEMIC_PROMPT.format(
                    grade=st.session_state.user_grade,
                    major=st.session_state.user_major if st.session_state.user_major else "通用专业",
                    question=message_content,
                    file_context=file_context
                )
            else:
                system_prompt = MENTAL_HEALTH_PROMPT.format(
                    situation=message_content,
                    file_context=file_context
                )

            # 调用AI
            response = ai_client.chat(system_prompt, message_content)

            # 如果有文件上下文，在回复中添加提示
            if file_context:
                response = f"💡 *基于您上传的文件内容分析*\n\n{response}"

            # 保存到数据库
            db.save_message(st.session_state.user_id, st.session_state.mode, "user", message_content)
            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant", response)

            # 添加AI响应到历史
            st.session_state.messages.append({"role": "assistant", "content": response})
            return True

        except Exception as e:
            st.error(f"处理消息时出现错误：{str(e)}")
            # 如果出错，移除已添加的用户消息
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
            return False


# ✅ 美化的聊天输入区域
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# 创建文件上传状态
if "uploaded_file_for_chat" not in st.session_state:
    st.session_state.uploaded_file_for_chat = None
if "uploaded_file_name" not in st.session_state:  # 新增：单独存储文件名
    st.session_state.uploaded_file_name = None
if "show_file_uploader" not in st.session_state:
    st.session_state.show_file_uploader = False

# 主要输入区域：输入框 + 文件按钮 + 发送按钮
col_input, col_file, col_send = st.columns([7, 1, 1.2])

# 输入框列
with col_input:
    input_key = f"main_chat_input_{st.session_state.get('input_reset_counter', 0)}"
    user_input = st.text_input(
        "消息输入",
        placeholder="💬 请输入您的问题... (按Enter发送)",
        key=input_key,
        label_visibility="collapsed"
    )

# 文件按钮列 - 使用普通按钮
with col_file:
    # 根据是否有文件显示不同的按钮样式 - 修复逻辑
    if st.session_state.uploaded_file_for_chat is not None:
        button_text = "✅"
        # 修复：安全获取文件名
        if hasattr(st.session_state.uploaded_file_for_chat, 'name'):
            file_name = st.session_state.uploaded_file_for_chat.name
        else:
            file_name = st.session_state.uploaded_file_name or "未知文件"
        button_help = f"已选择: {file_name}"
    else:
        button_text = "📎"
        button_help = "点击上传文件"

    if st.button(
            button_text,
            use_container_width=True,
            help=button_help,
            key="file_upload_trigger"
    ):
        st.session_state.show_file_uploader = True
        st.rerun()

# 发送按钮列
with col_send:
    send_clicked = st.button("➤ 发送", use_container_width=True, type="primary")

st.markdown('</div>', unsafe_allow_html=True)

# 文件上传弹窗（当点击文件按钮时显示）
if st.session_state.show_file_uploader:
    with st.container():
        st.markdown("### 📎 选择要上传的文件")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            uploaded_file = st.file_uploader(
                "选择文件",
                type=['docx', 'pdf', 'xlsx', 'xls', 'txt'],
                key="popup_file_upload",
                help="支持 Word、PDF、Excel、文本文件"
            )

            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ 确认", use_container_width=True, type="primary", key="confirm_upload"):
                    if uploaded_file:
                        # 修复：正确存储文件对象和文件名
                        st.session_state.uploaded_file_for_chat = uploaded_file
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.success(f"✅ 已选择文件: {uploaded_file.name}")
                    st.session_state.show_file_uploader = False
                    st.rerun()

            with col_cancel:
                if st.button("❌ 取消", use_container_width=True, key="cancel_upload"):
                    st.session_state.show_file_uploader = False
                    st.rerun()

# 显示当前选择的文件（在输入框下方）
if st.session_state.uploaded_file_for_chat is not None and not st.session_state.show_file_uploader:
    col_file_info, col_remove = st.columns([4, 1])

    with col_file_info:
        # 修复：安全获取文件名进行显示
        display_name = st.session_state.uploaded_file_name or "未知文件"
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #e8f5e8 0%, #c8e6c9 100%); 
                    color: #2e7d32; padding: 8px 15px; border-radius: 8px; 
                    margin: 5px 0; font-size: 14px; display: flex; align-items: center;">
            📎 <strong>{display_name}</strong>
        </div>
        """, unsafe_allow_html=True)

    with col_remove:
        if st.button("🗑️", help="移除文件", key="remove_file"):
            # 清理文件相关状态
            st.session_state.uploaded_file_for_chat = None
            st.session_state.uploaded_file_name = None

            # 清理输入相关状态，防止冲突
            if "last_processed_input" in st.session_state:
                st.session_state.last_processed_input = ""

            st.success("✅ 文件已成功删除")
            st.rerun()

# 修复：更新后续使用文件的代码部分
uploaded_file = st.session_state.uploaded_file_for_chat

# 处理文件上传
current_file = None
file_content_for_ai = ""

if uploaded_file is not None:
    # 修复：安全的文件处理逻辑
    try:
        # 检查是否需要重新处理文件
        should_process = True
        if st.session_state.uploaded_file_name:
            # 如果文件名相同，说明文件已经处理过了
            if hasattr(uploaded_file, 'name') and uploaded_file.name == st.session_state.uploaded_file_name:
                should_process = False

        if should_process:
            with st.spinner("🔍 正在处理文件..."):
                from file_processor import FileProcessor

                processor = FileProcessor()
                result = processor.process_file(uploaded_file)

                if result['success']:
                    current_file = {
                        'name': result['file_name'],
                        'content': result['content'],
                        'summary': result['summary'],
                        'file_type': result['file_type']
                    }

                    # 更新文件状态
                    st.session_state.uploaded_file_for_chat = uploaded_file
                    st.session_state.uploaded_file_name = result['file_name']

                    # 显示文件上传成功提示
                    st.success(f"✅ 文件 '{result['file_name']}' 已上传，请输入您的问题")

                    # 准备文件内容用于AI分析
                    file_content_for_ai = f"""
文件信息：
- 文件名：{result['file_name']}
- 文件类型：{result['file_type']}
- 文件摘要：{result['summary']}

文件内容：
{result['content'][:2000]}{'...(内容较长，已截取前2000字符)' if len(result['content']) > 2000 else ''}
"""
                else:
                    st.error(f"❌ 文件处理失败：{result['error']}")
        else:
            # 文件已经处理过了，直接使用
            file_name = st.session_state.uploaded_file_name
            st.info(f"📎 文件 '{file_name}' 已准备就绪，请输入您的问题")

    except Exception as e:
        st.error(f"❌ 文件处理出现错误：{str(e)}")
        # 清理错误状态
        st.session_state.uploaded_file_for_chat = None
        st.session_state.uploaded_file_name = None

# 🔧 修复后的消息处理逻辑
current_input = user_input.strip() if user_input else ""

# 简化消息发送判断逻辑
should_send_message = (
    current_input and  # 有输入内容
    send_clicked and   # 点击了发送按钮
    current_input != st.session_state.get("last_processed_input", "")  # 避免重复发送
)

# 处理新消息
if should_send_message:
    # 记录这次处理的输入
    st.session_state.last_processed_input = current_input

    # 获取当前文件状态
    uploaded_file = st.session_state.uploaded_file_for_chat

    # 初始化变量，确保在所有分支中都有定义
    full_user_message = current_input
    display_message = current_input
    file_content_for_ai = ""

    # 处理文件相关逻辑
    if uploaded_file is not None:
        file_name = st.session_state.uploaded_file_name or "未知文件"
        display_message = f"📎 {file_name}\n\n{current_input}"
        full_user_message = f"{current_input}\n\n[用户同时上传了文件: {file_name}]"

        # 重新处理文件以获取内容
        try:
            from file_processor import FileProcessor

            processor = FileProcessor()
            result = processor.process_file(uploaded_file)
            if result['success']:
                file_content_for_ai = f"""
文件信息：
- 文件名：{result['file_name']}
- 文件类型：{result['file_type']}
- 文件摘要：{result['summary']}

文件内容：
{result['content'][:2000]}{'...(内容较长，已截取前2000字符)' if len(result['content']) > 2000 else ''}
"""
        except Exception as e:
            st.warning(f"⚠️ 重新处理文件时出现问题：{str(e)}")
            file_content_for_ai = f"[文件: {file_name} - 处理出现问题]"

    # 添加用户消息到聊天记录
    st.session_state.messages.append({
        "role": "user",
        "content": display_message
    })

    # 处理AI响应
    with st.spinner("🤖 AI正在思考中..."):
        try:
            # 获取系统prompt并加入文件上下文
            if st.session_state.mode == "学业规划":
                from prompts import ACADEMIC_PROMPT

                system_prompt = ACADEMIC_PROMPT.format(
                    grade=st.session_state.user_grade,
                    major=st.session_state.user_major if st.session_state.user_major else "通用专业",
                    question=full_user_message,  # 现在这个变量在所有分支中都有定义
                    file_context=file_content_for_ai
                )
            else:
                from prompts import MENTAL_HEALTH_PROMPT

                system_prompt = MENTAL_HEALTH_PROMPT.format(
                    situation=full_user_message,  # 现在这个变量在所有分支中都有定义
                    file_context=file_content_for_ai
                )

            # 调用AI
            response = ai_client.chat(system_prompt, full_user_message)

            # 如果有文件，在回复中添加文件分析标识
            if uploaded_file is not None:
                file_name = st.session_state.uploaded_file_name or "未知文件"
                response = f"💡 *基于您上传的文件 '{file_name}' 进行分析*\n\n{response}"

            # 添加AI响应到聊天记录
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            # 保存到数据库
            db.save_message(st.session_state.user_id, st.session_state.mode, "user", display_message)
            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant", response)

            # 强制清空输入框：通过重新设置key来重置组件
            if "input_reset_counter" not in st.session_state:
                st.session_state.input_reset_counter = 0
            st.session_state.input_reset_counter += 1

            # 重新运行页面
            st.rerun()

        except Exception as e:
            st.error(f"处理消息时出现错误：{str(e)}")
            # 如果出错，移除已添加的用户消息
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

# 显示文件上传提示 - 修复文件名显示
if uploaded_file is not None and current_file:
    file_name = st.session_state.uploaded_file_name or "当前文件"
    st.info(f"💡 文件 '{file_name}' 已准备就绪！请在上方输入框中描述您希望AI如何分析这个文件，然后点击发送。")

# 🔻 底部信息
st.divider()
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.markdown("💡 **智能助手**")
    st.caption("基于先进AI技术")

with col_info2:
    st.markdown("🔐 **隐私保护**")
    st.caption("您的数据安全可靠")

with col_info3:
    st.markdown("🎯 **个性化服务**")
    st.caption("针对性建议和指导")

st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 10px;">
    💝 感谢使用AI校园助手，祝您学习进步，身心健康！
</div>
""", unsafe_allow_html=True)