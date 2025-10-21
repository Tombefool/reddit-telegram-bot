"""
国际组织动态抓取模块
专门抓取联合国、北约、欧盟等国际组织的最新动态
"""

import requests
import feedparser
import time
from typing import List, Dict
from datetime import datetime, timedelta


def fetch_international_organizations(max_items: int = 3) -> List[Dict]:
    """
    抓取国际组织动态
    
    Args:
        max_items: 每个组织最多抓取的文章数量
    
    Returns:
        国际组织动态列表
    """
    org_sources = [
        {
            "name": "BBC World",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "category": "国际组织",
            "keywords": ["UN", "NATO", "EU", "WTO", "IMF", "G7", "G20", "international", "organization", "summit", "conference"]
        },
        {
            "name": "Reuters World",
            "url": "https://feeds.reuters.com/reuters/worldNews",
            "category": "国际组织",
            "keywords": ["UN", "NATO", "EU", "WTO", "IMF", "G7", "G20", "international", "organization", "summit", "conference"]
        },
        {
            "name": "CNN International",
            "url": "http://rss.cnn.com/rss/edition.rss",
            "category": "国际组织",
            "keywords": ["UN", "NATO", "EU", "WTO", "IMF", "G7", "G20", "international", "organization", "summit", "conference"]
        },
        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "category": "国际组织",
            "keywords": ["UN", "NATO", "EU", "WTO", "IMF", "G7", "G20", "international", "organization", "summit", "conference"]
        },
        {
            "name": "Deutsche Welle",
            "url": "https://rss.dw.com/rss/rss-en-all",
            "category": "国际组织",
            "keywords": ["UN", "NATO", "EU", "WTO", "IMF", "G7", "G20", "international", "organization", "summit", "conference"]
        }
    ]
    
    all_news = []
    
    for source in org_sources:
        try:
            print(f"🏛️ 抓取 {source['name']}...")
            
            # 解析 RSS 源
            feed = feedparser.parse(source['url'])
            
            if feed.bozo:
                print(f"⚠️ {source['name']} RSS 解析失败")
                continue
            
            items_added = 0
            for entry in feed.entries[:max_items * 2]:
                if items_added >= max_items:
                    break
                
                # 检查是否包含相关关键词
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                content = f"{title} {summary}"
                
                # 关键词匹配
                if any(keyword.lower() in content for keyword in source['keywords']):
                    # 解析发布时间
                    pub_time = datetime.now()
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_time = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                    
                    # 检查新鲜度（48小时内，国际组织动态相对稳定）
                    if datetime.now() - pub_time <= timedelta(hours=48):
                        news_item = {
                            'title': entry.get('title', ''),
                            'url': entry.get('link', ''),
                            'selftext': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                            'summary': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                            'source': source['name'],
                            'category': source['category'],
                            'published_time': pub_time,
                            'created_utc': int(pub_time.timestamp()),
                            'subreddit': f"intl-org-{source['category'].lower()}",
                            'score': 0,
                            'num_comments': 0,
                            'author': source['name']
                        }
                        all_news.append(news_item)
                        items_added += 1
            
            print(f"✅ {source['name']}: {items_added} 条动态")
            time.sleep(1)  # 避免请求过快
            
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")
            continue
    
    # 按发布时间排序
    all_news.sort(key=lambda x: x['created_utc'], reverse=True)
    
    print(f"🏛️ 国际组织动态总计: {len(all_news)} 条")
    return all_news


def fetch_conflict_news(max_items: int = 3) -> List[Dict]:
    """
    抓取地区冲突与安全动态
    
    Args:
        max_items: 每个冲突地区最多抓取的文章数量
    
    Returns:
        冲突动态列表
    """
    conflict_sources = [
        {
            "name": "BBC World",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "category": "全球冲突",
            "keywords": ["Ukraine", "Russia", "Israel", "Palestine", "Middle East", "conflict", "war"]
        },
        {
            "name": "Reuters World",
            "url": "https://feeds.reuters.com/reuters/worldNews",
            "category": "世界新闻",
            "keywords": ["conflict", "military", "security", "defense", "war", "peace"]
        },
        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "category": "中东视角",
            "keywords": ["Middle East", "Palestine", "Israel", "Syria", "Iran", "Yemen"]
        }
    ]
    
    conflict_keywords = [
        "Ukraine", "Russia", "NATO", "war", "conflict", "military", "defense",
        "Israel", "Palestine", "Middle East", "Syria", "Iran", "Yemen",
        "North Korea", "DPRK", "nuclear", "missile", "sanctions",
        "Taiwan", "South China Sea", "territorial", "dispute"
    ]
    
    all_news = []
    
    for source in conflict_sources:
        try:
            print(f"⚔️ 抓取 {source['name']} 冲突动态...")
            
            feed = feedparser.parse(source['url'])
            
            if feed.bozo:
                print(f"⚠️ {source['name']} RSS 解析失败")
                continue
            
            items_added = 0
            for entry in feed.entries[:max_items * 3]:  # 多取一些用于过滤
                if items_added >= max_items:
                    break
                
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                content = f"{title} {summary}"
                
                # 冲突关键词匹配
                if any(keyword.lower() in content for keyword in conflict_keywords):
                    pub_time = datetime.now()
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_time = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                    
                    # 检查新鲜度（24小时内，冲突动态时效性强）
                    if datetime.now() - pub_time <= timedelta(hours=24):
                        news_item = {
                            'title': entry.get('title', ''),
                            'url': entry.get('link', ''),
                            'selftext': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                            'summary': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', ''),
                            'source': source['name'],
                            'category': '地区冲突',
                            'published_time': pub_time,
                            'created_utc': int(pub_time.timestamp()),
                            'subreddit': 'conflict-security',
                            'score': 0,
                            'num_comments': 0,
                            'author': source['name']
                        }
                        all_news.append(news_item)
                        items_added += 1
            
            print(f"✅ {source['name']}: {items_added} 条冲突动态")
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 失败: {e}")
            continue
    
    all_news.sort(key=lambda x: x['created_utc'], reverse=True)
    print(f"⚔️ 地区冲突动态总计: {len(all_news)} 条")
    return all_news


if __name__ == "__main__":
    # 测试抓取
    print("🧪 测试国际组织动态抓取...")
    org_news = fetch_international_organizations(max_items=2)
    
    print(f"\n🏛️ 国际组织动态 ({len(org_news)} 条):")
    for i, item in enumerate(org_news[:3], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   组织: {item['source']}")
        print(f"   时间: {item['published_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   链接: {item['url']}")
    
    print("\n" + "="*50)
    
    print("🧪 测试地区冲突动态抓取...")
    conflict_news = fetch_conflict_news(max_items=2)
    
    print(f"\n⚔️ 地区冲突动态 ({len(conflict_news)} 条):")
    for i, item in enumerate(conflict_news[:3], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   来源: {item['source']}")
        print(f"   时间: {item['published_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   链接: {item['url']}")
