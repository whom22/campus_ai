import streamlit as st
import time
import streamlit.components.v1 as components

# 页面配置
st.set_page_config(
    page_title="呼吸练习",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式
st.markdown("""
<style>
/* 隐藏Streamlit默认元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* 呼吸圆圈动画 */
.breathing-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
}

.breathing-circle {
    width: 200px;
    height: 200px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    transition: all 4s ease-in-out;
    display: flex;
    align-items: center;
    justify-content: center;
}

.breathing-circle.inhale {
    transform: scale(1.3);
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
}

.breathing-circle.hold {
    transform: scale(1.3);
}

.breathing-circle.exhale {
    transform: scale(1);
    box-shadow: 0 10px 40px rgba(102, 126, 234, 0.2);
}

/* 呼吸指示文字 */
.breathing-text {
    font-size: 2.5rem;
    color: #4A90E2;
    text-align: center;
    margin: 30px 0;
    font-weight: 300;
    letter-spacing: 2px;
}

/* 进度条样式 */
.stProgress > div > div > div > div {
    background-color: #667eea;
}

/* 按钮样式 */
.stButton > button {
    background-color: #667eea;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 16px;
    transition: all 0.3s;
}

.stButton > button:hover {
    background-color: #764ba2;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)


# 创建完整的呼吸练习应用
def breathing_exercise_app():
    # 侧边栏设置
    with st.sidebar:
        st.markdown("### ⚙️ 呼吸设置")

        # 呼吸模式选择
        breathing_pattern = st.selectbox(
            "选择呼吸模式",
            options=["4-7-8 放松呼吸", "方形呼吸", "平等呼吸"],
            help="4-7-8适合睡前，方形呼吸适合集中注意力"
        )

        # 练习时长
        duration = st.slider(
            "练习时长（分钟）",
            min_value=1,
            max_value=30,
            value=5,
            step=1
        )

        # 背景音乐
        background_sound = st.selectbox(
            "背景音乐",
            ["无", "海浪声", "雨声", "森林声"]
        )

        # 视觉主题
        theme = st.selectbox(
            "视觉主题",
            ["默认渐变", "海洋蓝", "森林绿", "日落橙"]
        )

        st.markdown("---")
        st.markdown("### 📊 练习统计")
        st.metric("总练习时间", "45分钟")
        st.metric("连续练习天数", "7天")

    # 主界面布局
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        st.markdown(
            """
            <h1 style='text-align: center; color: #667eea; margin-bottom: 40px;'>
                🧘 呼吸练习
            </h1>
            """,
            unsafe_allow_html=True
        )

        # 呼吸可视化容器
        breathing_container = st.empty()
        instruction_text = st.empty()
        progress_bar = st.empty()

        # 控制按钮
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

        with col_btn1:
            start_button = st.button("开始练习", key="start", use_container_width=True)

        with col_btn2:
            pause_button = st.button("暂停", key="pause", use_container_width=True)

        with col_btn3:
            stop_button = st.button("结束", key="stop", use_container_width=True)

        # 视频指导区域
        with st.expander("🎥 查看视频指导"):
            create_responsive_youtube_player("YRPh_GaiL8I")

    # 呼吸练习逻辑
    if start_button:
        # 初始化会话状态
        if 'breathing_active' not in st.session_state:
            st.session_state.breathing_active = True
            st.session_state.cycle_count = 0

        # 呼吸模式时间设置
        patterns = {
            "4-7-8 放松呼吸": {"inhale": 4, "hold": 7, "exhale": 8},
            "方形呼吸": {"inhale": 4, "hold1": 4, "exhale": 4, "hold2": 4},
            "平等呼吸": {"inhale": 4, "exhale": 4}
        }

        pattern = patterns[breathing_pattern]
        total_cycles = duration * 60 // sum(pattern.values())

        # 执行呼吸循环
        for cycle in range(total_cycles):
            if not st.session_state.get('breathing_active', True):
                break

            # 更新进度
            progress = (cycle + 1) / total_cycles
            progress_bar.progress(progress)

            # 吸气阶段
            breathing_container.markdown(
                """
                <div class="breathing-container">
                    <div class="breathing-circle inhale">
                        <span style="color: white; font-size: 24px;">吸气</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            instruction_text.markdown(
                f'<p class="breathing-text">深深吸气 {pattern["inhale"]}秒</p>',
                unsafe_allow_html=True
            )
            time.sleep(pattern["inhale"])

            # 保持阶段（如果有）
            if "hold" in pattern or "hold1" in pattern:
                hold_time = pattern.get("hold", pattern.get("hold1", 0))
                breathing_container.markdown(
                    """
                    <div class="breathing-container">
                        <div class="breathing-circle hold">
                            <span style="color: white; font-size: 24px;">保持</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                instruction_text.markdown(
                    f'<p class="breathing-text">屏住呼吸 {hold_time}秒</p>',
                    unsafe_allow_html=True
                )
                time.sleep(hold_time)

            # 呼气阶段
            breathing_container.markdown(
                """
                <div class="breathing-container">
                    <div class="breathing-circle exhale">
                        <span style="color: white; font-size: 24px;">呼气</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            instruction_text.markdown(
                f'<p class="breathing-text">缓慢呼气 {pattern["exhale"]}秒</p>',
                unsafe_allow_html=True
            )
            time.sleep(pattern["exhale"])

            st.session_state.cycle_count = cycle + 1

    if stop_button:
        st.session_state.breathing_active = False
        st.success(f"练习完成！您完成了 {st.session_state.get('cycle_count', 0)} 个呼吸循环。")
        st.balloons()


# 运行应用
if __name__ == "__main__":
    breathing_exercise_app()