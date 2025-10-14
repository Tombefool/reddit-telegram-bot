#!/usr/bin/env python3
"""
Render 优化版 Reddit Telegram Bot
专门为 Render Cron Job 环境优化
"""

import os
import sys
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量（Render 会自动注入）
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

def fetch_reddit_posts():
    """获取 Reddit 帖子"""
    log("📡 开始获取 Reddit 帖子...")
    
    posts = []
    subreddits = ['stocks', 'wallstreetbets', 'investing', 'cryptocurrency', 'bitcoin']
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    for subreddit in subreddits:
        try:
            log(f"  获取 r/{subreddit}...")
            url = f"https://www.reddit.com/r/{subreddit}/top.json"
            params = {'limit': 2, 't': 'day'}
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
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
                            'selftext': post.get('selftext', '')[:500]
                        })
                    log(f"  ✅ r/{subreddit}: {len(data['data']['children'])} 个帖子")
                else:
                    log(f"  ⚠️ r/{subreddit}: 无数据")
            else:
                log(f"  ❌ r/{subreddit}: HTTP {response.status_code}")
            
            # 添加延迟避免被限流
            time.sleep(3)
            
        except Exception as e:
            log(f"  ❌ r/{subreddit}: {e}")
    
    log(f"📊 总共获取 {len(posts)} 个帖子")
    return posts

def summarize_post(title, text, api_key=None):
    """生成帖子摘要"""
    if not api_key:
        # 简单截断
        if len(text) > 150:
            return text[:147] + "..."
        return text or "无内容"
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"请为以下 Reddit 帖子生成简洁的中文摘要 (2-3句话):\n标题: {title}\n内容: {text[:1000]}"
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip()
        else:
            return text[:150] + "..." if len(text) > 150 else text
            
    except Exception as e:
        log(f"⚠️ Gemini API 失败: {e}")
        return text[:150] + "..." if len(text) > 150 else text

def format_message(posts, timestamp):
    """格式化消息"""
    if not posts:
        return "📭 今天没有找到相关帖子"
    
    message = "🔔 每日 Reddit 财经要闻 (股票 & 加密货币)\n\n"
    
    # 按评分排序
    posts.sort(key=lambda x: x['score'], reverse=True)
    
    for i, post in enumerate(posts[:8], 1):  # 最多8个帖子
        # 转义 Markdown 特殊字符
        title = post['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
        
        message += f"{i}️⃣ [{title}]({post['url']})\n"
        message += f"⭐ 评分: {post['score']} | 📍 r/{post['subreddit']}\n"
        
        # 添加摘要
        summary = post.get('summary', '')
        if summary:
            message += f"💬 {summary}\n"
        
        message += "\n"
    
    message += f"📅 更新时间: {timestamp} (UTC+8)\n"
    message += "🤖 由 Reddit API 提供 | Gemini 可选摘要"
    
    # 检查长度
    if len(message) > 4000:
        message = message[:3997] + "..."
    
    return message

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
    log("🚀 Reddit Telegram Bot 启动 (Render 版)")
    log("=" * 50)
    
    try:
        # 1. 检查环境变量
        log("📋 检查环境变量...")
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not bot_token or not chat_id:
            log("❌ 缺少必需的环境变量")
            sys.exit(1)
        
        log("✅ 环境变量检查通过")
        
        # 2. 获取 Reddit 帖子
        posts = fetch_reddit_posts()
        
        if not posts:
            log("⚠️ 没有获取到任何帖子，发送备用消息")
            # 发送备用消息而不是退出
            backup_message = f"""🔔 每日 Reddit 财经要闻

📅 更新时间: {get_beijing_timestamp()} (UTC+8)

⚠️ 今日 Reddit API 暂时不可用
🤖 请稍后查看 Reddit 官网获取最新资讯

💡 我们正在努力恢复服务..."""
            
            success = send_telegram_message(bot_token, chat_id, backup_message)
            if success:
                log("✅ 备用消息发送成功")
                return
            else:
                log("❌ 备用消息发送失败")
                sys.exit(1)
        
        # 3. 生成摘要
        log("🤖 生成帖子摘要...")
        for post in posts:
            post['summary'] = summarize_post(
                post['title'], 
                post['selftext'], 
                gemini_key
            )
        
        # 4. 格式化消息
        log("📝 格式化消息...")
        timestamp = get_beijing_timestamp()
        message = format_message(posts, timestamp)
        
        # 5. 发送消息
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
