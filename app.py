import streamlit as st
import sqlite3
from datetime import datetime
import os
from ai_client import QianfanChat
from database import Database
from prompts import ACADEMIC_PROMPT, MENTAL_HEALTH_PROMPT

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

# ✅ 立即初始化session state（移到最前面）
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
ai_client = QianfanChat()


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

    # 🔧 修复：用户信息输入，绑定到session state
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

    # 🔧 修复的设置菜单
    st.divider()
    st.markdown("### ⚙️ 设置选项")

    with st.expander("🔧 系统设置"):
        # 🎨 修复的主题设置
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
                st.success("💾 数据导出功能开发中...")

        with col_data2:
            if st.button("🗑️ 清空数据", use_container_width=True, key="clear_data_btn"):
                st.session_state.messages = []
                st.success("✅ 对话数据已清空")

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
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("📅 周计划", use_container_width=True):
                    with st.spinner("🤖 AI正在为您生成周计划..."):
                        plan = ai_client.chat(
                            f"你是一个专业的学业规划师。请为{st.session_state.user_grade}{st.session_state.user_major}专业的学生生成一份详细的周学习计划，使用markdown格式，包含具体的时间安排、学习目标和注意事项。",
                            f"请为我生成本周学习计划"
                        )

                    st.markdown("#### 📅 本周学习计划")
                    # ✅ 使用markdown容器而不是text_area
                    with st.container():
                        st.markdown(f"""
                        <div class="generated-content">
                        {plan.replace('**', '<strong>').replace('**', '</strong>').replace('*', '•')}
                        </div>
                        """, unsafe_allow_html=True)

            with col_btn2:
                if st.button("💡 学习方法", use_container_width=True):
                    with st.spinner("🤖 AI正在为您推荐学习方法..."):
                        methods = ai_client.chat(
                            f"你是一个学习方法专家。请为{st.session_state.user_major}专业的{st.session_state.user_grade}学生推荐高效的学习方法，使用markdown格式输出。",
                            f"推荐适合{st.session_state.user_major}专业的学习方法"
                        )

                    st.markdown("#### 💡 学习方法推荐")
                    # ✅ 使用markdown渲染
                    st.markdown(methods)

        # 学习资源
        with st.expander("📚 学习资源"):
            st.markdown("""
            **推荐资源：**
            - 📖 在线课程平台
            - 📝 学术论文数据库  
            - 🎥 教学视频
            - 👥 学习社群
            """)

    else:  # 心理健康模式
        # 心情记录
        with st.expander("😊 心情记录", expanded=True):
            mood = st.select_slider(
                "今天的心情如何？",
                options=["😞 很差", "😕 不太好", "😐 一般", "🙂 不错", "😄 很好"],
                help="记录您的心情有助于了解情绪变化"
            )

            if st.button("💾 记录心情", use_container_width=True):
                db.save_mood(st.session_state.user_id, mood)
                st.markdown("""
                <div class="success-message">
                    ✅ 心情已记录！保持关注自己的情绪变化哦~
                </div>
                """, unsafe_allow_html=True)

        # 放松技巧 - 完整优化版本
        with st.expander("🧘 放松技巧"):
            # 初始化呼吸练习相关的状态
            if "breathing_panel_active" not in st.session_state:
                st.session_state.breathing_panel_active = False
            if "breathing_exercise_active" not in st.session_state:
                st.session_state.breathing_exercise_active = False
            if "show_video" not in st.session_state:
                st.session_state.show_video = False

            st.markdown("""
            <style>
            /* 呼吸练习容器 - 主要布局样式 */
            .breathing-exercise-container {
                background: rgba(255, 255, 255, 0.98);
                padding: 2rem;
                border-radius: 20px;
                margin: 1.5rem 0;
                text-align: center;
                box-shadow: 
                    0 8px 32px rgba(0, 0, 0, 0.1),
                    0 2px 8px rgba(0, 0, 0, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                position: relative;
                overflow: hidden;
            }

            /* 呼吸圆圈 - 主动画元素 */
            .breathing-circle {
                width: 160px;
                height: 160px;
                border-radius: 50%;
                margin: 2rem auto;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 2rem;
                font-weight: 700;
                position: relative;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                animation: breathingCycle 19s cubic-bezier(0.4, 0, 0.6, 1) infinite;
                transform-origin: center center;
            }

            /* 优化的呼吸动画关键帧 */
            @keyframes breathingCycle {
                /* 初始状态 - 吸气准备 */
                0% { 
                    transform: scale(0.75);
                    background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 50%, #81C784 100%);
                    box-shadow: 0 4px 20px rgba(76, 175, 80, 0.4);
                }

                /* 吸气阶段 - 4秒 (0-21%) */
                10% {
                    transform: scale(0.85);
                    background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 50%, #81C784 100%);
                }
                21% { 
                    transform: scale(1.3);
                    background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 50%, #81C784 100%);
                    box-shadow: 0 8px 32px rgba(76, 175, 80, 0.6);
                }

                /* 屏息阶段 - 7秒 (21-58%) */
                22% {
                    background: linear-gradient(135deg, #FF9800 0%, #FFA726 50%, #FFB74D 100%);
                    box-shadow: 0 8px 32px rgba(255, 152, 0, 0.6);
                }
                57% { 
                    transform: scale(1.3);
                    background: linear-gradient(135deg, #FF9800 0%, #FFA726 50%, #FFB74D 100%);
                    box-shadow: 0 8px 32px rgba(255, 152, 0, 0.6);
                }

                /* 呼气阶段 - 8秒 (58-100%) */
                58% {
                    background: linear-gradient(135deg, #2196F3 0%, #42A5F5 50%, #64B5F6 100%);
                    box-shadow: 0 8px 32px rgba(33, 150, 243, 0.6);
                }
                90% {
                    transform: scale(0.85);
                    background: linear-gradient(135deg, #2196F3 0%, #42A5F5 50%, #64B5F6 100%);
                }
                100% { 
                    transform: scale(0.75);
                    background: linear-gradient(135deg, #2196F3 0%, #42A5F5 50%, #64B5F6 100%);
                    box-shadow: 0 4px 20px rgba(33, 150, 243, 0.4);
                }
            }

            /* 文字指导容器 */
            .breathing-text-container {
                position: relative;
                height: 3rem;
                margin: 1.5rem 0;
                font-size: 1.25rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            /* 阶段文字样式 */
            .phase-text {
                position: absolute;
                width: 100%;
                text-align: center;
                opacity: 0;
                transition: all 0.3s ease;
                font-family: 'SF Pro Display', 'Microsoft YaHei', sans-serif;
                letter-spacing: 0.5px;
            }

            /* 吸气文字 */
            .inhale-phase {
                color: #2E7D32;
                animation: inhalePhaseDisplay 19s infinite;
            }

            /* 屏息文字 */
            .hold-phase {
                color: #E65100;
                animation: holdPhaseDisplay 19s infinite;
            }

            /* 呼气文字 */
            .exhale-phase {
                color: #1565C0;
                animation: exhalePhaseDisplay 19s infinite;
            }

            /* 修复的文字动画关键帧 */
            @keyframes inhalePhaseDisplay {
                0%, 21% { 
                    opacity: 1; 
                    transform: translateY(0) scale(1);
                }
                22%, 100% { 
                    opacity: 0; 
                    transform: translateY(-10px) scale(0.9);
                }
            }

            @keyframes holdPhaseDisplay {
                0%, 21% { opacity: 0; }
                22%, 57% { 
                    opacity: 1; 
                    transform: translateY(0) scale(1);
                }
                58%, 100% { 
                    opacity: 0; 
                    transform: translateY(-10px) scale(0.9);
                }
            }

            @keyframes exhalePhaseDisplay {
                0%, 57% { opacity: 0; }
                58%, 99% { 
                    opacity: 1; 
                    transform: translateY(0) scale(1);
                }
                100% { 
                    opacity: 0; 
                    transform: translateY(10px) scale(0.9);
                }
            }

            /* 进度指示器 */
            .breathing-progress {
                margin: 1.5rem 0;
                color: #666;
                font-size: 0.9rem;
                opacity: 0.8;
            }

            /* 辅助元素样式 */
            .breathing-instruction-card {
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                border: 1px solid rgba(102, 126, 234, 0.2);
                border-radius: 15px;
                padding: 1.5rem;
                margin: 1rem 0;
                backdrop-filter: blur(10px);
            }

            .breathing-step-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }

            .breathing-step-card {
                background: white;
                padding: 1rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
            }

            .breathing-step-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }

            /* 响应式设计 */
            @media (max-width: 768px) {
                .breathing-circle {
                    width: 120px;
                    height: 120px;
                    font-size: 1.5rem;
                }

                .breathing-text-container {
                    font-size: 1rem;
                    height: 2.5rem;
                }

                .breathing-exercise-container {
                    padding: 1.5rem;
                    margin: 1rem 0;
                }
            }
            </style>
            """, unsafe_allow_html=True)

            # 呼吸练习激活按钮
            if st.button("🌬️ 开始呼吸练习", use_container_width=True, type="primary"):
                st.session_state.breathing_panel_active = True
                st.session_state.breathing_exercise_active = False
                st.session_state.show_video = False
                st.rerun()

            # 呼吸练习面板渲染
            if st.session_state.breathing_panel_active:
                # 练习说明卡片
                st.markdown("""
                <div class="breathing-instruction-card">
                    <h4 style="color: #667eea; margin: 0 0 1rem 0; font-size: 1.25rem;">🍃 4-7-8呼吸法指导</h4>
                    <p style="margin: 0.5rem 0; color: #555; line-height: 1.6;">
                        这是一种科学验证的放松技巧，通过调节呼吸节奏来激活副交感神经系统，
                        有效缓解压力、焦虑，并改善睡眠质量。
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # 练习步骤说明
                st.markdown("""
                <div class="breathing-step-grid">
                    <div class="breathing-step-card" style="border-top: 3px solid #4CAF50;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🌱</div>
                        <div style="font-weight: 600; color: #4CAF50; margin-bottom: 0.25rem;">准备</div>
                        <div style="font-size: 0.8rem; color: #666;">舒适坐姿</div>
                    </div>
                    <div class="breathing-step-card" style="border-top: 3px solid #4CAF50;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💨</div>
                        <div style="font-weight: 600; color: #4CAF50; margin-bottom: 0.25rem;">吸气</div>
                        <div style="font-size: 0.8rem; color: #666;">4 秒</div>
                    </div>
                    <div class="breathing-step-card" style="border-top: 3px solid #FF9800;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⏸️</div>
                        <div style="font-weight: 600; color: #FF9800; margin-bottom: 0.25rem;">屏息</div>
                        <div style="font-size: 0.8rem; color: #666;">7 秒</div>
                    </div>
                    <div class="breathing-step-card" style="border-top: 3px solid #2196F3;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💨</div>
                        <div style="font-weight: 600; color: #2196F3; margin-bottom: 0.25rem;">呼气</div>
                        <div style="font-size: 0.8rem; color: #666;">8 秒</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 控制按钮区域
                if st.session_state.show_video:
                    # 显示视频播放界面
                    st.markdown("#### 📺 呼吸练习指导视频")

                    video_path = "breath.mp4"

                    try:
                        import os

                        if os.path.exists(video_path):
                            st.video(video_path)
                        else:
                            st.warning("⚠️ 视频文件未找到，请检查文件路径：" + video_path)
                            st.info("💡 请将视频文件放在项目根目录下，或修改 video_path 变量为正确路径")

                    except Exception as e:
                        st.error(f"❌ 视频播放出错：{str(e)}")

                    # 返回按钮
                    if st.button("🔙 返回练习选项", use_container_width=True, key="back_from_video"):
                        st.session_state.show_video = False
                        st.rerun()

                elif not st.session_state.breathing_exercise_active:
                    # 显示开始练习和视频按钮
                    col_start, col_video = st.columns(2)
                    with col_start:
                        if st.button("⏰ 开始引导练习", use_container_width=True, key="start_breathing_guide",
                                     type="primary"):
                            st.session_state.breathing_exercise_active = True
                            st.rerun()
                    with col_video:
                        if st.button("📺 观看指导视频", use_container_width=True, key="show_video_btn"):
                            st.session_state.show_video = True
                            st.rerun()
                else:
                    # 显示活跃的呼吸练习界面
                    # 练习状态标题
                    st.markdown("""
                    <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                        <h3 style="color: white; margin: 0; font-size: 1.5rem;">🧘‍♀️ 正在进行呼吸练习</h3>
                        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1rem;">
                            跟随下方动画进行 4-7-8 呼吸法，让身心得到深度放松
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # 主动画区域
                    st.markdown("""
                    <div class="breathing-exercise-container">
                        <div class="breathing-circle">🫁</div>

                        <div class="breathing-text-container">
                            <div class="phase-text inhale-phase">💨 鼻子缓慢吸气 4 秒</div>
                            <div class="phase-text hold-phase">⏸️ 轻柔保持呼吸 7 秒</div>
                            <div class="phase-text exhale-phase">💨 嘴巴慢慢呼气 8 秒</div>
                        </div>

                        <div class="breathing-progress">
                            完整周期：19 秒 | 绿色扩大时吸气，橙色保持时屏息，蓝色缩小时呼气
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 练习指导和建议
                    st.markdown("""
                    <div class="breathing-instruction-card">
                        <h5 style="color: #667eea; margin: 0 0 1rem 0;">🎵 练习要点</h5>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                            <div>
                                <div style="font-weight: 600; color: #4CAF50; margin-bottom: 0.5rem;">🌿 呼吸技巧</div>
                                <ul style="margin: 0; padding-left: 1rem; color: #666; font-size: 0.9rem; line-height: 1.5;">
                                    <li>鼻子吸气，嘴巴呼气</li>
                                    <li>保持自然舒适的节奏</li>
                                    <li>专注于呼吸的感觉</li>
                                </ul>
                            </div>
                            <div>
                                <div style="font-weight: 600; color: #FF9800; margin-bottom: 0.5rem;">🧘 身体姿态</div>
                                <ul style="margin: 0; padding-left: 1rem; color: #666; font-size: 0.9rem; line-height: 1.5;">
                                    <li>脊背自然挺直</li>
                                    <li>肩膀放松下沉</li>
                                    <li>双脚平放地面</li>
                                </ul>
                            </div>
                            <div>
                                <div style="font-weight: 600; color: #2196F3; margin-bottom: 0.5rem;">💭 意识专注</div>
                                <ul style="margin: 0; padding-left: 1rem; color: #666; font-size: 0.9rem; line-height: 1.5;">
                                    <li>观察呼吸的自然流动</li>
                                    <li>接纳当下的感受</li>
                                    <li>温和地回到呼吸上</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 完成练习按钮
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

            # 正念冥想按钮
            if st.button("💭 正念冥想", use_container_width=True):
                # 创建冥想指导的交互式界面
                st.markdown("""
                <div class="info-card">
                <h4>🧘 5分钟正念冥想指导</h4>
                <div style="background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <h5 style="margin: 0; color: white;">🎯 冥想准备</h5>
                </div>
                </div>
                """, unsafe_allow_html=True)

                # 使用全宽布局显示冥想步骤
                meditation_steps = [
                    ("🪑 舒适坐姿", "找一个舒适的坐姿，脊背自然挺直，双脚平放地面"),
                    ("👁️ 轻闭双眼", "轻闭双眼，或轻柔地凝视前方某一点"),
                    ("🫁 专注呼吸", "将注意力温和地集中在自然呼吸的感觉上"),
                    ("🧠 观察思绪", "观察思绪的来来去去，不做任何评判或抗拒"),
                    ("🎯 温和回归", "当发现走神时，温柔地将注意力带回到呼吸上")
                ]

                for i, (title, desc) in enumerate(meditation_steps):
                    color = "#4facfe" if i % 2 == 0 else "#00f2fe"
                    st.markdown(f"""
                    <div style="background: white; margin: 12px 0; padding: 18px; border-radius: 12px; 
                                box-shadow: 0 3px 6px rgba(0,0,0,0.08); border-left: 4px solid {color};">
                        <h5 style="color: {color}; margin: 0; font-size: 18px;">{title}</h5>
                        <p style="color: #666; margin: 8px 0; font-size: 15px; line-height: 1.6;">{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # 心理健康资源
        with st.expander("📞 求助资源"):
            st.markdown("""
            **如需专业帮助：**
            - 🏥 校医院心理咨询
            - 📞 心理援助热线
            - 👥 心理健康社团
            - 💊 专业心理治疗
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
                    major=st.session_state.user_major if st.session_state.user_major else "机器人工程",
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