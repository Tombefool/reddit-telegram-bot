#!/usr/bin/env python3
"""
简化版 Reddit Telegram Bot - 使用备用 API 端点
"""

import os
import sys
import requests
import time
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def log(message):
    """统一日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def get_beijing_timestamp():
    """获取北京时间戳"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time.strftime("%Y-%m-%d %H:%M")

def fetch_reddit_posts_simple():
    """使用简化的方式获取 Reddit 帖子"""
    log("📡 开始获取 Reddit 帖子 (简化版)...")
    
    posts = []
    subreddits = ['stocks', 'bitcoin']  # 减少到2个板块
    
    # 使用更真实的浏览器 headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.reddit.com/',
        'Origin': 'https://www.reddit.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    }
    
    for subreddit in subreddits:
        try:
            log(f"  获取 r/{subreddit}...")
            
            # 尝试不同的 URL 格式
            urls_to_try = [
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=2",
                f"https://www.reddit.com/r/{subreddit}/top.json?limit=2&t=day",
                f"https://old.reddit.com/r/{subreddit}/hot.json?limit=2"
            ]
            
            success = False
            for url in urls_to_try:
                try:
                    log(f"    尝试: {url}")
                    response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'children' in data['data']:
                            for post_data in data['data']['children']:
                                post = post_data['data']
                                posts.append({
                                    'title': post.get('title', '')[:100],
                                    'url': f"https://reddit.com{post.get('permalink', '')}",
                                    'score': post.get('score', 0),
                                    'subreddit': subreddit,
                                    'selftext': post.get('selftext', '')[:200]
                                })
                            log(f"  ✅ r/{subreddit}: {len(data['data']['children'])} 个帖子")
                            success = True
                            break
                        else:
                            log(f"    ⚠️ 无数据: {url}")
                    else:
                        log(f"    ❌ HTTP {response.status_code}: {url}")
                        
                except Exception as e:
                    log(f"    ❌ 错误: {e}")
                    continue
            
            if not success:
                log(f"  ❌ r/{subreddit}: 所有 URL 都失败")
            
            # 随机延迟 2-5 秒
            delay = random.uniform(2, 5)
            log(f"  等待 {delay:.1f} 秒...")
            time.sleep(delay)
            
        except Exception as e:
            log(f"  ❌ r/{subreddit}: {e}")
    
    log(f"📊 总共获取 {len(posts)} 个帖子")
    return posts

def send_telegram_message(bot_token, chat_id, text):
    """发送 Telegram 消息"""
    log("📤 发送 Telegram 消息...")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }
    
    try:
        log(f"消息长度: {len(text)} 字符")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                log("✅ Telegram 消息发送成功")
                return True
            else:
                log(f"❌ Telegram API 错误: {result.get('description')}")
                return False
        else:
            log(f"❌ HTTP 错误: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"❌ 发送失败: {e}")
        return False

def main():
    """主函数"""
    log("🚀 Reddit Telegram Bot 启动 (简化版)")
    log("=" * 50)
    
    try:
        # 1. 检查环境变量
        log("📋 检查环境变量...")
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token or not chat_id:
            log("❌ 缺少必需的环境变量")
            sys.exit(1)
        
        log("✅ 环境变量检查通过")
        
        # 2. 获取 Reddit 帖子
        posts = fetch_reddit_posts_simple()
        
        # 3. 格式化消息
        timestamp = get_beijing_timestamp()
        
        if posts:
            message = f"""🔔 每日 Reddit 财经要闻 (简化版)

📊 今日获取到 {len(posts)} 个热门帖子

"""
            
            for i, post in enumerate(posts[:5], 1):  # 最多5个帖子
                title = post['title'].replace('*', '\\*').replace('_', '\\_')
                message += f"{i}️⃣ [{title}]({post['url']})\n"
                message += f"⭐ 评分: {post['score']} | 📍 r/{post['subreddit']}\n\n"
            
            message += f"📅 更新时间: {timestamp} (UTC+8)\n"
            message += "🤖 由 Reddit API 提供 (简化版)"
        else:
            message = f"""🔔 每日 Reddit 财经要闻

📅 更新时间: {timestamp} (UTC+8)

⚠️ 今日 Reddit API 暂时不可用
🤖 请稍后查看 Reddit 官网获取最新资讯

💡 我们正在努力恢复服务..."""
        
        # 4. 发送消息
        success = send_telegram_message(bot_token, chat_id, message)
        
        if success:
            log("🎉 任务完成! 消息已成功发送到 Telegram")
        else:
            log("❌ 任务失败! 消息发送失败")
            sys.exit(1)
            
    except Exception as e:
        log(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
