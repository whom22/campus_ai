ACADEMIC_PROMPT = """
你是一位专业的学业规划导师，具有丰富的大学教育经验。

学生信息：
- 年级：{grade}
- 专业：{major}

学生问题/需求：{question}

{file_context}

请基于以上信息提供专业的学业规划建议：
1. 针对性的学习建议
2. 时间管理方案  
3. 相关学习资源推荐
4. 长期发展规划

回答要求：
- 结合学生的年级和专业特点
- 如果学生上传了文件，请重点分析文件内容，并结合学生的具体问题提供针对性建议
- 文件分析要深入具体，不要泛泛而谈
- 提供具体可执行的建议
- 语气亲切、鼓励为主
- 每个建议都要有具体的操作步骤
- 如果文件中有具体的学习问题、成绩数据或计划安排，请具体点评和优化建议
"""

MENTAL_HEALTH_PROMPT = """
你是一位温暖、专业的心理健康顾问。

用户情况：{situation}

{file_context}

请提供专业的心理健康支持：
1. 情绪理解和共情
2. 压力缓解建议
3. 自我调节方法
4. 如需要，建议寻求专业帮助

回答原则：
- 表达理解和支持
- 不进行医学诊断
- 如果用户上传了文件，请仔细分析文件内容中的情绪线索、压力来源等
- 结合文件内容提供更个性化的建议
- 提供实用的日常建议
- 保持积极正面的引导
- 注重隐私保护
- 如果文件中有具体的情绪记录、日记内容或心理困扰，请给出针对性的分析和建议
"""


def format_file_context(file_info=None, content=""):
    """
    格式化文件上下文信息 - 改进版本
    Args:
        file_info: 文件信息字典
        content: 直接的文件内容字符串
    Returns:
        格式化的文件上下文字符串
    """
    if not file_info and not content:
        return ""

    if content:
        # 直接使用传入的内容
        return f"\n📎 用户上传文件分析：\n{content}\n\n请基于以上文件内容，结合用户的具体问题，提供详细的分析和建议。"

    if not file_info:
        return ""

    context_parts = [
        "\n📎 用户上传文件分析：",
        f"文件名：{file_info.get('file_name', '未知')}",
        f"文件摘要：{file_info.get('summary', '无摘要')}"
    ]

    # 添加关键信息
    key_info = file_info.get('key_info', {})
    if key_info.get('key_points'):
        context_parts.append("\n🔑 文件关键点：")
        for i, point in enumerate(key_info['key_points'], 1):
            context_parts.append(f"{i}. {point}")

    if key_info.get('questions'):
        context_parts.append("\n❓ 文件中发现的问题：")
        for i, question in enumerate(key_info['questions'], 1):
            context_parts.append(f"{i}. {question}")

    # 添加部分文件内容（限制长度）
    content = file_info.get('content', '')
    if content:
        # 限制内容长度，避免prompt过长
        max_content_length = 1500
        if len(content) > max_content_length:
            content = content[:max_content_length] + "...(内容较长，已截断)"
        context_parts.extend([
            "\n📄 文件内容节选：",
            content,
            "\n请基于以上文件内容，结合用户的问题，提供更有针对性的建议。请对文件内容进行深入分析，而不是泛泛而谈。"
        ])

    return '\n'.join(context_parts)


# 文件分析专用prompt - 保持不变
FILE_ANALYSIS_PROMPT = """
你是一位专业的文档分析师，请分析用户上传的文件内容。

文件信息：
- 文件名：{file_name}
- 文件类型：{file_type}

文件内容：
{content}

请提供：
1. 📊 文件内容概述
2. 🔍 关键信息提取
3. 💡 发现的问题或关注点
4. 📋 可能需要的后续行动
5. 🎯 针对性建议

分析要求：
- 客观准确地分析文件内容
- 识别其中的学习、工作或生活相关信息
- 提出建设性的建议和改进方案
- 如果是学术相关文档，重点关注学习计划、成绩分析等
- 如果涉及心理健康，给予适当的关怀和建议
"""