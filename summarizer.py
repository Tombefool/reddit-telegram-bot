"""
文本摘要模块
支持使用 Gemini API 生成摘要,如果不可用则使用简单文本截断
"""

import os
from typing import Optional


def summarize_post(title: str, text: str, api_key: Optional[str] = None) -> str:
    """
    为帖子生成摘要
    
    Args:
        title: 帖子标题
        text: 帖子内容
        api_key: Gemini API 密钥 (可选)
    
    Returns:
        摘要文本
    """
    if api_key and api_key.strip():
        try:
            return summarize_with_gemini(title, text, api_key)
        except Exception as e:
            print(f"Gemini API 摘要失败: {e}")
            print("回退到文本截断模式")
    
    return truncate_text(title, text)


def summarize_with_gemini(title: str, text: str, api_key: str) -> str:
    """
    使用 Gemini API 生成摘要
    
    Args:
        title: 帖子标题
        text: 帖子内容
        api_key: Gemini API 密钥
    
    Returns:
        Gemini 生成的摘要
    """
    try:
        import google.generativeai as genai
        
        # 配置 Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 构建智能提示词
        prompt = f"""
你是一位专业的新闻编辑，请为以下内容生成高质量的中文摘要：

标题: {title}

内容: {text[:1000]}

要求:
1. 摘要要简洁有力，突出核心信息
2. 使用自然流畅的中文表达
3. 控制在2-3句话内
4. 保持客观中立，避免主观判断
5. 如果涉及金融内容，请用专业术语
6. 如果涉及政治内容，请保持平衡报道
7. 避免使用"据悉"、"据报道"等冗余表达
8. 直接陈述事实，不要添加解释性语言

请直接输出摘要，不要任何前缀或后缀。
"""
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        # 确保摘要不为空
        if not summary:
            return truncate_text(title, text)
        
        return summary
        
    except ImportError:
        print("google-generativeai 库未安装,回退到文本截断模式")
        return truncate_text(title, text)
    except Exception as e:
        print(f"Gemini API 调用失败: {e}")
        return truncate_text(title, text)


def truncate_text(title: str, text: str, max_length: int = 150) -> str:
    """
    简单文本截断
    
    Args:
        title: 帖子标题
        text: 帖子内容
        max_length: 最大长度
    
    Returns:
        截断后的文本
    """
    if not text or text.strip() == "":
        return f"标题: {title}"
    
    # 清理文本
    cleaned_text = text.strip()
    
    # 移除多余的空白字符
    cleaned_text = ' '.join(cleaned_text.split())
    
    # 如果文本长度超过限制,进行截断
    if len(cleaned_text) > max_length:
        truncated = cleaned_text[:max_length]
        # 尝试在单词边界截断
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # 如果最后一个空格位置合理
            truncated = truncated[:last_space]
        truncated += "..."
        return truncated
    
    return cleaned_text


def format_summary_for_telegram(summary: str) -> str:
    """
    格式化摘要用于 Telegram 显示
    
    Args:
        summary: 原始摘要文本
    
    Returns:
        格式化后的摘要
    """
    # 转义 Markdown 特殊字符
    formatted = summary.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
    
    return f"💬 {formatted}"


if __name__ == "__main__":
    # 测试代码
    test_title = "Bitcoin reaches new all-time high"
    test_text = "Bitcoin has reached a new all-time high of $100,000 today, driven by institutional adoption and positive regulatory news. Many analysts believe this is just the beginning of a new bull market cycle."
    
    print("测试文本截断:")
    truncated = truncate_text(test_title, test_text)
    print(f"截断结果: {truncated}")
    
    print("\n测试格式化:")
    formatted = format_summary_for_telegram(truncated)
    print(f"格式化结果: {formatted}")
    
    # 如果有 Gemini API key,测试 API 调用
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print("\n测试 Gemini API:")
        try:
            gemini_summary = summarize_with_gemini(test_title, test_text, gemini_key)
            print(f"Gemini 摘要: {gemini_summary}")
        except Exception as e:
            print(f"Gemini API 测试失败: {e}")
    else:
        print("\n未设置 GEMINI_API_KEY,跳过 Gemini API 测试")
