#!/usr/bin/env python3
"""
极简版 Reddit Telegram Bot
用于确保 GitHub Actions 能成功运行
"""

import os
import sys
import requests
from datetime import datetime, timedelta

def get_beijing_timestamp():
    """获取北京时间戳"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time.strftime("%Y-%m-%d %H:%M")

def fetch_simple_reddit_posts():
    """获取简单的 Reddit 帖子"""
    print("📡 获取 Reddit 帖子...")
    
    posts = []
    subreddits = ['stocks', 'bitcoin']
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/top.json"
            params = {'limit': 1, 't': 'day'}
            
            print(f"  获取 r/{subreddit}...")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'children' in data['data']:
                    for post_data in data['data']['children'][:1]:
                        post = post_data['data']
                        posts.append({
                            'title': post.get('title', '')[:100],  # 限制长度
                            'url': f"https://reddit.com{post.get('permalink', '')}",
                            'score': post.get('score', 0),
                            'subreddit': subreddit
                        })
                    print(f"  ✅ r/{subreddit}: 1 个帖子")
                else:
                    print(f"  ⚠️ r/{subreddit}: 无数据")
            else:
                print(f"  ❌ r/{subreddit}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ r/{subreddit}: {e}")
    
    print(f"📊 总共获取 {len(posts)} 个帖子")
    return posts

def format_simple_message(posts, timestamp):
    """格式化简单消息"""
    if not posts:
        return "📭 今天没有找到相关帖子"
    
    message = "🔔 每日 Reddit 财经要闻\n\n"
    
    for i, post in enumerate(posts, 1):
        # 转义特殊字符
        title = post['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
        
        message += f"{i}️⃣ [{title}]({post['url']})\n"
        message += f"⭐ 评分: {post['score']} | 📍 r/{post['subreddit']}\n\n"
    
    message += f"📅 更新时间: {timestamp} (UTC+8)\n"
    message += "🤖 由 Reddit API 提供"
    
    # 确保不超过 Telegram 限制
    if len(message) > 4000:
        message = message[:3997] + "..."
    
    return message

def send_telegram_message(bot_token, chat_id, text):
    """发送 Telegram 消息"""
    print("📤 发送 Telegram 消息...")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }
    
    try:
        print(f"消息长度: {len(text)} 字符")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"HTTP 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Telegram 消息发送成功")
                return True
            else:
                print(f"❌ Telegram API 错误: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Reddit Telegram Bot (极简版)")
    print("=" * 40)
    
    try:
        # 1. 检查环境变量
        print("📋 检查环境变量...")
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ 环境变量未设置")
            sys.exit(1)
        
        print("✅ 环境变量检查通过")
        
        # 2. 获取 Reddit 帖子
        posts = fetch_simple_reddit_posts()
        
        if not posts:
            print("❌ 没有获取到任何帖子")
            sys.exit(1)
        
        # 3. 格式化消息
        print("📝 格式化消息...")
        timestamp = get_beijing_timestamp()
        message = format_simple_message(posts, timestamp)
        
        # 4. 发送消息
        success = send_telegram_message(bot_token, chat_id, message)
        
        if success:
            print("🎉 任务完成! 消息已成功发送到 Telegram")
        else:
            print("❌ 任务失败! 消息发送失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
