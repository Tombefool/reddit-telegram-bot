#!/usr/bin/env python3
"""
Render 测试脚本 - 最简单的版本
"""

import os
import requests
from datetime import datetime, timedelta

def get_beijing_timestamp():
    """获取北京时间戳"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time.strftime("%Y-%m-%d %H:%M")

def main():
    print("🚀 Render 测试脚本启动")
    print("=" * 40)
    
    # 检查环境变量
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    print(f"TELEGRAM_BOT_TOKEN: {'✅ 已设置' if bot_token else '❌ 未设置'}")
    print(f"CHAT_ID: {'✅ 已设置' if chat_id else '❌ 未设置'}")
    
    if not bot_token or not chat_id:
        print("❌ 缺少必需的环境变量")
        return
    
    # 发送测试消息
    test_message = f"""🤖 Render 测试成功！

📅 时间: {get_beijing_timestamp()}
✅ 环境变量: 正常
✅ Python 脚本: 运行正常
✅ Telegram API: 连接正常

🎉 Reddit Bot 基础功能已就绪！

下一步：配置 Reddit API 访问"""
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        print("📤 发送测试消息...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ 测试消息发送成功！")
                print("🎉 Render 部署测试完成！")
            else:
                print(f"❌ Telegram API 错误: {result.get('description')}")
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    main()
