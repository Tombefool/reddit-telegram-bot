"""
Reddit Telegram 自动推送机器人主程序
每天北京时间 09:00 自动抓取 Reddit 财经板块热门帖子并推送到 Telegram
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from reddit_fetcher import fetch_multiple_subreddits
from summarizer import summarize_post, format_summary_for_telegram
from telegram_sender import send_message_with_retry, format_message_for_telegram, validate_telegram_config


def load_configuration():
    """加载环境配置"""
    load_dotenv()
    
    config = {
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('CHAT_ID'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    # 验证必需配置
    if not config['telegram_bot_token']:
        print("❌ 错误: 未设置 TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    
    if not config['chat_id']:
        print("❌ 错误: 未设置 CHAT_ID")
        sys.exit(1)
    
    print("✅ 配置加载成功")
    return config


def get_target_subreddits():
    """获取目标 Reddit 板块列表"""
    return [
        'stocks',
        'wallstreetbets', 
        'investing',
        'cryptocurrency',
        'bitcoin'
    ]


def process_posts(posts, gemini_api_key=None):
    """处理帖子,生成摘要"""
    processed_posts = []
    
    for post in posts:
        print(f"处理帖子: {post['title'][:50]}...")
        
        # 生成摘要
        summary = summarize_post(
            title=post['title'],
            text=post['selftext'],
            api_key=gemini_api_key
        )
        
        # 格式化摘要
        formatted_summary = format_summary_for_telegram(summary)
        
        # 添加到处理后的帖子
        processed_post = post.copy()
        processed_post['summary'] = formatted_summary
        processed_posts.append(processed_post)
    
    return processed_posts


def get_beijing_timestamp():
    """获取北京时间戳"""
    # GitHub Actions 运行在 UTC 时间
    # 北京时间 = UTC + 8
    utc_now = datetime.utcnow()
    beijing_time = utc_now.replace(hour=utc_now.hour + 8)
    
    return beijing_time.strftime("%Y-%m-%d %H:%M")


def main():
    """主程序入口"""
    print("🚀 Reddit Telegram Bot 启动")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        config = load_configuration()
        
        # 2. 验证 Telegram 配置
        print("验证 Telegram 配置...")
        if not validate_telegram_config(config['telegram_bot_token'], config['chat_id']):
            print("❌ Telegram 配置验证失败")
            sys.exit(1)
        
        # 3. 获取目标板块
        subreddits = get_target_subreddits()
        print(f"目标板块: {', '.join(subreddits)}")
        
        # 4. 抓取 Reddit 帖子
        print("\n开始抓取 Reddit 帖子...")
        posts = fetch_multiple_subreddits(subreddits, posts_per_subreddit=2)
        
        if not posts:
            print("❌ 没有获取到任何帖子")
            sys.exit(1)
        
        print(f"✅ 成功获取 {len(posts)} 个帖子")
        
        # 5. 处理帖子 (生成摘要)
        print("\n开始处理帖子...")
        processed_posts = process_posts(posts, config['gemini_api_key'])
        
        # 6. 格式化消息
        print("\n格式化消息...")
        timestamp = get_beijing_timestamp()
        message = format_message_for_telegram(processed_posts, timestamp)
        
        # 7. 发送到 Telegram
        print("\n发送消息到 Telegram...")
        success = send_message_with_retry(
            config['telegram_bot_token'],
            config['chat_id'],
            message
        )
        
        if success:
            print("🎉 任务完成! 消息已成功发送到 Telegram")
        else:
            print("❌ 任务失败! 消息发送失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
