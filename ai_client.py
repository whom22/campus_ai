import os
import qianfan
import logging
from typing import List, Dict, Any, Optional, Union, Iterator
import time


class QianfanChat:
    """百度千帆大模型聊天客户端"""

    def __init__(
            self,
            model: str = "ernie-4.0-turbo-8k",
            app_id: str = "app-XyzFJbtu",
            bearer_token: str = "bce-v3/ALTAK-RiaEJnLNwWS37tszkaoyt/5db71fc6cdf2b5d56fdcfb1bfd8e86aecb3b1fb1",
            max_retries: int = 3,
            **kwargs
    ):
        self.model = model
        self.max_retries = max_retries

        # 设置认证信息
        os.environ["QIANFAN_BEARER_TOKEN"] = bearer_token

        # 初始化客户端
        try:
            self.client = qianfan.ChatCompletion(
                version="2",
                app_id=app_id,
                **kwargs
            )
        except Exception as e:
            logging.error(f"初始化千帆v2客户端失败: {e}")
            raise

    def chat(
            self,
            system_prompt_or_messages: Union[str, List[Dict]],
            user_input: Optional[str] = None,
            temperature: float = 0.7,
            top_p: float = 0.9,
            stream: bool = False,
            **kwargs
    ) -> Union[str, Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        发送聊天请求

        支持两种调用方式：
        1. chat(system_prompt, user_input) - 兼容原来的调用方式
        2. chat(messages) - 直接传递消息列表
        """

        # 处理不同的调用方式
        if isinstance(system_prompt_or_messages, str) and user_input is not None:
            # 兼容原来的调用方式: chat(system_prompt, user_input)
            messages = [
                {"role": "system", "content": system_prompt_or_messages},
                {"role": "user", "content": user_input}
            ]
            return_string = True
        elif isinstance(system_prompt_or_messages, list):
            # 新的调用方式: chat(messages)
            messages = system_prompt_or_messages
            return_string = False
        elif isinstance(system_prompt_or_messages, str) and user_input is None:
            # 简单调用方式: chat(user_message)
            messages = [{"role": "user", "content": system_prompt_or_messages}]
            return_string = True
        else:
            raise ValueError("Invalid arguments. Use chat(system_prompt, user_input) or chat(messages)")

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            **kwargs
        }

        if stream:
            return self._stream_chat(params)
        else:
            result = self._chat_with_retry(params)
            # 为了兼容原来的调用方式，直接返回内容字符串
            if return_string:
                return result.get("content", "")
            else:
                return result

    def _chat_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """带重试的聊天请求"""

        for attempt in range(self.max_retries):
            try:
                response = self.client.do(**params)

                # v2版本响应格式（OpenAI标准）
                if "choices" in response and response["choices"]:
                    choice = response["choices"][0]
                    return {
                        "content": choice["message"]["content"],
                        "usage": response.get("usage", {}),
                        "model": response.get("model", ""),
                        "finish_reason": choice.get("finish_reason", "")
                    }
                else:
                    return {"error": "No choices in response", "content": ""}

            except Exception as e:
                logging.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return {"error": str(e), "content": "抱歉，AI服务暂时不可用，请稍后重试。"}

    def _stream_chat(self, params: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """处理流式响应"""
        try:
            response = self.client.do(**params)

            for chunk in response:
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield {"content": content, "error": False}

        except Exception as e:
            yield {"error": str(e), "content": ""}

    def chat_with_history(self, messages: List[Dict], user_input: str) -> str:
        """
        带历史记录的聊天
        """
        messages.append({"role": "user", "content": user_input})
        result = self.chat(messages)
        if isinstance(result, dict):
            return result.get("content", "")
        return str(result)

    def safe_ai_call(self, system_prompt: str, user_input: str, max_retries: int = 3) -> str:
        """
        安全的AI调用，带重试机制 - 兼容原来的调用方式
        """
        old_max_retries = self.max_retries
        self.max_retries = max_retries

        try:
            result = self.chat(system_prompt, user_input)
            return str(result)
        finally:
            self.max_retries = old_max_retries


# 简化的工厂函数
def create_qianfan_client():
    """创建一个配置好的千帆客户端"""
    return QianfanChat()