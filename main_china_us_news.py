#!/usr/bin/env python3
"""
中美关系专题新闻 Telegram Bot
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
import time
import random
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

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

def setup_gemini():
    """设置 Gemini API"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        log("⚠️ 未设置 GEMINI_API_KEY，将使用基础功能")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        log("✅ Gemini API 配置成功")
        return model
    except Exception as e:
        log(f"❌ Gemini API 配置失败: {e}")
        return None

def escape_html(text: str) -> str:
    """转义 Telegram HTML 模式需要的字符"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )

def sanitize_text(text: str) -> str:
    """移除无关符号"""
    if not text:
        return ""
    cleaned = text.replace("*", "").replace("`", "")
    cleaned = cleaned.strip('"').strip("'")
    cleaned = cleaned.replace("\\n", " ").replace("\n", " ")
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()

def clean_ai_artifacts(text: str) -> str:
    """清理 AI 输出中的说明性前缀/噪声"""
    if not text:
        return ""
    cleaned = text
    patterns = [
        r"^以下是.*?中文翻译[:：]\s*",
        r"^翻译[一二三]?[：:]\s*",
        r"^解释[：:]\s*.*$",
        r"^或[者]?[：:]\s*",
        r"^注[：:]\s*",
    ]
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE|re.MULTILINE)
    cleaned = re.sub(r"（[^）]*?(请删除|不需要|解释|示例)[^）]*?）", "", cleaned)
    cleaned = re.sub(r"\([^)]*?(please remove|example|explanation)[^)]*?\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = sanitize_text(cleaned)
    return cleaned

def summarize_text(model, title: str, content: str, fallback_chars: int = 90) -> str:
    """生成简短摘要"""
    raw = (content or "")
    if not raw and title:
        raw = title
    if model:
        try:
            prompt = f"请用简体中文将以下新闻概述为最多60字，保留关键信息，不要加前后缀：\n标题：{title}\n内容：{content}"
            resp = model.generate_content(prompt)
            summary = (resp.text or "").strip()
            summary = summary.strip('"').strip("'")
            if len(summary) > 60:
                summary = summary[:57] + "..."
            return summary
        except Exception:
            pass
    clean = raw.replace("\n", " ").strip()
    if len(clean) > fallback_chars:
        return clean[:fallback_chars - 3] + "..."
    return clean

def translate_with_gemini(model, text):
    """使用 Gemini 翻译文本"""
    if not model:
        return text
    
    try:
        prompt = f"请将以下英文新闻翻译成中文，保持专业性和准确性：\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        log(f"⚠️ 翻译失败: {e}")
        return text

def fetch_gnews_china_us(api_key, max_articles=8):
    """从 GNews API 获取中美关系新闻"""
    log("📡 获取中美关系新闻...")
    
    try:
        # 搜索中美关系相关关键词
        search_queries = [
            "China US relations",
            "China trade war",
            "China tariffs",
            "China technology ban",
            "China congress bill",
            "China policy",
            "China investment",
            "China semiconductor"
        ]
        
        all_articles = []
        
        for query in search_queries:
            url = "https://gnews.io/api/v4/search"
            params = {
                'token': api_key,
                'q': query,
                'lang': 'en',
                'country': 'us',
                'max': 2
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                for article in articles:
                    all_articles.append({
                        'title': article.get('title', ''),
                        'content': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'GNews'),
                        'time': article.get('publishedAt', ''),
                        'url': article.get('url', ''),
                        'type': 'gnews'
                    })
            
            time.sleep(1)  # 避免 API 限制
        
        # 去重
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get('title', '').lower()
            if title not in seen_titles and len(title) > 10:
                seen_titles.add(title)
                unique_articles.append(article)
        
        log(f"✅ GNews 中美关系: {len(unique_articles)} 条新闻")
        return unique_articles[:max_articles]
        
    except Exception as e:
        log(f"❌ GNews 中美关系获取失败: {e}")
        return []

def fetch_rss_china_us():
    """获取 RSS 中美关系新闻"""
    log("📡 获取 RSS 中美关系新闻...")
    
    rss_sources = [
        ("NPR News", "http://www.npr.org/rss/rss.php?id=1001"),
        ("HuffPost World", "https://www.huffpost.com/section/world-news/feed"),
        ("FOX News", "http://feeds.foxnews.com/foxnews/latest"),
        ("NYT Top Stories", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
        ("CNN International", "http://rss.cnn.com/rss/edition.rss"),
        ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss"),
    ]
    
    all_news = []
    
    # 中美关系关键词
    china_us_keywords = [
        'china', 'chinese', 'beijing', 'beijing', 'taiwan', 'taiwanese',
        'trade war', 'tariff', 'semiconductor', 'chip', 'huawei', 'tiktok',
        'congress', 'senate', 'house', 'bill', 'proposal', 'legislation',
        'biden china', 'trump china', 'us china', 'america china',
        'investment', 'sanction', 'export', 'import', 'manufacturing',
        'technology', 'ai', 'artificial intelligence', '5g', 'cyber',
        'military', 'defense', 'navy', 'air force', 'pacific'
    ]
    
    for name, url in rss_sources:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                items = root.findall('.//item')
                
                for item in items[:5]:  # 每个源最多5条
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    description_elem = item.find('description')
                    pub_date_elem = item.find('pubDate')
                    
                    if title_elem is not None and link_elem is not None:
                        title = title_elem.text
                        link = link_elem.text
                        description = description_elem.text if description_elem is not None else ""
                        pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                        
                        # 检查是否包含中美关系关键词
                        content = f"{title} {description}".lower()
                        
                        if any(keyword.lower() in content for keyword in china_us_keywords):
                            all_news.append({
                                'title': title,
                                'content': description,
                                'source': name,
                                'time': pub_date,
                                'url': link,
                                'type': 'rss'
                            })
            
            time.sleep(1)  # 避免请求过快
            
        except Exception as e:
            log(f"❌ {name}: {e}")
    
    log(f"📊 RSS 中美关系: {len(all_news)} 条新闻")
    return all_news

def search_china_us_with_gemini(model):
    """使用 Gemini 搜索中美关系新闻"""
    if not model:
        return []
    
    search_queries = [
        "China US trade relations latest news",
        "US Congress China bills proposals 2025",
        "China technology restrictions US policy",
        "China Taiwan relations US stance",
        "China semiconductor ban US companies",
        "China investment restrictions US",
        "China military tensions US response"
    ]
    
    all_news = []
    
    for query in search_queries:
        try:
            log(f"🔍 Gemini 搜索: {query}")
            
            prompt = f"""
            请搜索关于"{query}"的最新新闻，重点关注：
            1. 美国国会议员的新提案
            2. 中美贸易政策变化
            3. 技术限制和制裁
            4. 台湾问题相关动态
            5. 军事和外交政策
            
            请提供 2 条最重要的新闻，每条包含：
            - 标题
            - 简要内容
            - 来源
            - 时间
            
            格式为JSON：
            [
                {{
                    "title": "新闻标题",
                    "content": "新闻内容摘要",
                    "source": "新闻来源",
                    "time": "发布时间",
                    "url": "新闻链接（如果有）"
                }}
            ]
            """
            
            response = model.generate_content(prompt)
            result_text = response.text
            
            try:
                start_idx = result_text.find('[')
                end_idx = result_text.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    json_text = result_text[start_idx:end_idx]
                    news_data = json.loads(json_text)
                    all_news.extend(news_data)
                    log(f"✅ Gemini 搜索成功: {len(news_data)} 条新闻")
                else:
                    log("⚠️ Gemini 返回格式异常")
            except json.JSONDecodeError as e:
                log(f"⚠️ JSON 解析失败: {e}")
            
            time.sleep(2)  # 避免 API 限制
            
        except Exception as e:
            log(f"❌ Gemini 搜索失败: {e}")
    
    return all_news

def categorize_news(news_items):
    """对新闻进行分类"""
    categories = {
        'congress_bills': [],  # 国会提案
        'trade_policy': [],    # 贸易政策
        'technology': [],      # 技术限制
        'taiwan': [],          # 台湾问题
        'military': [],        # 军事外交
        'other': []            # 其他
    }
    
    for news in news_items:
        title = news.get('title', '').lower()
        content = news.get('content', '').lower()
        text = f"{title} {content}"
        
        if any(word in text for word in ['congress', 'senate', 'house', 'bill', 'proposal', 'legislation', 'committee']):
            categories['congress_bills'].append(news)
        elif any(word in text for word in ['trade', 'tariff', 'import', 'export', 'commerce', 'economic']):
            categories['trade_policy'].append(news)
        elif any(word in text for word in ['technology', 'semiconductor', 'chip', 'ai', 'artificial intelligence', '5g', 'cyber', 'huawei', 'tiktok']):
            categories['technology'].append(news)
        elif any(word in text for word in ['taiwan', 'taiwanese', 'tsai', 'cross-strait']):
            categories['taiwan'].append(news)
        elif any(word in text for word in ['military', 'defense', 'navy', 'air force', 'pacific', 'south china sea']):
            categories['military'].append(news)
        else:
            categories['other'].append(news)
    
    return categories

def send_telegram_message(bot_token, chat_id, text):
    """发送 Telegram 消息"""
    log("📤 发送 Telegram 消息...")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
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
    log("🚀 中美关系专题新闻 Bot 启动")
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
        
        # 2. 设置 Gemini API
        model = setup_gemini()
        
        # 3. 获取中美关系新闻
        all_news = []
        
        # GNews API
        gnews_key = os.getenv('GNEWS_API_KEY')
        if gnews_key:
            gnews_items = fetch_gnews_china_us(gnews_key, 8)
            all_news.extend(gnews_items)
        
        # RSS 新闻
        rss_items = fetch_rss_china_us()
        all_news.extend(rss_items)
        
        # Gemini 搜索
        if model:
            gemini_items = search_china_us_with_gemini(model)
            all_news.extend(gemini_items)
        
        # 去重
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title = news.get('title', '').lower()
            if title not in seen_titles and len(title) > 10:
                seen_titles.add(title)
                unique_news.append(news)
        
        # 分类
        categories = categorize_news(unique_news)
        
        # 4. 格式化消息
        timestamp = get_beijing_timestamp()
        
        if unique_news:
            message_lines = []
            message_lines.append("🇺🇸🇨🇳 中美关系专题简报")
            message_lines.append("")
            message_lines.append(f"📅 更新时间: {timestamp} (UTC+8)")
            message_lines.append(f"📊 今日收集 {len(unique_news)} 条中美关系新闻")
            message_lines.append("")
            
            # 按类别显示新闻
            category_names = {
                'congress_bills': '🏛️ 国会提案与立法',
                'trade_policy': '💰 贸易政策',
                'technology': '🔬 技术限制',
                'taiwan': '🏝️ 台湾问题',
                'military': '⚔️ 军事外交',
                'other': '📰 其他要闻'
            }
            
            for category, name in category_names.items():
                items = categories[category]
                if items:
                    message_lines.append(f"<b>{name}</b>")
                    
                    for i, news in enumerate(items[:3], 1):  # 每类最多3条
                        title = news.get('title', '无标题')
                        content = news.get('content', '')
                        source = news.get('source', '未知来源')
                        url = news.get('url', '')
                        
                        # 翻译标题与摘要
                        zh_title = translate_with_gemini(model, title) if model else title
                        summary = summarize_text(model, title, content)
                        zh_title = clean_ai_artifacts(sanitize_text(zh_title))
                        summary = clean_ai_artifacts(sanitize_text(summary))
                        zh_title = escape_html(zh_title)
                        summary = escape_html(summary)
                        
                        if len(zh_title) > 80:
                            zh_title = zh_title[:77] + "..."
                        
                        if url:
                            message_lines.append(f"{i}️⃣ <a href=\"{escape_html(url)}\">{zh_title}</a>")
                        else:
                            message_lines.append(f"{i}️⃣ {zh_title}")
                        if summary:
                            message_lines.append(f"📝 摘要: {summary}")
                        message_lines.append(f"📰 来源: {escape_html(sanitize_text(source))}")
                        message_lines.append("")
            
            message_lines.append("📎 来源：多家权威媒体 + AI 摘要")
            message_text = "\n".join(message_lines)
            
            # 安全长度控制
            if len(message_text) > 4000:
                message_text = message_text[:3997] + "..."
            message = message_text
        else:
            message = f"""🇺🇸🇨🇳 中美关系专题简报

📅 更新时间: {timestamp} (UTC+8)

⚠️ 今日中美关系新闻源暂时不可用
🤖 请稍后查看新闻网站获取最新资讯

💡 我们正在努力恢复服务..."""
        
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
