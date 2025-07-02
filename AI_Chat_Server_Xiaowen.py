import streamlit as st
import time
import json
import requests
from datetime import datetime

# 修改后的API类
class WenHuaAPI:
    def __init__(self):
        self.base_url = "https://swarm.wenhua.com.cn/aiservice/api/ShiXi/GetContent"
        self.headers = {
            "Content-Type": "application/json"
        }

    def generate_response(self, content_text):
        payload = {
            "content": content_text
        }
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload,
            stream=True,
            timeout=30
        )
        if response.status_code != 200:
            error_msg = f"API错误: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text[:200]}"
            raise Exception(error_msg)
        return response


# 初始化session state
def init_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "api" not in st.session_state:
        st.session_state.api = WenHuaAPI()
    if "is_responding" not in st.session_state:
        st.session_state.is_responding = False
    if "prompt_to_process" not in st.session_state:
        st.session_state.prompt_to_process = None


# 添加消息到对话历史
def add_message(sender, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.conversation.append({
        "sender": sender,
        "message": message,
        "timestamp": timestamp
    })


# 主应用
def main():
    st.set_page_config(
        page_title="文华财经AI智能客服助手",
        page_icon=":speech_balloon:",
        layout="wide"
    )

    init_session_state()

    # 自定义CSS样式
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
    /* 聊天容器样式 */
    .chat-container {
        height: 500px;
        overflow-y: auto;
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

    st.title("文华财经AI智能客服助手")
    st.caption("基于文华财经大模型的AI智能客服系统")

    # 创建对话区域容器
    chat_container = st.container(border=True)

    with chat_container:
        if not st.session_state.conversation:
            st.markdown("""
                <div class="ai-message-container">
                    <div class="avatar ai-avatar">🤖</div>
                    <div class="ai-message">
                        您好！我是文华财经的客服助手小文，很高兴为您服务。
                        <div class="message-timestamp">{} | AI助手</div>
                    </div>
                </div>
            """.format(datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)

        for msg in st.session_state.conversation:
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

        # 插入滚动标记
        st.markdown('<div id="endofchat"></div>', unsafe_allow_html=True)
        st.markdown("""
            <script>
                document.getElementById("endofchat").scrollIntoView({ behavior: "smooth" });
            </script>
        """, unsafe_allow_html=True)

    st.divider()

    # 用户输入区域
    prompt = st.chat_input("请输入您的问题...", key="user_input",
                           disabled=st.session_state.is_responding)

    if prompt:
        add_message("user", prompt)
        st.session_state.prompt_to_process = prompt
        st.session_state.is_responding = True
        st.toast('小文已收到您的问题，正在思考中...', icon='🤖')
        st.rerun()

    if st.session_state.is_responding and st.session_state.prompt_to_process:
        # 构建上下文内容
        context_content = ""
        for msg in st.session_state.conversation:
            if msg["sender"] == "user":
                context_content += f"用户: {msg['message']}\n"
            elif msg["sender"] == "ai":
                context_content += f"AI: {msg['message']}\n"

        # 添加系统提示
        system_prompt = (
            "你是文华财经公司的客服助手小文，请以专业、友好的态度回答用户问题。"
            "回答要简洁明了，专注于提供市场信息、数据分析和操作指导。"
            "如果用户咨询购买问题，请明确提供400客服电话方便用户转人工服务。"
            "保持上下文逻辑关联，确保回答准确、专业。"
        )
        context_content = f"系统设定: {system_prompt}\n{context_content}"

        try:
            response_stream = st.session_state.api.generate_response(context_content)
            full_response = ""

            with chat_container:
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
                        datetime.now().strftime('%H:%M:%S')
                    ),
                    unsafe_allow_html=True
                )

                for line in response_stream.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    token = delta.get("content", "")
                                    if token is not None:
                                        full_response += token
                                        display_response = full_response
                                        if not token.endswith(('\n', '。', '！', '？', '；')):
                                            display_response += "…"
                                        ai_response_placeholder.markdown(
                                            response_html.format(
                                                display_response.replace('\n', '<br>'),
                                                datetime.now().strftime('%H:%M:%S')
                                            ),
                                            unsafe_allow_html=True
                                        )
                            except json.JSONDecodeError:
                                continue

                final_html = response_html.format(
                    full_response.replace('\n', '<br>'),
                    datetime.now().strftime('%H:%M:%S')
                ).replace("thinking", "completed").replace("【深度思考中】", "【已深度思考】")
                ai_response_placeholder.markdown(final_html, unsafe_allow_html=True)

                st.markdown('<div id="endofchat_after_response"></div>', unsafe_allow_html=True)
                st.markdown("""
                    <script>
                        document.getElementById("endofchat_after_response").scrollIntoView({ behavior: "smooth" });
                    </script>
                """, unsafe_allow_html=True)

            add_message("ai", full_response)
        except Exception as e:
            error_msg = f"抱歉，发生错误: {str(e)}"
            add_message("ai", error_msg)

        st.session_state.is_responding = False
        st.session_state.prompt_to_process = None
        st.rerun()

    # 新增：在输入框下方显示持久的状态提示
    if st.session_state.is_responding:
        st.status("AI 正在生成回复，请在回复完成后再提新问题...", state="running")
    else:
        st.toast('小文思考完成啦！希望您满意！', icon='🤖')


if __name__ == "__main__":
    main()