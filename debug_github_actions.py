#!/usr/bin/env python3
"""
GitHub Actions 故障诊断脚本
帮助诊断 Reddit Telegram Bot 在 GitHub Actions 中的问题
"""

import os
import sys
import requests
from datetime import datetime

def check_environment():
    """检查环境变量"""
    print("🔍 检查环境变量...")
    
    required_vars = ['TELEGRAM_BOT_TOKEN', 'CHAT_ID']
    optional_vars = ['GEMINI_API_KEY']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 已设置 ({value[:10]}...)")
        else:
            print(f"❌ {var}: 未设置")
            return False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 已设置 ({value[:10]}...)")
        else:
            print(f"⚠️ {var}: 未设置 (可选)")
    
    return True

def check_telegram_api():
    """检查 Telegram API"""
    print("\n🔍 检查 Telegram API...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Telegram 配置不完整")
        return False
    
    try:
        # 检查 Bot 状态
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                print(f"✅ Bot 状态正常: @{bot_info['result']['username']}")
            else:
                print(f"❌ Bot 状态异常: {bot_info}")
                return False
        else:
            print(f"❌ Bot API 请求失败: {response.status_code}")
            return False
        
        # 测试发送消息
        test_message = f"🤖 GitHub Actions 测试 - {datetime.now().strftime('%H:%M:%S')}"
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': test_message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ Telegram 消息发送成功")
                return True
            else:
                print(f"❌ Telegram 消息发送失败: {result.get('description', '未知错误')}")
                return False
        else:
            print(f"❌ Telegram API 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram API 检查失败: {e}")
        return False

def check_reddit_api():
    """检查 Reddit API"""
    print("\n🔍 检查 Reddit API...")
    
    test_subreddit = "stocks"
    url = f"https://www.reddit.com/r/{test_subreddit}/top.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    params = {'limit': 1, 't': 'day'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'children' in data['data']:
                print("✅ Reddit API 访问正常")
                return True
            else:
                print("❌ Reddit API 响应格式异常")
                print(f"响应内容: {data}")
                return False
        else:
            print(f"❌ Reddit API 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Reddit API 检查失败: {e}")
        return False

def check_gemini_api():
    """检查 Gemini API"""
    print("\n🔍 检查 Gemini API...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY 未设置，跳过检查")
        return True
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        test_prompt = "请用中文简单说一句话测试API连接。"
        response = model.generate_content(test_prompt)
        
        if response.text:
            print("✅ Gemini API 连接成功")
            return True
        else:
            print("❌ Gemini API 返回空响应")
            return False
            
    except ImportError:
        print("❌ google-generativeai 库未安装")
        return False
    except Exception as e:
        print(f"❌ Gemini API 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 GitHub Actions 故障诊断")
    print("=" * 50)
    
    # 检查各项配置
    env_ok = check_environment()
    telegram_ok = check_telegram_api() if env_ok else False
    reddit_ok = check_reddit_api()
    gemini_ok = check_gemini_api()
    
    print("\n" + "=" * 50)
    print("📊 诊断结果总结:")
    print(f"环境变量: {'✅ 正常' if env_ok else '❌ 异常'}")
    print(f"Telegram API: {'✅ 正常' if telegram_ok else '❌ 异常'}")
    print(f"Reddit API: {'✅ 正常' if reddit_ok else '❌ 异常'}")
    print(f"Gemini API: {'✅ 正常' if gemini_ok else '❌ 异常'}")
    
    if env_ok and telegram_ok and reddit_ok and gemini_ok:
        print("\n🎉 所有检查通过！问题可能在代码逻辑中。")
    else:
        print("\n⚠️ 发现问题，请检查上述异常项目。")
    
    return env_ok and telegram_ok and reddit_ok and gemini_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
