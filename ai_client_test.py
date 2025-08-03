# 最终测试
from ai_client import QianfanChat

try:
    client = QianfanChat()
    response = client.chat("你是一个AI助手", "你好")
    print("✅ 成功:", response)
except Exception as e:
    print("❌ 失败:", e)