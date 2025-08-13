import streamlit as st
import os
from ai_client import QianfanChat
from database import Database
from prompts import ACADEMIC_PROMPT, MENTAL_HEALTH_PROMPT
from data_exporter import DataExporter
import time
import base64
from datetime import datetime
import sqlite3
from data_exporter import DataExporter
import pandas as pd
from datetime import datetime

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
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stActionButton {display: none;}
[data-testid="stToolbar"] {display: none;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}
div[data-testid="stToolbar"] {
    visibility: hidden;
    height: 0%;
    position: fixed;
}
div[data-testid="stDecoration"] {
    visibility: hidden;
    height: 0%;
    position: fixed;
}
div[data-testid="stStatusWidget"] {
    visibility: hidden;
    height: 0%;
    position: fixed;
}
</style>
"""
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
# 🎨 新增：主题控制
if "theme" not in st.session_state:
    st.session_state.theme = "紫色渐变"
# 🔧 新增：用户信息存储到session state
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_grade" not in st.session_state:
    st.session_state.user_grade = "大一"
if "user_major" not in st.session_state:
    st.session_state.user_major = ""

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


# 🎨 动态主题CSS函数
def get_theme_css(theme):
    """根据主题返回对应的CSS"""
    theme_configs = {
        "紫色渐变": {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "bg_start": "#f5f7fa",
            "bg_end": "#c3cfe2",
            "sidebar_start": "#f8f9ff",
            "sidebar_end": "#e6e9ff"
        },
        "蓝色渐变": {
            "primary": "#4facfe",
            "secondary": "#00f2fe",
            "bg_start": "#e3f2fd",
            "bg_end": "#bbdefb",
            "sidebar_start": "#e1f5fe",
            "sidebar_end": "#b3e5fc"
        },
        "绿色渐变": {
            "primary": "#56ab2f",
            "secondary": "#a8e6cf",
            "bg_start": "#f1f8e9",
            "bg_end": "#c8e6c9",
            "sidebar_start": "#e8f5e8",
            "sidebar_end": "#c8e6c9"
        }
    }

    config = theme_configs.get(theme, theme_configs["紫色渐变"])

    return f"""
    <style>
        /* 主标题样式 */
        .main-header {{
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, {config['primary']} 0%, {config['secondary']} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            padding: 1rem 0;
        }}

        /* 工具按钮样式 */
        .stButton > button {{
            background: linear-gradient(90deg, {config['primary']} 0%, {config['secondary']} 100%);
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
            background: linear-gradient(90deg, {config['primary']} 0%, {config['secondary']} 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            text-align: center;
            font-weight: 600;
            margin-bottom: 1rem;
        }}

        /* 渐变背景 */
        .stApp {{
            background: linear-gradient(135deg, {config['bg_start']} 0%, {config['bg_end']} 100%) !important;
        }}

        /* 侧边栏美化 */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {config['sidebar_start']} 0%, {config['sidebar_end']} 100%) !important;
        }}

        /* 输入框发送按钮样式 */
        .input-container .stButton > button {{
            background: linear-gradient(90deg, {config['primary']} 0%, {config['secondary']} 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 15px 30px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            height: 53px !important;
        }}

        .input-container .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4) !important;
        }}

        /* 其他样式保持不变 */
        .info-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid {config['primary']};
            margin: 1rem 0;
        }}

        .success-message {{
            background: linear-gradient(90deg, {config['primary']} 0%, {config['secondary']} 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
        }}

        /* 隐藏Streamlit默认元素的样式保持不变 */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stActionButton {{display: none;}}
        [data-testid="stToolbar"] {{display: none;}}
        [data-testid="stDecoration"] {{display: none;}}
        [data-testid="stStatusWidget"] {{display: none;}}
        section[data-testid="stBottom"] {{display: none !important;}}

        /* 输入框样式 */
        .input-container {{
            background: transparent !important;
            margin: 20px 0 !important;
        }}

        .input-container .stTextInput > div > div {{
            background: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid #e1e5e9 !important;
            border-radius: 25px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            backdrop-filter: blur(10px) !important;
        }}

        .input-container .stTextInput input {{
            background: transparent !important;
            border: none !important;
            color: #333 !important;
            font-size: 16px !important;
            padding: 15px 20px !important;
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


# 应用动态主题CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

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
    if grade != st.session_state.user_grade:
        st.session_state.user_grade = grade
    if major != st.session_state.user_major:
        st.session_state.user_major = major

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

    # 更新模式（去掉emoji用于后端处理）
    if "🎯 学业规划" in mode:
        st.session_state.mode = "学业规划"
    else:
        st.session_state.mode = "心理健康"

    # 清空对话
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
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
        # 🎨 主题设置
        new_theme = st.selectbox(
            "🎨 界面主题",
            ["紫色渐变", "蓝色渐变", "绿色渐变"],
            index=["紫色渐变", "蓝色渐变", "绿色渐变"].index(st.session_state.theme),
            help="选择您喜欢的界面主题",
            key="theme_selector"
        )

        # 当主题改变时立即应用
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

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

        # 数据管理
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            if st.button("📁 导出数据", use_container_width=True, key="export_data_btn"):
                with st.spinner("📊 正在生成数据报告..."):
                    try:
                        # 生成Markdown报告
                        markdown_content = data_exporter.generate_markdown_report(st.session_state.user_id)

                        if markdown_content:
                            # 生成文件名
                            user_name = st.session_state.user_name or "未知用户"
                            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"AI校园助手_数据报告_{user_name}_{current_time}.md"

                            # 创建下载按钮
                            st.success("✅ 数据报告生成成功！")

                            # 显示预览
                            with st.expander("📄 报告预览", expanded=False):
                                st.markdown("```markdown")
                                preview_content = markdown_content[:1000] + "..." if len(
                                    markdown_content) > 1000 else markdown_content
                                st.text(preview_content)
                                st.markdown("```")

                            # 提供下载
                            st.download_button(
                                label="📥 下载完整报告",
                                data=markdown_content,
                                file_name=filename,
                                mime="text/markdown",
                                use_container_width=True
                            )

                            # 统计信息
                            lines_count = len(markdown_content.split('\n'))
                            chars_count = len(markdown_content)
                            st.caption(f"📋 报告包含 {lines_count} 行，{chars_count} 个字符")

                        else:
                            st.warning("⚠️ 暂无数据可导出，请先使用AI校园助手进行对话")

                    except Exception as e:
                        st.error(f"❌ 导出失败: {str(e)}")

        with col_data2:
            if st.button("🗑️ 清空数据", use_container_width=True, key="clear_data_btn"):
                # 🔧 修复：移除嵌套的columns，使用简单的垂直布局

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

                    # 🔧 修复：垂直排列确认按钮，而不是使用columns
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
    # 模式指示器
    mode_emoji = "🎯" if st.session_state.mode == "学业规划" else "💚"
    st.markdown(f"""
    <div class="mode-indicator">
        {mode_emoji} {st.session_state.mode}助手
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
            # 欢迎消息
            st.info(f"""
            👋 欢迎使用AI校园助手！

            我是您的{st.session_state.mode}专家，可以帮助您：

            {"📚 制定学习计划 📈 提高学习效率 🎯 规划职业发展" if st.session_state.mode == "学业规划" else "😌 情绪调节 💪 压力管理 🧘 心理健康指导"}

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
                    with st.spinner("🤖 AI正在分析您的情绪..."):
                        try:
                            emotion_prompt = "请作为心理健康顾问，帮助分析用户的情绪状态并提供调节建议。"
                            emotion_content = ai_client.chat(emotion_prompt, "请帮我分析当前的情绪状态并提供调节建议")

                            st.session_state.messages.append({
                                "role": "user",
                                "content": "🌈 请帮我分析当前的情绪状态并提供调节建议"
                            })

                            formatted_emotion = f"## 🌈 情绪分析与建议\n\n{emotion_content}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": formatted_emotion
                            })

                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            "🌈 请帮我分析当前的情绪状态并提供调节建议")
                            db.save_message(st.session_state.user_id, st.session_state.mode, "assistant",
                                            formatted_emotion)

                            st.success("✅ 情绪分析已生成，请查看左侧对话框")
                            st.rerun()

                        except Exception as e:
                            st.error(f"生成情绪分析时出错：{str(e)}")

            with col_support2:
                if st.button("💪 压力管理", use_container_width=True, key="quick_stress"):
                    with st.spinner("🤖 AI正在为您提供压力管理建议..."):
                        try:
                            stress_prompt = "请作为心理健康专家，提供实用的压力管理技巧和建议。"
                            stress_content = ai_client.chat(stress_prompt, "请为我提供有效的压力管理技巧和方法")

                            st.session_state.messages.append({
                                "role": "user",
                                "content": "💪 请为我提供有效的压力管理技巧和方法"
                            })

                            formatted_stress = f"## 💪 压力管理指南\n\n{stress_content}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": formatted_stress
                            })

                            db.save_message(st.session_state.user_id, st.session_state.mode, "user",
                                            "💪 请为我提供有效的压力管理技巧和方法")
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
            st.markdown("""
            **如需专业帮助：**
            - 🏥 校医院心理咨询
            - 📞 心理援助热线：400-161-9995
            - 👥 心理健康社团
            - 💊 专业心理治疗
            - 🌐 在线心理平台：壹心理、简单心理
            """)


# 🔧 修复的消息处理函数
def process_user_message(message_content):
    """处理用户消息的独立函数"""
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": message_content})

    # 获取AI响应
    with st.spinner("🤖 AI正在思考中..."):
        try:
            # 根据模式选择prompt，使用session state中的用户信息
            if st.session_state.mode == "学业规划":
                system_prompt = ACADEMIC_PROMPT.format(
                    grade=st.session_state.user_grade,
                    major=st.session_state.user_major if st.session_state.user_major else "通用专业",
                    question=message_content
                )
            else:
                system_prompt = MENTAL_HEALTH_PROMPT.format(
                    situation=message_content
                )

            # 调用AI
            response = ai_client.chat(system_prompt, message_content)

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

col_input, col_send = st.columns([5, 1])

with col_input:
    # 🔧 修复：使用动态key来强制重置输入框
    input_key = f"main_chat_input_{st.session_state.get('input_reset_counter', 0)}"
    user_input = st.text_input(
        "消息输入",
        placeholder="💬 请输入您的问题... (按Enter发送)",
        key=input_key,
        label_visibility="collapsed"
    )

with col_send:
    send_clicked = st.button("➤ 发送", use_container_width=True, type="primary")

st.markdown('</div>', unsafe_allow_html=True)

# 🔧 完全重新设计的消息处理逻辑
current_input = user_input.strip() if user_input else ""

# 初始化上次处理的输入记录
if "last_processed_input" not in st.session_state:
    st.session_state.last_processed_input = ""

# 检测新消息：输入框有内容 且 (点击发送按钮 或 输入内容与上次不同)
is_new_message = (
        current_input and
        current_input != st.session_state.last_processed_input and
        (send_clicked or current_input != st.session_state.get("previous_input", ""))
)

# 记录当前输入用于下次比较
st.session_state.previous_input = current_input

# 处理新消息
if is_new_message:
    # 记录这次处理的输入
    st.session_state.last_processed_input = current_input

    # 处理消息
    if process_user_message(current_input):
        # 强制清空输入框：通过重新设置key来重置组件
        if "input_reset_counter" not in st.session_state:
            st.session_state.input_reset_counter = 0
        st.session_state.input_reset_counter += 1

        # 清空相关状态
        st.session_state.previous_input = ""

        # 重新运行页面
        st.rerun()

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