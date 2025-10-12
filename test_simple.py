#!/usr/bin/env python3
"""
简化版 Reddit Telegram Bot 测试
用于诊断 GitHub Actions 问题
"""

import os
import sys
from datetime import datetime, timedelta

def test_simple_message():
    """测试发送简单消息"""
    print("🧪 测试发送简单消息...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ 环境变量未设置")
        return False
    
    import requests
    
    # 简单的测试消息
    test_message = f"""🤖 Reddit Bot 测试消息

📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ GitHub Actions 运行正常
🔧 正在诊断问题...

请忽略此测试消息。"""
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        print(f"发送消息到 Chat ID: {chat_id}")
        print(f"消息长度: {len(test_message)} 字符")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"HTTP 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ 简单消息发送成功")
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

def test_reddit_simple():
    """测试 Reddit API 简单访问"""
    print("\n🧪 测试 Reddit API...")
    
    import requests
    
    url = "https://www.reddit.com/r/stocks/top.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    params = {'limit': 1, 't': 'day'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Reddit API 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'children' in data['data']:
                print("✅ Reddit API 访问正常")
                return True
            else:
                print("❌ Reddit API 响应格式异常")
                return False
        else:
            print(f"❌ Reddit API 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Reddit API 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Reddit Bot 简化测试")
    print("=" * 40)
    
    # 检查环境变量
    print("🔍 检查环境变量...")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print(f"TELEGRAM_BOT_TOKEN: {'✅' if bot_token else '❌'}")
    print(f"CHAT_ID: {'✅' if chat_id else '❌'}")
    print(f"GEMINI_API_KEY: {'✅' if gemini_key else '⚠️ (可选)'}")
    
    if not bot_token or not chat_id:
        print("❌ 必需的环境变量未设置")
        sys.exit(1)
    
    # 测试简单消息
    message_ok = test_simple_message()
    
    # 测试 Reddit API
    reddit_ok = test_reddit_simple()
    
    print("\n" + "=" * 40)
    print("📊 测试结果:")
    print(f"简单消息: {'✅ 成功' if message_ok else '❌ 失败'}")
    print(f"Reddit API: {'✅ 成功' if reddit_ok else '❌ 失败'}")
    
    if message_ok and reddit_ok:
        print("\n🎉 基本功能正常！问题可能在复杂逻辑中。")
        return True
    else:
        print("\n⚠️ 发现问题，需要进一步调试。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
