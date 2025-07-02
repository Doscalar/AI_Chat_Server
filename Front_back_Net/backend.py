from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from datetime import datetime
import uvicorn
import json
from typing import Dict, List

app = FastAPI()

# 内存存储会话数据（生产环境应使用数据库）
sessions: Dict[str, dict] = {}


class SessionData(BaseModel):
    conversation: List[dict]
    is_responding: bool
    prompt_to_process: str = None


class MessageRequest(BaseModel):
    session_id: str
    content_text: str


class InitSessionRequest(BaseModel):
    session_id: str


class WenHuaAPI:
    def __init__(self):
        self.base_url = "Wenhua API"
        self.headers = {"Content-Type": "application/json"}

    def generate_response(self, content_text: str) -> requests.Response:
        payload = {"content": content_text}
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


@app.post("/init_session")
def init_session(req: InitSessionRequest):
    session_id = req.session_id
    if session_id not in sessions:
        sessions[session_id] = {
            "conversation": [],
            "is_responding": False,
            "prompt_to_process": None
        }
    return {"status": "success", "session_id": session_id}


@app.get("/get_conversation/{session_id}")
def get_conversation(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]["conversation"]


@app.get("/get_session_state/{session_id}")
def get_session_state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "is_responding": sessions[session_id]["is_responding"],
        "prompt_to_process": sessions[session_id]["prompt_to_process"]
    }


@app.post("/add_user_message")
def add_user_message(req: MessageRequest):
    session_id = req.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    timestamp = datetime.now().strftime("%H:%M:%S")
    sessions[session_id]["conversation"].append({
        "sender": "user",
        "message": req.content_text,
        "timestamp": timestamp
    })

    sessions[session_id]["is_responding"] = True
    sessions[session_id]["prompt_to_process"] = req.content_text

    return {"status": "success"}


@app.post("/process_ai_response")
def process_ai_response(req: InitSessionRequest):
    session_id = req.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if not sessions[session_id]["prompt_to_process"]:
        return {"status": "error", "message": "No prompt to process"}

    # 构建上下文
    context_content = ""
    for msg in sessions[session_id]["conversation"]:
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

    # 调用API
    api = WenHuaAPI()
    try:
        response_stream = api.generate_response(context_content)
        full_response = ""

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
                    except json.JSONDecodeError:
                        continue

        # 添加AI回复
        timestamp = datetime.now().strftime("%H:%M:%S")
        sessions[session_id]["conversation"].append({
            "sender": "ai",
            "message": full_response,
            "timestamp": timestamp
        })

        sessions[session_id]["is_responding"] = False
        sessions[session_id]["prompt_to_process"] = None

        return {"status": "success", "response": full_response}

    except Exception as e:
        error_msg = f"抱歉，发生错误: {str(e)}"
        timestamp = datetime.now().strftime("%H:%M:%S")
        sessions[session_id]["conversation"].append({
            "sender": "ai",
            "message": error_msg,
            "timestamp": timestamp
        })
        sessions[session_id]["is_responding"] = False
        sessions[session_id]["prompt_to_process"] = None

        return {"status": "error", "message": error_msg}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
