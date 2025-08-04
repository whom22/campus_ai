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

    # 用户信息输入
    name = st.text_input("📝 姓名", key="user_name", placeholder="请输入您的姓名")
    grade = st.selectbox("🎯 年级", ["大一", "大二", "大三", "大四", "研究生"], help="选择您当前的年级")
    major = st.text_input("🎓 专业", key="user_major", placeholder="请输入您的专业")

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
            help="选择您喜欢的界面主题"
        )

        # 当主题改变时立即应用
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

        # 其他设置保持不变...
        font_size = st.slider(
            "📝 字体大小",
            min_value=12,
            max_value=20,
            value=16,
            help="调整界面字体大小"
        )

        enable_animation = st.checkbox(
            "✨ 启用动画效果",
            value=True,
            help="开启或关闭界面动画"
        )

        # 字体大小
        font_size = st.slider(
            "📝 字体大小",
            min_value=12,
            max_value=20,
            value=16,
            help="调整界面字体大小"
        )

        # 动画效果
        enable_animation = st.checkbox(
            "✨ 启用动画效果",
            value=True,
            help="开启或关闭界面动画"
        )

        # 数据管理
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            if st.button("📁 导出数据", use_container_width=True):
                st.success("💾 数据导出功能开发中...")

        with col_data2:
            if st.button("🗑️ 清空数据", use_container_width=True):
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
                            f"你是一个专业的学业规划师。请为{grade}{major}专业的学生生成一份详细的周学习计划，使用markdown格式，包含具体的时间安排、学习目标和注意事项。",
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
                            f"你是一个学习方法专家。请为{major}专业的{grade}学生推荐高效的学习方法，使用markdown格式输出。",
                            f"推荐适合{major}专业的学习方法"
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

        # 放松技巧
        with st.expander("🧘 放松技巧"):
            if st.button("🫁 呼吸练习", use_container_width=True):
                st.markdown("""
                <div class="info-card">
                <h4>🫁 4-7-8呼吸法</h4>
                <ol>
                <li><strong>吸气</strong> 4秒 💨</li>
                <li><strong>屏息</strong> 7秒 ⏸️</li>
                <li><strong>呼气</strong> 8秒 💨</li>
                <li><strong>重复</strong> 3-4次 🔄</li>
                </ol>
                <p>💡 这个练习可以帮助你快速放松身心！</p>
                </div>
                """, unsafe_allow_html=True)

            if st.button("💭 正念冥想", use_container_width=True):
                st.markdown("""
                <div class="info-card">
                <h4>💭 5分钟正念练习</h4>
                <ul>
                <li>🪑 找个舒适的坐姿</li>
                <li>👁️ 轻闭双眼，专注呼吸</li>
                <li>🧠 观察思绪，不做判断</li>
                <li>🎯 当走神时，轻柔地回到呼吸</li>
                </ul>
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

# ✅ 美化的聊天输入区域
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# 🔧 输入框清空逻辑处理
if st.session_state.clear_input:
    st.session_state.input_text = ""
    st.session_state.clear_input = False

col_input, col_send = st.columns([5, 1])

with col_input:
    # 🔧 修复：使用session state控制输入框的值
    user_input = st.text_input(
        "消息输入",
        placeholder="💬 请输入您的问题... (按Enter发送)",
        key="main_chat_input",
        value=st.session_state.input_text,  # 绑定到session state
        label_visibility="collapsed"
    )

    # 🔧 实时更新input_text状态
    if user_input != st.session_state.input_text:
        st.session_state.input_text = user_input

with col_send:
    send_clicked = st.button("➤ 发送", use_container_width=True, type="primary")

st.markdown('</div>', unsafe_allow_html=True)


# 🔧 修复的消息处理函数
def process_user_message(message_content):
    """处理用户消息的独立函数"""
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": message_content})

    # 获取AI响应
    with st.spinner("🤖 AI正在思考中..."):
        try:
            # 根据模式选择prompt
            if st.session_state.mode == "学业规划":
                system_prompt = ACADEMIC_PROMPT.format(
                    grade=grade if 'grade' in locals() and grade else "大一",
                    major=major if 'major' in locals() and major else "机器人工程",
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

            # 🔧 关键修复：设置清空标志
            st.session_state.clear_input = True

            return True

        except Exception as e:
            st.error(f"处理消息时出现错误：{str(e)}")
            # 如果出错，移除已添加的用户消息
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
            return False


# 🔧 简化的消息检测和处理逻辑
current_input = user_input.strip() if user_input else ""

# 处理发送按钮点击或Enter键提交
if (send_clicked or (
        current_input and current_input != st.session_state.get("last_processed_input", ""))) and current_input:
    # 防止重复处理同一条消息
    st.session_state.last_processed_input = current_input

    # 处理消息
    if process_user_message(current_input):
        # 消息处理成功，重新运行页面
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