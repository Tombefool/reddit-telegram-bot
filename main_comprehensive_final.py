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
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def log(message):
    """统一日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

class SourceHealthMonitor:
    """源健康监控器"""
    def __init__(self, db_path="sources_health.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_health (
                source_name TEXT PRIMARY KEY,
                last_success TIMESTAMP,
                last_failure TIMESTAMP,
                failure_count INTEGER DEFAULT 0,
                is_healthy INTEGER DEFAULT 1,
                weight REAL DEFAULT 1.0
            )
        ''')
        conn.commit()
        conn.close()
    
    def record_success(self, source_name: str, weight: float = 1.0):
        """记录成功"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO source_health 
            (source_name, last_success, failure_count, is_healthy, weight)
            VALUES (?, ?, 0, 1, ?)
        ''', (source_name, datetime.now(), weight))
        conn.commit()
        conn.close()
    
    def record_failure(self, source_name: str):
        """记录失败"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO source_health 
            (source_name, last_failure, failure_count, is_healthy)
            VALUES (?, ?, COALESCE((SELECT failure_count FROM source_health WHERE source_name = ?), 0) + 1, 0)
        ''', (source_name, datetime.now(), source_name))
        conn.commit()
        conn.close()
    
    def is_healthy(self, source_name: str) -> bool:
        """检查源是否健康"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT is_healthy FROM source_health WHERE source_name = ?', (source_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else True
    
    def get_weight(self, source_name: str) -> float:
        """获取源权重"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT weight FROM source_health WHERE source_name = ?', (source_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 1.0

class NewsCache:
    """新闻缓存管理器"""
    def __init__(self, db_path="news_cache.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                summary TEXT,
                url TEXT,
                source TEXT,
                category TEXT,
                weight REAL,
                timestamp TIMESTAMP,
                UNIQUE(title, source)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON news_cache(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON news_cache(category)
        ''')
        conn.commit()
        conn.close()
    
    def add_news(self, news_item: Dict[str, Any], category: str, weight: float = 1.0):
        """添加新闻到缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO news_cache 
                (title, summary, url, source, category, weight, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_item.get('title', ''),
                news_item.get('summary', ''),
                news_item.get('url', ''),
                news_item.get('source', ''),
                category,
                weight,
                datetime.now()
            ))
            conn.commit()
        except Exception as e:
            log(f"缓存添加失败: {e}")
        finally:
            conn.close()
    
    def get_cached_news(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取缓存的新闻"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT title, summary, url, source, weight, timestamp
            FROM news_cache 
            WHERE category = ? 
            ORDER BY weight DESC, timestamp DESC 
            LIMIT ?
        ''', (category, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'title': row[0],
                'summary': row[1],
                'url': row[2],
                'source': row[3],
                'weight': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        return results
    
    def cleanup_old_news(self, hours: int = 24):
        """清理旧新闻"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor.execute('DELETE FROM news_cache WHERE timestamp < ?', (cutoff_time,))
        conn.commit()
        conn.close()

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
        r"^您好[，,\s].*$",
        r"^你(好|您)提供的标题.*?已经是中文.*$",
        r"已经是中文[。\.].*$",
        r"如果您.*英文.*请.*提供.*原文.*$",
        r"^标题[：:].*$",
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
            prompt = (
                "你是新闻编辑。仅输出摘要本句，不要任何说明或前后缀，不要加‘标题/内容’等标签。"
                "用简体中文在60字内概述关键信息。\n\n"
                f"标题：{title}\n内容：{content}"
            )
            resp = model.generate_content(prompt)
            summary = clean_ai_artifacts((resp.text or "").strip())
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
    """使用 Gemini 翻译文本：若已是中文则原样返回；禁止解释性前后缀"""
    if not model:
        return text

    try:
        # 简单中文检测：包含CJK字符则视为中文
        if re.search(r"[\u4e00-\u9fff]", text or ""):
            return text
        prompt = (
            "仅输出翻译结果（简体中文），不要任何解释、礼貌用语或前后缀；"
            "不要出现‘标题/内容/翻译为/如下’等提示语；保持简洁准确：\n\n"
            f"{text}"
        )
        response = model.generate_content(prompt)
        translated = (response.text or "").strip()
        return clean_ai_artifacts(translated)
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
    
    # 3. RSS 新闻源（带健康监控）
    # 从配置读取来源，primary 优先
    rss_sources = []
    health_monitor = SourceHealthMonitor()
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            # 优先源
            for s in cfg.get('primary', []):
                if health_monitor.is_healthy(s['name']):
                    rss_sources.append((s['name'], s['url'], 1.0))  # 优先源权重1.0
                else:
                    log(f"⚠️ 优先源 {s['name']} 不健康，跳过")
            # 次级源
            for s in cfg.get('secondary', []):
                if health_monitor.is_healthy(s['name']):
                    rss_sources.append((s['name'], s['url'], 0.8))  # 次级源权重0.8
                else:
                    log(f"⚠️ 次级源 {s['name']} 不健康，跳过")
            # 可选社交代理 RSS（基于分组与权重+镜像轮换）
            social_groups = cfg.get('social_groups', {})
            nitter_mirrors = cfg.get('nitter_mirrors', ["https://nitter.net"]) 
            mirror_idx = random.randint(0, len(nitter_mirrors)-1)
            def nitter_url(handle: str) -> str:
                base = nitter_mirrors[mirror_idx % len(nitter_mirrors)].rstrip('/')
                return f"{base}/{handle}/rss"
            for group_name, group in social_groups.items():
                if group.get('enabled'):
                    group_weight = group.get('weight', 0.7)
                    for handle in group.get('accounts', []):
                        source_name = f"Twitter-{handle}"
                        if health_monitor.is_healthy(source_name):
                            rss_sources.append((source_name, nitter_url(handle), group_weight))
                        else:
                            log(f"⚠️ 社交源 {source_name} 不健康，跳过")
    except Exception:
        # 回退内置
        rss_sources = [
            ("AP News", "https://apnews.com/apf-topnews?output=rss", 1.0),
            ("Reuters World", "https://feeds.reuters.com/reuters/worldNews", 1.0),
            ("Sputnik", "https://sputniknews.com/export/rss2/archive/index.xml", 1.0),
            ("联合早报", "https://www.zaobao.com.sg/rss.xml", 1.0),
            ("NPR News", "http://www.npr.org/rss/rss.php?id=1001", 0.8),
            ("HuffPost World", "https://www.huffpost.com/section/world-news/feed", 0.8),
            ("FOX News", "http://feeds.foxnews.com/foxnews/latest", 0.8),
            ("NYT Top Stories", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", 0.8),
            ("CNN International", "http://rss.cnn.com/rss/edition.rss", 0.8),
            ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", 0.8)
        ]
    
    for name, url, weight in rss_sources:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            }
            
            # 带重试的请求（指数退避）
            def get_with_retry(u, headers, timeout=10, retries=3):
                delay = 1
                for attempt in range(retries):
                    try:
                        return requests.get(u, headers=headers, timeout=timeout)
                    except requests.RequestException:
                        if attempt == retries - 1:
                            raise
                        time.sleep(delay)
                        delay = min(delay * 2, 8)

            response_text = None
            # 社交源：镜像轮换 + RSSHub 兜底
            if name.startswith('Twitter-'):
                try:
                    handle = name.split('Twitter-')[-1]
                    # 尝试 Nitter 镜像，最多尝试全部镜像
                    tried = 0
                    for offset in range(len(nitter_mirrors)):
                        base = nitter_mirrors[(mirror_idx + offset) % len(nitter_mirrors)].rstrip('/')
                        social_url = f"{base}/{handle}/rss"
                        try:
                            r = get_with_retry(social_url, headers, timeout=10, retries=2)
                            if r.status_code == 200 and r.text.strip():
                                response_text = r.text
                                break
                        except Exception:
                            pass
                        tried += 1
                    # 若全部 Nitter 失败，尝试 RSSHub
                    if not response_text:
                        rsshub_mirrors = cfg.get('rsshub_mirrors', ['https://rsshub.app'])
                        for rb in rsshub_mirrors:
                            rb = rb.rstrip('/')
                            # 优先使用 /x/user/:id
                            social_url = f"{rb}/x/user/{handle}"
                            try:
                                r = get_with_retry(social_url, headers, timeout=12, retries=2)
                                if r.status_code == 200 and r.text.strip():
                                    response_text = r.text
                                    break
                            except Exception:
                                pass
                except Exception:
                    response_text = None
            else:
                resp = get_with_retry(url, headers, timeout=10, retries=3)
                if resp.status_code == 200:
                    response_text = resp.text

            if response_text:
                root = ET.fromstring(response_text)
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
                        keywords = ['trump', 'biden', 'president', 'election', 'china', 'russia', 'ukraine', 'israel', 'palestine', 'economy', 'market', 'trade', 'war', 'conflict', 'politics', 'government', 'congress', 'senate', 'bill', 'proposal', 'bitcoin', 'crypto', 'cryptocurrency', 'stock', 'nasdaq', 'dow', 's&p', 'sp500', 'lithium', 'nickel', 'cobalt', 'rare earth', 'graphite']
                        content = f"{title} {description}".lower()
                        
                        if any(keyword in content for keyword in keywords):
                            news_type = 'china_us' if any(word in content for word in ['china', 'chinese', 'beijing', 'taiwan', 'trade war', 'tariff', 'semiconductor', 'huawei', 'tiktok']) else 'general'
                            news_item = {
                                'title': title,
                                'content': description,
                                'source': name,
                                'time': pub_date,
                                'url': link,
                                'type': news_type,
                                'weight': weight
                            }
                            all_news.append(news_item)
                            # 记录成功
                            health_monitor.record_success(name, weight)
            
            time.sleep(1)
        except Exception as e:
            log(f"❌ {name}: {e}")
            # 记录失败
            health_monitor.record_failure(name)
    
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
        
        # 4. 初始化缓存和健康监控
        news_cache = NewsCache()
        health_monitor = SourceHealthMonitor()
        
        # 清理旧缓存
        news_cache.cleanup_old_news(24)
        
        # 5. 分类新闻（新增标签：俄乌冲突、关键矿产、虚拟货币与全球股市）
        lower = lambda s: (s or '').lower()
        trump_news = [n for n in all_news if 'trump' in lower(n.get('title')) or 'trump' in lower(n.get('content'))]
        china_us_news = [n for n in all_news if (n.get('type') == 'china_us' or 'china' in lower(n.get('title')) or 'china' in lower(n.get('content'))) and n not in trump_news]
        ru_ua_news = [n for n in all_news if any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['ukraine','zelensky','russia','kremlin','putin','donbas','crimea'])]
        minerals_news = [n for n in all_news if any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['lithium','nickel','cobalt','rare earth','graphite','copper','critical mineral','mining','battery metal'])]
        crypto_markets_news = [n for n in all_news if any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['bitcoin','crypto','cryptocurrency','ethereum','nasdaq','dow','s&p','sp500','stocks','markets','equities','fed'])]
        other_news = [n for n in all_news if n not in trump_news and n not in china_us_news and n not in ru_ua_news and n not in minerals_news and n not in crypto_markets_news]
        
        # 权重排序函数：按权重×时间新鲜度排序
        def weight_sort_key(item):
            weight = item.get('weight', 1.0)
            time_str = item.get('time', '')
            # 简单的时间新鲜度评分（越新越高）
            time_score = 1.0
            if 'today' in time_str.lower() or 'just' in time_str.lower():
                time_score = 1.0
            elif 'hour' in time_str.lower():
                time_score = 0.9
            elif 'minute' in time_str.lower():
                time_score = 0.95
            else:
                time_score = 0.8
            return weight * time_score

        # 回填工具：将列表补齐到目标条数，优先同主题宽匹配，再次为总体按时间最新
        def unique_key(item):
            return (item.get('title','').strip().lower())

        def fill_to_count(primary, target, wide_filter=None):
            selected_keys = {unique_key(x) for x in primary}
            result = list(primary)
            # 候选池：按权重×时间新鲜度排序
            pool = sorted(all_news, key=weight_sort_key, reverse=True)
            # 第一轮：按宽匹配条件补齐
            if wide_filter:
                for item in pool:
                    if len(result) >= target:
                        break
                    if unique_key(item) in selected_keys:
                        continue
                    if wide_filter(item):
                        result.append(item)
                        selected_keys.add(unique_key(item))
            # 第二轮：任意最新补齐
            for item in pool:
                if len(result) >= target:
                    break
                if unique_key(item) in selected_keys:
                    continue
                result.append(item)
                selected_keys.add(unique_key(item))
            # 最终按权重排序
            final_result = sorted(result, key=weight_sort_key, reverse=True)[:target]
            
            # 缓存新闻到数据库
            for item in final_result:
                category = "trump" if wide_filter and "trump" in str(wide_filter).lower() else "general"
                news_cache.add_news(item, category, item.get('weight', 1.0))
            
            return final_result

        def fill_to_count_with_cache(primary, category, target, wide_filter=None):
            """带缓存的补齐函数"""
            selected_keys = {unique_key(x) for x in primary}
            result = list(primary)
            # 候选池：按权重×时间新鲜度排序
            pool = sorted(all_news, key=weight_sort_key, reverse=True)
            # 第一轮：按宽匹配条件补齐
            if wide_filter:
                for item in pool:
                    if len(result) >= target:
                        break
                    if unique_key(item) in selected_keys:
                        continue
                    if wide_filter(item):
                        result.append(item)
                        selected_keys.add(unique_key(item))
            # 第二轮：任意最新补齐
            for item in pool:
                if len(result) >= target:
                    break
                if unique_key(item) in selected_keys:
                    continue
                result.append(item)
                selected_keys.add(unique_key(item))
            # 最终按权重排序
            final_result = sorted(result, key=weight_sort_key, reverse=True)[:target]
            
            # 缓存新闻到数据库
            for item in final_result:
                news_cache.add_news(item, category, item.get('weight', 1.0))
            
            return final_result

        # 定义各主题的宽匹配函数并补齐到10条
        trump_news = fill_to_count_with_cache(
            trump_news, "trump", 10,
            wide_filter=lambda n: 'white house' in lower(n.get('content')) or 'president' in lower(n.get('content'))
        )
        china_us_news = fill_to_count_with_cache(
            china_us_news, "china_us", 10,
            wide_filter=lambda n: any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['china','beijing','taiwan','tariff','semiconductor','huawei','tiktok','congress','bipartisan'])
        )
        ru_ua_news = fill_to_count_with_cache(
            ru_ua_news, "ru_ua", 10,
            wide_filter=lambda n: any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['ukraine','russia','kremlin','moscow','kyiv','nato'])
        )
        minerals_news = fill_to_count_with_cache(
            minerals_news, "minerals", 10,
            wide_filter=lambda n: any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['lithium','nickel','cobalt','rare earth','graphite','copper','mining','battery'])
        )
        crypto_markets_news = fill_to_count_with_cache(
            crypto_markets_news, "crypto_markets", 10,
            wide_filter=lambda n: any(k in lower(n.get('title')) or k in lower(n.get('content')) for k in ['bitcoin','crypto','ethereum','nasdaq','dow','s&p','sp500','stocks','market'])
        )
        
        # 5. 格式化消息（遵循用户提供的出版格式）
        timestamp = get_beijing_timestamp()
        
        # 媒体中文名映射
        def source_cn(name: str) -> str:
            n = (name or '').strip()
            mapping = {
                'CNN': '有线电视新闻网 CNN',
                'CNN International': '有线电视新闻网 CNN',
                'The New York Times': '纽约时报 NYT',
                'NYT Top Stories': '纽约时报 NYT',
                'Reuters': '路透社 Reuters',
                'Reuters World': '路透社 Reuters',
                'Bloomberg': '彭博社 Bloomberg',
                'Fox News': '福克斯新闻 FOX',
                'FOX News': '福克斯新闻 FOX',
                'Washington Post': '华盛顿邮报 WP',
                'The Washington Post': '华盛顿邮报 WP',
                'NPR': '美国国家公共电台 NPR',
                'NPR News': '美国国家公共电台 NPR',
                'Financial Times': '金融时报 FT',
                'The Wall Street Journal': '华尔街日报 WSJ',
                'Wall Street Journal': '华尔街日报 WSJ',
                'HuffPost': '赫芬顿邮报 HuffPost',
                'AP News': '美联社 AP',
                'Associated Press': '美联社 AP',
                '联合早报': '联合早报 LHZB',
                'Sputnik': '俄罗斯卫星通讯社 Sputnik',
            }
            return mapping.get(n, n or '未知来源')

        def extract_time_iso(time_str: str) -> str:
            if not time_str:
                return ''
            t = time_str.replace('T', ' ').replace('Z', '').strip()
            return t[:16]

        def extract_entities(text: str) -> str:
            if not text:
                return ''
            keywords = ['特朗普', '拜登', '哈里斯', '国会', '参议院', '众议院', '白宫', '美国', '中国', '北京', '台湾', '华为', 'TikTok', '英伟达', '美联储']
            found = []
            for k in keywords:
                if k in text:
                    found.append(k)
            en_keywords = ['Trump', 'Biden', 'Congress', 'Senate', 'House', 'White House', 'China', 'Taiwan', 'Huawei', 'TikTok', 'Nvidia', 'Federal Reserve']
            for k in en_keywords:
                if k.lower() in text.lower():
                    found.append(k)
            uniq = []
            for x in found:
                if x not in uniq:
                    uniq.append(x)
            return '；'.join(uniq[:4])

        def format_source_link(name: str, url: str) -> str:
            txt = source_cn(name)
            if url:
                return f'[{txt}]({url})'
            return txt

        if all_news:
            lines = []
            lines.append('每日综合要闻简报')
            lines.append(f'更新时间：{timestamp} (UTC+8)')
            lines.append(f'今日收录：{len(all_news)}条重点新闻')
            
            # 源健康状态统计
            healthy_sources = 0
            total_sources = 0
            try:
                conn = sqlite3.connect("sources_health.db")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM source_health WHERE is_healthy = 1")
                healthy_sources = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM source_health")
                total_sources = cursor.fetchone()[0]
                conn.close()
            except:
                pass
            
            if total_sources > 0:
                health_rate = (healthy_sources / total_sources) * 100
                lines.append(f'源健康状态：{healthy_sources}/{total_sources} ({health_rate:.1f}%)')
            
            lines.append('')
            lines.append('---')
            lines.append('')

            # 特朗普总统动态
            lines.append('## 一、特朗普总统动态')
            lines.append('')
            for idx, news in enumerate(trump_news[:3], 1):
                title = clean_ai_artifacts(sanitize_text(translate_with_gemini(model, news.get('title','')) if model else news.get('title','')))
                summary_base = clean_ai_artifacts(sanitize_text(summarize_text(model, news.get('title',''), news.get('content',''))))
                time_part = extract_time_iso(news.get('time',''))
                entity_part = extract_entities(title + ' ' + (news.get('content','') or ''))
                summary = summary_base
                if time_part:
                    summary = f"时间：{time_part}；" + summary
                if entity_part:
                    summary = f"人物/机构：{entity_part}；" + summary
                src = format_source_link(news.get('source','未知来源'), news.get('url',''))
                if len(title) > 80:
                    title = title[:77] + '...'
                lines.append(f'{idx}. **{title}**')
                if summary:
                    lines.append(f'摘要：{summary}')
                lines.append(f'来源：{src}')
                lines.append('')

            lines.append('---')
            lines.append('')

            # 中美关系专题
            lines.append('## 二、中美关系专题')
            lines.append('')
            for idx, news in enumerate(china_us_news[:10], 1):
                title = clean_ai_artifacts(sanitize_text(translate_with_gemini(model, news.get('title','')) if model else news.get('title','')))
                summary_base = clean_ai_artifacts(sanitize_text(summarize_text(model, news.get('title',''), news.get('content',''))))
                time_part = extract_time_iso(news.get('time',''))
                entity_part = extract_entities(title + ' ' + (news.get('content','') or ''))
                summary = summary_base
                if time_part:
                    summary = f"时间：{time_part}；" + summary
                if entity_part:
                    summary = f"人物/机构：{entity_part}；" + summary
                src = format_source_link(news.get('source','未知来源'), news.get('url',''))
                if len(title) > 80:
                    title = title[:77] + '...'
                lines.append(f'{idx}. **{title}**')
                if summary:
                    lines.append(f'摘要：{summary}')
                lines.append(f'来源：{src}')
                lines.append('')

            lines.append('---')
            lines.append('')

            # 俄乌冲突动态
            lines.append('## 三、俄乌冲突动态')
            lines.append('')
            for idx, news in enumerate(ru_ua_news[:10], 1):
                title = clean_ai_artifacts(sanitize_text(translate_with_gemini(model, news.get('title','')) if model else news.get('title','')))
                summary_base = clean_ai_artifacts(sanitize_text(summarize_text(model, news.get('title',''), news.get('content',''))))
                time_part = extract_time_iso(news.get('time',''))
                entity_part = extract_entities(title + ' ' + (news.get('content','') or ''))
                summary = summary_base
                if time_part:
                    summary = f"时间：{time_part}；" + summary
                if entity_part:
                    summary = f"人物/机构：{entity_part}；" + summary
                src = format_source_link(news.get('source','未知来源'), news.get('url',''))
                if len(title) > 80:
                    title = title[:77] + '...'
                lines.append(f'{idx}. **{title}**')
                if summary:
                    lines.append(f'摘要：{summary}')
                lines.append(f'来源：{src}')
                lines.append('')

            lines.append('---')
            lines.append('')
            # 关键矿产合作
            lines.append('## 四、关键矿产合作')
            lines.append('')
            for idx, news in enumerate(minerals_news[:10], 1):
                title = clean_ai_artifacts(sanitize_text(translate_with_gemini(model, news.get('title','')) if model else news.get('title','')))
                summary_base = clean_ai_artifacts(sanitize_text(summarize_text(model, news.get('title',''), news.get('content',''))))
                time_part = extract_time_iso(news.get('time',''))
                entity_part = extract_entities(title + ' ' + (news.get('content','') or ''))
                summary = summary_base
                if time_part:
                    summary = f"时间：{time_part}；" + summary
                if entity_part:
                    summary = f"人物/机构：{entity_part}；" + summary
                src = format_source_link(news.get('source','未知来源'), news.get('url',''))
                if len(title) > 80:
                    title = title[:77] + '...'
                lines.append(f'{idx}. **{title}**')
                if summary:
                    lines.append(f'摘要：{summary}')
                lines.append(f'来源：{src}')
                lines.append('')

            lines.append('---')
            lines.append('')

            # 虚拟货币和全球股市动态
            lines.append('## 五、虚拟货币和全球股市动态')
            lines.append('')
            for idx, news in enumerate(crypto_markets_news[:10], 1):
                title = clean_ai_artifacts(sanitize_text(translate_with_gemini(model, news.get('title','')) if model else news.get('title','')))
                summary_base = clean_ai_artifacts(sanitize_text(summarize_text(model, news.get('title',''), news.get('content',''))))
                time_part = extract_time_iso(news.get('time',''))
                entity_part = extract_entities(title + ' ' + (news.get('content','') or ''))
                summary = summary_base
                if time_part:
                    summary = f"时间：{time_part}；" + summary
                if entity_part:
                    summary = f"人物/机构：{entity_part}；" + summary
                src = format_source_link(news.get('source','未知来源'), news.get('url',''))
                if len(title) > 80:
                    title = title[:77] + '...'
                lines.append(f'{idx}. **{title}**')
                if summary:
                    lines.append(f'摘要：{summary}')
                lines.append(f'来源：{src}')
                lines.append('')

            lines.append('---')
            lines.append('')
            lines.append('来源：多家权威媒体 + AI 摘要')

            message_text = "\n".join(lines)
            if len(message_text) > 4000:
                message_text = message_text[:3997] + '...'
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
