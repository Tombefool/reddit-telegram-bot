#!/usr/bin/env python3
"""
综合新闻版 Telegram Bot - 财经 + 政治新闻，中文推送
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

def translate_keywords_to_chinese(keywords):
    """将英文关键词翻译为中文"""
    translation_map = {
        'stock': '股票',
        'market': '市场',
        'economy': '经济',
        'finance': '金融',
        'bitcoin': '比特币',
        'crypto': '加密货币',
        'trading': '交易',
        'investment': '投资',
        'earnings': '收益',
        'revenue': '收入',
        'business': '商业',
        'dollar': '美元',
        'inflation': '通胀',
        'fed': '美联储',
        'federal': '联邦',
        'nasdaq': '纳斯达克',
        'dow': '道琼斯',
        'sp500': '标普500',
        'trump': '特朗普',
        'biden': '拜登',
        'president': '总统',
        'election': '选举',
        'congress': '国会',
        'senate': '参议院',
        'house': '众议院',
        'policy': '政策',
        'government': '政府',
        'china': '中国',
        'russia': '俄罗斯',
        'ukraine': '乌克兰',
        'israel': '以色列',
        'palestine': '巴勒斯坦',
        'trade': '贸易',
        'tariff': '关税',
        'sanction': '制裁',
        'war': '战争',
        'conflict': '冲突',
        'diplomacy': '外交',
        'summit': '峰会',
        'g7': '七国集团',
        'g20': '二十国集团',
        'nato': '北约',
        'un': '联合国',
        'truth social': 'Truth Social',
        'twitter': '推特',
        'x': 'X平台'
    }
    
    chinese_keywords = []
    for keyword in keywords:
        chinese_keywords.append(keyword)
        if keyword.lower() in translation_map:
            chinese_keywords.append(translation_map[keyword.lower()])
    
    return chinese_keywords

def fetch_news_from_rss(name, url, max_items=3, news_type="财经"):
    """从单个 RSS 源获取新闻"""
    log(f"  获取 {name} ({news_type})...")
    
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
            
            # 政治关键词
            politics_keywords = ['trump', 'biden', 'president', 'election', 'congress', 'senate', 'house', 'policy', 'government', 'china', 'russia', 'ukraine', 'israel', 'palestine', 'trade', 'tariff', 'sanction', 'war', 'conflict', 'diplomacy', 'summit', 'g7', 'g20', 'nato', 'un', 'truth social', 'twitter', 'x']
            
            # 根据新闻类型选择关键词
            if news_type == "财经":
                keywords = finance_keywords
            else:
                keywords = politics_keywords
            
            # 添加中文关键词
            keywords.extend(translate_keywords_to_chinese(keywords))
            
            news_items = []
            for item in items[:max_items*3]:  # 获取更多以便筛选
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                
                if title_elem is not None and link_elem is not None:
                    title = title_elem.text
                    link = link_elem.text
                    description = description_elem.text if description_elem is not None else ""
                    pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                    
                    # 检查是否包含相关关键词
                    title_lower = title.lower() if title else ""
                    desc_lower = description.lower() if description else ""
                    
                    is_relevant = any(keyword.lower() in title_lower or keyword.lower() in desc_lower for keyword in keywords)
                    
                    if is_relevant:
                        news_items.append({
                            'title': title,
                            'link': link,
                            'description': description,
                            'pub_date': pub_date,
                            'source': name,
                            'type': news_type
                        })
                        
                        if len(news_items) >= max_items:
                            break
            
            log(f"  ✅ {name}: {len(news_items)} 个{news_type}新闻")
            return news_items
            
        else:
            log(f"  ❌ {name}: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        log(f"  ❌ {name}: {e}")
        return []

def fetch_all_news():
    """获取所有新闻源的财经和政治新闻"""
    log("📡 开始获取综合新闻...")
    
    # 新闻源配置 - 财经类
    finance_sources = [
        ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", 3),
        ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", 2),
        ("Financial Times", "https://www.ft.com/rss/home", 2),
        ("WSJ World News", "https://feeds.a.dj.com/rss/RSSWorldNews.xml", 2),
    ]
    
    # 新闻源配置 - 政治类
    politics_sources = [
        ("NYT Top Stories", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", 3),
        ("CNN International", "http://rss.cnn.com/rss/edition.rss", 2),
        ("Washington Post World", "http://feeds.washingtonpost.com/rss/world", 2),
        ("HuffPost World", "https://www.huffpost.com/section/world-news/feed", 2),
        ("FOX News", "http://feeds.foxnews.com/foxnews/latest", 2),
        ("LA Times World", "https://www.latimes.com/world-nation/rss2.0.xml", 1),
    ]
    
    all_news = []
    
    # 获取财经新闻
    log("💰 获取财经新闻...")
    for name, url, max_items in finance_sources:
        news_items = fetch_news_from_rss(name, url, max_items, "财经")
        all_news.extend(news_items)
        time.sleep(random.uniform(1, 2))
    
    # 获取政治新闻
    log("🏛️ 获取政治新闻...")
    for name, url, max_items in politics_sources:
        news_items = fetch_news_from_rss(name, url, max_items, "政治")
        all_news.extend(news_items)
        time.sleep(random.uniform(1, 2))
    
    # 按时间排序（最新的在前）
    all_news.sort(key=lambda x: x.get('pub_date', ''), reverse=True)
    
    log(f"📊 总共获取 {len(all_news)} 个新闻")
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
    log("🚀 综合新闻版 Telegram Bot 启动")
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
            # 分类统计
            finance_count = len([n for n in news_items if n['type'] == '财经'])
            politics_count = len([n for n in news_items if n['type'] == '政治'])
            
            message = f"""🔔 每日综合要闻

📊 今日获取到 {len(news_items)} 条新闻
💰 财经新闻: {finance_count} 条
🏛️ 政治新闻: {politics_count} 条

"""
            
            # 按类型分组显示
            current_type = None
            item_num = 1
            
            for news in news_items[:12]:  # 最多12条新闻
                if news['type'] != current_type:
                    current_type = news['type']
                    if current_type == '财经':
                        message += "💰 **财经要闻**\n"
                    else:
                        message += "🏛️ **政治要闻**\n"
                
                title = news['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
                if len(title) > 80:
                    title = title[:77] + "..."
                
                message += f"{item_num}️⃣ [{title}]({news['link']})\n"
                message += f"📰 来源: {news['source']}\n\n"
                item_num += 1
            
            message += f"📅 更新时间: {timestamp} (UTC+8)\n"
            message += "🤖 由多个权威新闻源提供"
        else:
            message = f"""🔔 每日综合要闻

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
