from openai import OpenAI

# 创建客户端
client = OpenAI(
    api_key="bce-v3/ALTAK-RiaEJnLNwWS37tszkaoyt/5db71fc6cdf2b5d56fdcfb1bfd8e86aecb3b1fb1",  # 千帆bearer token
    base_url="https://qianfan.baidubce.com/v2",  # 千帆域名
    default_headers={"appid": "app-XyzFJbtu"}  # 用户在千帆上的appid，非必传
)

# 测试调用
completion = client.chat.completions.create(
    model="ernie-4.0-turbo-8k",  # 预置服务请查看模型列表，定制服务请填入API地址
    messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
              {'role': 'user', 'content': 'Hello！'}]
)

print("第一次调用结果:")
print(completion.choices[0].message.content)


# 基本对话 - 修正后的调用方式
def chat_with_qianfan(prompt, system_prompt="You are a helpful assistant."):
    """简单的聊天函数"""
    completion = client.chat.completions.create(
        model="ernie-4.0-turbo-8k",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
    )
    return completion.choices[0].message.content


# 使用修正后的方式
print("\n介绍人工智能:")
response = chat_with_qianfan("介绍一下人工智能的发展历史")
print(response)


# 流式对话 - 修正后的调用方式
def stream_chat_with_qianfan(prompt, system_prompt="You are a helpful assistant."):
    """流式聊天函数"""
    stream = client.chat.completions.create(
        model="ernie-4.0-turbo-8k",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()  # 换行


# 使用流式对话
print("\n写诗（流式输出）:")
stream_chat_with_qianfan("写一首关于春天的诗")

print("\n完成测试！")