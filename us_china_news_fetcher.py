"""
中美关系新闻抓取模块
专门抓取中美关系相关的新闻和动态
"""

import requests
import feedparser
import time
from typing import List, Dict
from datetime import datetime, timedelta
import re


def fetch_us_china_news(max_items: int = 5) -> List[Dict]:
    """
    抓取中美关系相关新闻
    
    Args:
        max_items: 每个源最多抓取的文章数量
    
    Returns:
        新闻文章列表
    """
    news_sources = [
        {
            "name": "South China Morning Post",
            "url": "https://www.scmp.com/rss/91/feed",
            "category": "中美关系"
        },
        {
            "name": "Foreign Policy",
            "url": "https://foreignpolicy.com/feed/",
            "category": "地缘政治"
        },
        {
            "name": "BBC World",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "category": "中美关系"
        },
        {
            "name": "CNN International",
            "url": "http://rss.cnn.com/rss/edition.rss",
            "category": "中美关系"
        },
        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "category": "中美关系"
        }
    ]
    
    # 中美关系关键词
    keywords = [
        "China", "US", "中美", "贸易战", "关税", "华为", "TikTok", "芯片", "半导体",
        "一带一路", "Belt and Road", "南海", "South China Sea", "台湾", "Taiwan",
        "香港", "Hong Kong", "新疆", "Xinjiang", "人权", "human rights",
        "科技竞争", "tech competition", "供应链", "supply chain", "脱钩", "decoupling",
        "拜登", "Biden", "特朗普", "Trump", "习近平", "Xi Jinping"
    ]
    
    all_news = []
    
    for source in news_sources:
        try:
            print(f"📰 抓取 {source['name']}...")
            
            # 解析 RSS 源
            feed = feedparser.parse(source['url'])
            
            if feed.bozo:
                print(f"⚠️ {source['name']} RSS 解析失败")
                continue
            
            items_added = 0
            for entry in feed.entries[:max_items * 2]:  # 多取一些用于过滤
                if items_added >= max_items:
                    break
                
                # 检查是否包含中美关系关键词
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                content = f"{title} {summary}"
                
                # 关键词匹配
                if any(keyword.lower() in content for keyword in keywords):
                    # 解析发布时间
                    pub_time = datetime.now()
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_time = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                    
                    # 检查新鲜度（24小时内）
                    if datetime.now() - pub_time <= timedelta(hours=24):
                        news_item = {
                            'title': entry.get('title', ''),
                            'url': entry.get('link', ''),
                            'selftext': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                            'summary': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                            'source': source['name'],
                            'category': source['category'],
                            'published_time': pub_time,
                            'created_utc': int(pub_time.timestamp()),
                            'subreddit': 'us-china-news',
                            'score': 0,
                            'num_comments': 0,
                            'author': source['name']
                        }
                        all_news.append(news_item)
                        items_added += 1
            
            print(f"✅ {source['name']}: {items_added} 条相关新闻")
            time.sleep(1)  # 避免请求过快
            
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")
            continue
    
    # 按发布时间排序
    all_news.sort(key=lambda x: x['created_utc'], reverse=True)
    
    print(f"📊 中美关系新闻总计: {len(all_news)} 条")
    return all_news


def filter_us_china_posts(posts: List[Dict]) -> List[Dict]:
    """
    从 Reddit 帖子中过滤出中美关系相关内容
    
    Args:
        posts: Reddit 帖子列表
    
    Returns:
        过滤后的帖子列表
    """
    keywords = [
        "china", "chinese", "us-china", "中美", "贸易战", "关税", "华为", "tiktok",
        "semiconductor", "chip", "taiwan", "hong kong", "xinjiang", "belt and road",
        "biden", "trump", "xi jinping", "trade war", "tech war", "decoupling"
    ]
    
    filtered_posts = []
    
    for post in posts:
        title = post.get('title', '').lower()
        content = post.get('selftext', '').lower()
        subreddit = post.get('subreddit', '').lower()
        
        # 检查是否包含中美关系关键词
        if any(keyword in title or keyword in content for keyword in keywords):
            # 标记为中美关系相关
            post['category'] = '中美关系'
            post['subreddit'] = f"us-china-{post.get('subreddit', '')}"
            filtered_posts.append(post)
        # 特定板块直接包含
        elif subreddit in ['china', 'sino', 'china_news', 'geopolitics']:
            post['category'] = '中美关系'
            post['subreddit'] = f"us-china-{subreddit}"
            filtered_posts.append(post)
    
    return filtered_posts


if __name__ == "__main__":
    # 测试抓取
    print("🧪 测试中美关系新闻抓取...")
    news = fetch_us_china_news(max_items=3)
    
    print(f"\n📰 抓取结果 ({len(news)} 条):")
    for i, item in enumerate(news[:5], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   来源: {item['source']}")
        print(f"   时间: {item['published_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   链接: {item['url']}")
