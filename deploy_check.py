#!/usr/bin/env python3
"""
Reddit Telegram Bot 部署验证脚本
检查所有配置是否正确
"""

import os
import requests
from dotenv import load_dotenv

def check_telegram_config():
    """检查 Telegram 配置"""
    print("🔍 检查 Telegram 配置...")
    
    bot_token = "8277624200:AAFbcpacMXFq5Mesj4agPO95-o5zuKWifpQ"
    chat_id = "8160481050"
    
    try:
        # 检查 Bot 状态
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                print(f"✅ Bot 状态正常: @{bot_info['result']['username']}")
            else:
                print("❌ Bot 状态异常")
                return False
        else:
            print(f"❌ Bot API 请求失败: {response.status_code}")
            return False
        
        # 测试发送消息
        test_message = "🤖 Reddit Bot 部署验证测试"
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': test_message
            }
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
        print(f"❌ Telegram 配置检查失败: {e}")
        return False

def check_gemini_config():
    """检查 Gemini API 配置"""
    print("\n🔍 检查 Gemini API 配置...")
    
    api_key = "AIzaSyBmEIjAe1LQAudfj-rRr5QDj0zcCpZpg2Y"
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        test_prompt = "请用中文简单说一句话测试API连接。"
        response = model.generate_content(test_prompt)
        
        if response.text:
            print("✅ Gemini API 连接成功")
            print(f"   测试响应: {response.text}")
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

def check_reddit_access():
    """检查 Reddit API 访问"""
    print("\n🔍 检查 Reddit API 访问...")
    
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
                return False
        else:
            print(f"❌ Reddit API 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Reddit API 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Reddit Telegram Bot 部署验证")
    print("=" * 50)
    
    # 检查各项配置
    telegram_ok = check_telegram_config()
    gemini_ok = check_gemini_config()
    reddit_ok = check_reddit_access()
    
    print("\n" + "=" * 50)
    print("📊 验证结果总结:")
    print(f"Telegram 配置: {'✅ 正常' if telegram_ok else '❌ 异常'}")
    print(f"Gemini API: {'✅ 正常' if gemini_ok else '❌ 异常'}")
    print(f"Reddit API: {'✅ 正常' if reddit_ok else '❌ 异常'}")
    
    if telegram_ok and gemini_ok and reddit_ok:
        print("\n🎉 所有配置验证通过！可以安全部署到 GitHub Actions。")
        print("\n📋 下一步:")
        print("1. 创建 GitHub 仓库")
        print("2. 推送代码到 GitHub")
        print("3. 配置 GitHub Secrets")
        print("4. 启用 GitHub Actions")
        print("5. 手动触发测试")
    else:
        print("\n⚠️ 部分配置存在问题，请检查后再部署。")
    
    return telegram_ok and gemini_ok and reddit_ok

if __name__ == "__main__":
    main()
