"""
Telegram 消息发送模块
通过 Telegram Bot API 发送消息
"""

import requests
import time
from typing import Optional
from datetime import datetime, timedelta


def send_message(bot_token: str, chat_id: str, text: str, parse_mode: str = 'Markdown') -> bool:
    """
    发送消息到 Telegram
    
    Args:
        bot_token: Telegram Bot Token
        chat_id: 聊天 ID
        text: 消息内容
        parse_mode: 解析模式 ('Markdown' 或 'HTML')
    
    Returns:
        发送是否成功
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # 检查消息长度
    if len(text) > 4096:
        print(f"⚠️ 消息长度 {len(text)} 超过 Telegram 限制 4096，将被截断")
        text = text[:4093] + "..."
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }
    
    try:
        print("正在发送 Telegram 消息...")
        print(f"消息长度: {len(text)} 字符")
        
        response = requests.post(url, json=payload, timeout=30)
        
        # 打印响应状态
        print(f"HTTP 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Telegram 消息发送成功")
                return True
            else:
                print(f"❌ Telegram API 返回错误: {result.get('description', '未知错误')}")
                print(f"错误代码: {result.get('error_code', 'N/A')}")
                return False
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 发送 Telegram 消息失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发送消息时发生未知错误: {e}")
        return False


def send_message_with_retry(bot_token: str, chat_id: str, text: str, max_retries: int = 3) -> bool:
    """
    带重试机制的消息发送
    
    Args:
        bot_token: Telegram Bot Token
        chat_id: 聊天 ID
        text: 消息内容
        max_retries: 最大重试次数
    
    Returns:
        发送是否成功
    """
    for attempt in range(max_retries):
        if send_message(bot_token, chat_id, text):
            return True
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 2  # 递增等待时间
            print(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    print(f"❌ 经过 {max_retries} 次尝试后仍然发送失败")
    return False


def validate_telegram_config(bot_token: str, chat_id: str) -> bool:
    """
    验证 Telegram 配置
    
    Args:
        bot_token: Telegram Bot Token
        chat_id: 聊天 ID
    
    Returns:
        配置是否有效
    """
    if not bot_token or not chat_id:
        print("❌ Telegram Bot Token 或 Chat ID 未设置")
        return False
    
    # 测试发送一个简单的测试消息
    test_message = "🤖 Reddit Bot 配置测试消息"
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('ok'):
            print("✅ Telegram 配置验证成功")
            return True
        else:
            print(f"❌ Telegram 配置验证失败: {result.get('description', '未知错误')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram 配置验证失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证配置时发生未知错误: {e}")
        return False


def format_message_for_telegram(posts: list, timestamp: str) -> str:
    """
    格式化消息用于 Telegram 发送 - 优化版
    
    Args:
        posts: 帖子列表
        timestamp: 时间戳
    
    Returns:
        格式化后的消息
    """
    if not posts:
        return "📭 今日暂无重要资讯"
    
    # 智能消息头部
    current_hour = datetime.now().hour
    if 6 <= current_hour <= 12:
        header = "🌅 晨间财经要闻"
    elif 18 <= current_hour <= 22:
        header = "🌆 晚间市场动态"
    else:
        header = "📰 实时资讯速递"
    
    message = f"{header}\n\n"
    
    # 按重要性和新鲜度排序
    sorted_posts = sorted(posts, key=lambda x: (
        x.get('quality_score', 0) + x.get('freshness_score', 0) * 2,
        x.get('score', 0)
    ), reverse=True)
    
    # 生成消息内容
    post_counter = 1
    for post in sorted_posts[:12]:  # 最多显示12条
        # 转义 Markdown 特殊字符
        title = post['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
        
        # 智能标题处理
        if len(title) > 80:
            title = title[:77] + "..."
        
        # 添加重要性标识
        quality_score = post.get('quality_score', 0)
        if quality_score >= 15:
            importance = "🔥"
        elif quality_score >= 10:
            importance = "⭐"
        else:
            importance = "📌"
        
        message += f"{importance} **{title}**\n"
        message += f"🔗 [查看原文]({post['url']})\n"
        
        # 时间信息
        created_utc = post.get('created_utc')
        time_info = ""
        try:
            if isinstance(created_utc, (int, float)) and created_utc > 0:
                dt = datetime.utcfromtimestamp(created_utc)
                delta = datetime.utcnow() - dt
                if delta < timedelta(minutes=30):
                    time_info = "🆕 刚刚"
                elif delta < timedelta(hours=1):
                    time_info = f"🕐 {int(delta.total_seconds() // 60)}分钟前"
                elif delta < timedelta(hours=6):
                    time_info = f"🕕 {int(delta.total_seconds() // 3600)}小时前"
                else:
                    time_info = f"📅 {int(delta.days)}天前"
        except Exception:
            time_info = "📅 时间未知"
        
        # 来源信息
        source = post.get('subreddit', 'unknown')
        source_emoji = {
            'stocks': '📈', 'wallstreetbets': '🎯', 'bitcoin': '₿',
            'cryptocurrency': '💎', 'investing': '💰', 'china': '🇨🇳',
            'geopolitics': '🌍', 'worldnews': '🌐', 'politics': '🏛️'
        }.get(source.lower(), '📰')
        
        message += f"{time_info} | {source_emoji} r/{source} | ⭐ {post.get('score', 0)}\n"
        
        # 添加智能摘要
        summary = post.get('summary', '')
        if summary:
            # 清理摘要
            summary = summary.strip()
            if len(summary) > 150:
                summary = summary[:147] + "..."
            message += f"💡 {summary}\n"
        
        message += "\n"
        post_counter += 1
    
    # 智能消息尾部
    message += f"⏰ 更新时间: {timestamp} (北京时间)\n"
    message += "🤖 智能筛选 | AI 摘要 | 实时更新"
    
    # 检查消息长度
    if len(message) > 4000:
        message = message[:3997] + "..."
    
    return message


if __name__ == "__main__":
    # 测试代码
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if bot_token and chat_id:
        print("测试 Telegram 配置...")
        if validate_telegram_config(bot_token, chat_id):
            print("配置验证成功!")
        else:
            print("配置验证失败!")
    else:
        print("未设置 TELEGRAM_BOT_TOKEN 或 CHAT_ID")
    
    # 测试消息格式化
    test_posts = [
        {
            'title': 'Bitcoin reaches new high',
            'url': 'https://reddit.com/r/bitcoin/test',
            'score': 1234,
            'subreddit': 'bitcoin',
            'summary': '比特币创历史新高，机构投资者持续买入'
        },
        {
            'title': 'Tesla stock analysis',
            'url': 'https://reddit.com/r/stocks/test',
            'score': 567,
            'subreddit': 'stocks',
            'summary': '特斯拉股票分析报告，看好长期前景'
        }
    ]
    
    test_message = format_message_for_telegram(test_posts, "2025-01-12 09:00")
    print("\n测试消息格式:")
    print(test_message)
