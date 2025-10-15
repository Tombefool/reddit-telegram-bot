#!/usr/bin/env python3
"""
综合版新闻 Telegram Bot - 包含中美关系专题
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

def fetch_all_news_sources(model):
    """获取所有新闻源"""
    log("📝 生成综合新闻简报...")
    
    all_news = []
    
    # 1. GNews API - 通用新闻
    gnews_key = os.getenv('GNEWS_API_KEY')
    if gnews_key:
        try:
            url = "https://gnews.io/api/v4/top-headlines"
            params = {
                'token': gnews_key,
                'lang': 'en',
                'country': 'us',
                'max': 5
            }
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get('articles', []):
                    all_news.append({
                        'title': article.get('title', ''),
                        'content': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'GNews'),
                        'time': article.get('publishedAt', ''),
                        'url': article.get('url', ''),
                        'type': 'general'
                    })
            log(f"✅ GNews 通用: {len([n for n in all_news if n['type'] == 'general'])} 条")
        except Exception as e:
            log(f"❌ GNews 通用失败: {e}")
    
    # 2. GNews API - 中美关系专题
    if gnews_key:
        try:
            china_us_queries = ["China US relations", "China trade war", "China congress bill"]
            for query in china_us_queries:
                url = "https://gnews.io/api/v4/search"
                params = {
                    'token': gnews_key,
                    'q': query,
                    'lang': 'en',
                    'country': 'us',
                    'max': 2
                }
                response = requests.get(url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        all_news.append({
                            'title': article.get('title', ''),
                            'content': article.get('description', ''),
                            'source': article.get('source', {}).get('name', 'GNews'),
                            'time': article.get('publishedAt', ''),
                            'url': article.get('url', ''),
                            'type': 'china_us'
                        })
                time.sleep(1)
            log(f"✅ GNews 中美关系: {len([n for n in all_news if n['type'] == 'china_us'])} 条")
        except Exception as e:
            log(f"❌ GNews 中美关系失败: {e}")
    
    # 3. RSS 新闻源
    rss_sources = [
        ("NPR News", "http://www.npr.org/rss/rss.php?id=1001"),
        ("HuffPost World", "https://www.huffpost.com/section/world-news/feed"),
        ("FOX News", "http://feeds.foxnews.com/foxnews/latest"),
        ("NYT Top Stories", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
        ("CNN International", "http://rss.cnn.com/rss/edition.rss"),
        ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss"),
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
                
                for item in items[:2]:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    description_elem = item.find('description')
                    pub_date_elem = item.find('pubDate')
                    
                    if title_elem is not None and link_elem is not None:
                        title = title_elem.text
                        link = link_elem.text
                        description = description_elem.text if description_elem is not None else ""
                        pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                        
                        # 关键词筛选
                        keywords = ['trump', 'biden', 'president', 'election', 'china', 'russia', 'ukraine', 'israel', 'palestine', 'economy', 'market', 'trade', 'war', 'conflict', 'politics', 'government', 'congress', 'senate', 'bill', 'proposal']
                        content = f"{title} {description}".lower()
                        
                        if any(keyword in content for keyword in keywords):
                            news_type = 'china_us' if any(word in content for word in ['china', 'chinese', 'beijing', 'taiwan', 'trade war', 'tariff', 'semiconductor', 'huawei', 'tiktok']) else 'general'
                            all_news.append({
                                'title': title,
                                'content': description,
                                'source': name,
                                'time': pub_date,
                                'url': link,
                                'type': news_type
                            })
            
            time.sleep(1)
        except Exception as e:
            log(f"❌ {name}: {e}")
    
    # 4. Gemini 搜索补充
    if model:
        search_queries = [
            "Trump latest news today",
            "US politics today",
            "China US relations latest",
            "International news key developments"
        ]
        
        for query in search_queries:
            try:
                prompt = f"请搜索关于'{query}'的最新新闻，提供2条最重要的新闻，格式为JSON：[{{\"title\": \"标题\", \"content\": \"内容\", \"source\": \"来源\", \"time\": \"时间\", \"url\": \"链接\"}}]"
                response = model.generate_content(prompt)
                result_text = response.text
                
                try:
                    start_idx = result_text.find('[')
                    end_idx = result_text.rfind(']') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_text = result_text[start_idx:end_idx]
                        news_data = json.loads(json_text)
                        for news in news_data:
                            news['type'] = 'china_us' if 'china' in query.lower() else 'general'
                        all_news.extend(news_data)
                except:
                    pass
                
                time.sleep(2)
            except Exception as e:
                log(f"❌ Gemini 搜索失败: {e}")
    
    # 去重和排序
    seen_titles = set()
    unique_news = []
    for news in all_news:
        title = news.get('title', '').lower()
        if title not in seen_titles and len(title) > 10:
            seen_titles.add(title)
            unique_news.append(news)
    
    unique_news.sort(key=lambda x: x.get('time', ''), reverse=True)
    
    log(f"📊 总共收集 {len(unique_news)} 条新闻")
    return unique_news

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
    log("🚀 综合版新闻 Telegram Bot 启动")
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
        
        # 3. 获取所有新闻
        all_news = fetch_all_news_sources(model)
        
        # 4. 分类新闻
        trump_news = [n for n in all_news if 'trump' in n.get('title', '').lower() or 'trump' in n.get('content', '').lower()]
        china_us_news = [n for n in all_news if n.get('type') == 'china_us' and n not in trump_news]
        other_news = [n for n in all_news if n not in trump_news and n not in china_us_news]
        
        # 5. 格式化消息
        timestamp = get_beijing_timestamp()
        
        if all_news:
            message_lines = []
            message_lines.append("🌍 每日综合要闻简报")
            message_lines.append("")
            message_lines.append(f"📅 更新时间: {timestamp} (UTC+8)")
            message_lines.append(f"📊 今日收集 {len(all_news)} 条重要新闻")
            message_lines.append("")
            
            # 特朗普动态
            if trump_news:
                message_lines.append("🔥 <b>特朗普总统动态</b>")
                for i, news in enumerate(trump_news[:3], 1):
                    title = news.get('title', '无标题')
                    content = news.get('content', '')
                    source = news.get('source', '未知来源')
                    url = news.get('url', '')
                    
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
            
            # 中美关系专题
            if china_us_news:
                message_lines.append("🇺🇸🇨🇳 <b>中美关系专题</b>")
                for i, news in enumerate(china_us_news[:4], 1):
                    title = news.get('title', '无标题')
                    content = news.get('content', '')
                    source = news.get('source', '未知来源')
                    url = news.get('url', '')
                    
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
            
            # 其他国际要闻
            if other_news:
                message_lines.append("🌍 <b>其他国际要闻</b>")
                for i, news in enumerate(other_news[:4], 1):
                    title = news.get('title', '无标题')
                    content = news.get('content', '')
                    source = news.get('source', '未知来源')
                    url = news.get('url', '')
                    
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
            message = f"""🌍 每日综合要闻简报

📅 更新时间: {timestamp} (UTC+8)

⚠️ 今日新闻源暂时不可用
🤖 请稍后查看新闻网站获取最新资讯

💡 我们正在努力恢复服务..."""
        
        # 6. 发送消息
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
