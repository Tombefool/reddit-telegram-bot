#!/usr/bin/env python3
"""
最小化测试脚本 - 用于快速定位 GitHub Actions 问题
"""

import os
import sys
import requests
from datetime import datetime

def main():
    print("🚀 最小化测试开始")
    print("=" * 40)
    
    # 1. 检查环境变量
    print("📋 检查环境变量...")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print(f"TELEGRAM_BOT_TOKEN: {'✅ 已设置' if bot_token else '❌ 未设置'}")
    print(f"CHAT_ID: {'✅ 已设置' if chat_id else '❌ 未设置'}")
    print(f"GEMINI_API_KEY: {'✅ 已设置' if gemini_key else '⚠️ 未设置 (可选)'}")
    
    if not bot_token or not chat_id:
        print("❌ 缺少必需的环境变量")
        sys.exit(1)
    
    # 2. 测试 Telegram API
    print("\n📤 测试 Telegram API...")
    try:
        # 测试 Bot 状态
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        print(f"Bot API 状态码: {response.status_code}")
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ Bot 状态正常: @{bot_info['result']['username']}")
            else:
                print(f"❌ Bot API 错误: {bot_info}")
                sys.exit(1)
        else:
            print(f"❌ Bot API 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            sys.exit(1)
        
        # 检查是否启用测试消息发送
        send_test_message = os.getenv('SEND_TEST_MESSAGE', 'false').lower() == 'true'
        
        if send_test_message:
            # 发送测试消息
            test_message = f"""🤖 GitHub Actions 测试成功！

📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ 环境变量: 正常
✅ Telegram API: 正常
✅ 最小化测试: 通过

🎉 Reddit Bot 基础功能正常！"""
            
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': test_message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                },
                timeout=30
            )
            
            print(f"发送消息状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ 测试消息发送成功")
                else:
                    print(f"❌ 发送消息失败: {result.get('description')}")
            else:
                print(f"❌ 发送消息 HTTP 错误: {response.status_code}")
        else:
            print("ℹ️ 测试消息发送已禁用（设置 SEND_TEST_MESSAGE=true 启用）")
        
        print("🎉 最小化测试完成！")
        return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
