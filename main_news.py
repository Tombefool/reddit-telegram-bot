#!/usr/bin/env python3
"""
新闻版 Reddit Telegram Bot - 使用多个新闻 RSS 源
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
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

def fetch_news_from_rss(name, url, max_items=3):
    """从单个 RSS 源获取新闻"""
    log(f"  获取 {name}...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('.//item')
            
            # 财经关键词
            finance_keywords = ['stock', 'market', 'economy', 'finance', 'bitcoin', 'crypto', 'trading', 'investment', 'earnings', 'revenue', 'business', 'dollar', 'inflation', 'fed', 'federal', 'nasdaq', 'dow', 's&p', 'sp500']
            
            news_items = []
            for item in items[:max_items*2]:  # 获取更多以便筛选
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                
                if title_elem is not None and link_elem is not None:
                    title = title_elem.text
                    link = link_elem.text
                    description = description_elem.text if description_elem is not None else ""
                    pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                    
                    # 检查是否包含财经关键词
                    title_lower = title.lower()
                    desc_lower = description.lower()
                    
                    is_finance = any(keyword in title_lower or keyword in desc_lower for keyword in finance_keywords)
                    
                    if is_finance:
                        news_items.append({
                            'title': title,
                            'link': link,
                            'description': description,
                            'pub_date': pub_date,
                            'source': name
                        })
                        
                        if len(news_items) >= max_items:
                            break
            
            log(f"  ✅ {name}: {len(news_items)} 个财经新闻")
            return news_items
            
        else:
            log(f"  ❌ {name}: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        log(f"  ❌ {name}: {e}")
        return []

def fetch_all_news():
    """获取所有新闻源的财经新闻"""
    log("📡 开始获取财经新闻...")
    
    # 新闻源配置
    news_sources = [
        ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", 3),
        ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", 2),
        ("Financial Times", "https://www.ft.com/rss/home", 2),
        ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml", 2),
        ("CNN Business", "http://rss.cnn.com/rss/money_latest.rss", 1),
    ]
    
    all_news = []
    
    for name, url, max_items in news_sources:
        news_items = fetch_news_from_rss(name, url, max_items)
        all_news.extend(news_items)
        
        # 随机延迟 1-3 秒
        delay = random.uniform(1, 3)
        time.sleep(delay)
    
    # 按时间排序（最新的在前）
    all_news.sort(key=lambda x: x.get('pub_date', ''), reverse=True)
    
    log(f"📊 总共获取 {len(all_news)} 个财经新闻")
    return all_news

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
    log("🚀 新闻版 Reddit Telegram Bot 启动")
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
        
        # 2. 获取新闻
        news_items = fetch_all_news()
        
        # 3. 格式化消息
        timestamp = get_beijing_timestamp()
        
        if news_items:
            message = f"""🔔 每日财经要闻

📊 今日获取到 {len(news_items)} 条财经新闻

"""
            
            for i, news in enumerate(news_items[:8], 1):  # 最多8条新闻
                title = news['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
                if len(title) > 80:
                    title = title[:77] + "..."
                
                message += f"{i}️⃣ [{title}]({news['link']})\n"
                message += f"📰 来源: {news['source']}\n\n"
            
            message += f"📅 更新时间: {timestamp} (UTC+8)\n"
            message += "🤖 由多个权威新闻源提供"
        else:
            message = f"""🔔 每日财经要闻

📅 更新时间: {timestamp} (UTC+8)

⚠️ 今日新闻源暂时不可用
🤖 请稍后查看新闻网站获取最新资讯

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
