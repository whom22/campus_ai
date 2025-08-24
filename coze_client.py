import requests
import json


class CozeChat:
    def __init__(self, api_key=None, bot_id=None):
        self.api_key = api_key or "your_coze_api_key"
        self.bot_id = bot_id or "your_coze_bot_id"
        self.base_url = "https://api.coze.cn/open_api/v2/chat"

    def chat(self, system_prompt, user_message):
        """调用Coze智能体进行心理健康对话"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': 'api.coze.cn',
            'Connection': 'keep-alive'
        }

        payload = {
            "conversation_id": "123",
            "bot_id": self.bot_id,
            "user": "user_id",
            "query": user_message,
            "stream": False
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            if result.get('code') == 0:
                messages = result.get('messages', [])
                for message in messages:
                    if message.get('type') == 'answer':
                        return message.get('content', '抱歉，我无法回答您的问题。')

            return "抱歉，服务暂时不可用。"

        except Exception as e:
            return f"调用智能体失败：{str(e)}"