import streamlit as st
import requests
import uuid
import time
from datetime import datetime

# 后端API地址
BACKEND_URL = "http://localhost:8000"

# 自定义CSS样式（完全保留原始样式）
st.markdown("""
<style>
/* 用户消息容器 - 右侧 */
.user-message-container {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
    align-items: flex-start;
}
/* AI消息容器 - 左侧 */
.ai-message-container {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 15px;
    align-items: flex-start;
}
/* 用户消息气泡 */
.user-message {
    background-color: #f0f7ff;
    border-radius: 15px 15px 0 15px;
    padding: 12px 15px;
    max-width: 100%;
    border: 1px solid #d0e0ff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    margin-left: 8px;
}
/* AI消息气泡 */
.ai-message {
    background-color: #f8f9fa;
    border-radius: 15px 15px 15px 0;
    padding: 12px 15px;
    max-width: 100%;
    border: 1px solid #e0e0e0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    margin-left: 8px;
}
.message-timestamp {
    font-size: 0.75rem;
    color: #777;
    margin-top: 4px;
    text-align: right;
}
/* 头像样式 */
.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
}
.user-avatar {
    background-color: #e0e0ff;
}
.ai-avatar {
    background-color: #d1ecff;
}
/* 隐藏Streamlit默认的消息容器 */
[data-testid="stChatMessage"] {
    display: none !important;
}
/* 状态标题样式 */
.status-title {
    font-weight: bold;
    margin-bottom: 5px;
    color: #333;
}
.thinking {
    color: #ff6b00;
}
.completed {
    color: #28a745;
}
.waiting-indicator {
    display: inline-block;
    animation: ellipsis 1.5s infinite;
}
@keyframes ellipsis {
    0% { content: '.'; }
    33% { content: '..'; }
    66% { content: '...'; }
    100% { content: '.'; }
}
</style>
""", unsafe_allow_html=True)


# 初始化会话
def init_session():
    if "session_id" not in st.session_state:
        session_id = str(uuid.uuid4())
        st.session_state.session_id = session_id

        # 初始化后端会话
        response = requests.post(
            f"{BACKEND_URL}/init_session",
            json={"session_id": session_id}
        )

        if response.status_code == 200:
            st.toast('会话已初始化', icon='✅')
        else:
            st.error("会话初始化失败")


# 获取对话历史
def get_conversation():
    session_id = st.session_state.session_id
    response = requests.get(f"{BACKEND_URL}/get_conversation/{session_id}")
    if response.status_code == 200:
        return response.json()
    return []


# 获取会话状态
def get_session_state():
    session_id = st.session_state.session_id
    response = requests.get(f"{BACKEND_URL}/get_session_state/{session_id}")
    if response.status_code == 200:
        return response.json()
    return {"is_responding": False, "prompt_to_process": None}


# 添加用户消息
def add_user_message(prompt):
    session_id = st.session_state.session_id
    response = requests.post(
        f"{BACKEND_URL}/add_user_message",
        json={"session_id": session_id, "content_text": prompt}
    )
    return response.status_code == 200


# 处理AI响应
def process_ai_response():
    session_id = st.session_state.session_id
    response = requests.post(
        f"{BACKEND_URL}/process_ai_response",
        json={"session_id": session_id}
    )
    return response


# 主应用
def main():
    st.set_page_config(
        page_title="文华财经AI智能客服助手",
        page_icon=":speech_balloon:",
        layout="wide"
    )

    init_session()

    st.title("文华财经AI智能客服助手")
    st.caption("基于文华财经大模型的AI智能客服系统")

    # 创建对话区域容器
    chat_container = st.container(border=True)

    # 显示对话历史
    with chat_container:
        conversation = get_conversation()

        # 初始问候语
        if not conversation:
            st.markdown("""
                <div class="ai-message-container">
                    <div class="avatar ai-avatar">🤖</div>
                    <div class="ai-message">
                        您好！我是文华财经的客服助手小文，很高兴为您服务。
                        <div class="message-timestamp">{} | AI助手</div>
                    </div>
                </div>
            """.format(datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)

        # 显示对话历史
        for msg in conversation:
            if msg["sender"] == "ai":
                st.markdown(f"""
                    <div class="ai-message-container">
                        <div class="avatar ai-avatar">🤖</div>
                        <div class="ai-message">
                            <div class="status-title completed">【已深度思考】</div>
                            {msg["message"]}
                            <div class="message-timestamp">{msg['timestamp']} | AI助手</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            elif msg["sender"] == "user":
                st.markdown(f"""
                    <div class="user-message-container">
                        <div class="user-message">
                            {msg["message"]}
                            <div class="message-timestamp">{msg['timestamp']} | 您</div>
                        </div>
                        <div class="avatar user-avatar">👤</div>
                    </div>
                """, unsafe_allow_html=True)

        # 滚动到底部
        st.markdown('<div id="endofchat"></div>', unsafe_allow_html=True)
        st.markdown("""
            <script>
                document.getElementById("endofchat").scrollIntoView({ behavior: "smooth" });
            </script>
        """, unsafe_allow_html=True)

    st.divider()

    # 获取会话状态
    session_state = get_session_state()

    # 用户输入区域
    prompt = st.chat_input(
        "请输入您的问题...",
        key="user_input",
        disabled=session_state["is_responding"]
    )

    if prompt and not session_state["is_responding"]:
        # 添加用户消息到后端
        if add_user_message(prompt):
            st.rerun()

    # 处理AI响应
    if session_state["is_responding"] and session_state["prompt_to_process"]:
        # 显示AI思考中状态
        with chat_container:
            timestamp = datetime.now().strftime("%H:%M:%S")
            ai_response_placeholder = st.empty()
            response_html = """
                <div class="ai-message-container">
                    <div class="avatar ai-avatar">🤖</div>
                    <div class="ai-message">
                        <div class="status-title thinking">【深度思考中】</div>
                        <div class="message-content">{}</div>
                        <div class="message-timestamp">{} | AI助手</div>
                    </div>
                </div>
            """
            ai_response_placeholder.markdown(
                response_html.format(
                    "<span class='waiting-indicator'>...</span>",
                    timestamp
                ),
                unsafe_allow_html=True
            )

        # 处理AI响应
        response = process_ai_response()

        # 获取并显示AI回复
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                # 获取完整的对话历史（包含新回复）
                conversation = get_conversation()
                ai_message = conversation[-1]["message"]

                # 模拟流式输出效果
                display_message = ""
                for char in ai_message:
                    display_message += char
                    time.sleep(0.02)  # 控制输出速度
                    ai_response_placeholder.markdown(
                        response_html.format(
                            display_message.replace('\n', '<br>'),
                            timestamp
                        ),
                        unsafe_allow_html=True
                    )

                # 更新为最终状态
                final_html = response_html.format(
                    ai_message.replace('\n', '<br>'),
                    timestamp
                ).replace("thinking", "completed").replace("【深度思考中】", "【已深度思考】")
                ai_response_placeholder.markdown(final_html, unsafe_allow_html=True)

                # 滚动到底部
                st.markdown('<div id="endofchat_after_response"></div>', unsafe_allow_html=True)
                st.markdown("""
                    <script>
                        document.getElementById("endofchat_after_response").scrollIntoView({ behavior: "smooth" });
                    </script>
                """, unsafe_allow_html=True)

                # 显示完成提示
                st.toast('小文思考完成啦！希望您满意！', icon='🤖')
        else:
            st.error("处理AI响应时出错")

        st.rerun()

    # 显示状态提示
    if session_state["is_responding"]:
        st.status("AI 正在生成回复，请在回复完成后再提新问题...", state="running")


if __name__ == "__main__":
    main()