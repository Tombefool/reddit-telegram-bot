#!/usr/bin/env python3
"""
测试多个新闻 RSS 源
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def test_rss_source(name, url, keywords=None):
    """测试单个 RSS 源"""
    print(f"\n🔍 测试 {name}...")
    print(f"📡 URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ RSS 源可访问")
            
            try:
                root = ET.fromstring(response.text)
                items = root.findall('.//item')
                print(f"📰 找到 {len(items)} 个新闻条目")
                
                if items and keywords:
                    # 检查财经相关新闻
                    finance_items = []
                    for item in items:
                        title_elem = item.find('title')
                        description_elem = item.find('description')
                        
                        if title_elem is not None and description_elem is not None:
                            title = title_elem.text.lower()
                            description = description_elem.text.lower()
                            
                            for keyword in keywords:
                                if keyword in title or keyword in description:
                                    finance_items.append(item)
                                    break
                    
                    print(f"💰 找到 {len(finance_items)} 个财经相关新闻")
                    
                    if finance_items:
                        print("📈 财经新闻示例:")
                        for i, item in enumerate(finance_items[:2], 1):
                            title_elem = item.find('title')
                            link_elem = item.find('link')
                            title = title_elem.text if title_elem is not None else "无标题"
                            link = link_elem.text if link_elem is not None else "无链接"
                            print(f"  {i}. {title}")
                            print(f"     🔗 {link}")
                
                return True, len(items)
                
            except ET.ParseError as e:
                print(f"❌ XML 解析失败: {e}")
                return False, 0
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False, 0

def main():
    print("🚀 测试多个新闻 RSS 源")
    print("=" * 60)
    
    # 财经关键词
    finance_keywords = ['stock', 'market', 'economy', 'finance', 'bitcoin', 'crypto', 'trading', 'investment', 'earnings', 'revenue', 'business', 'dollar', 'inflation', 'fed', 'federal']
    
    # 要测试的 RSS 源
    sources = [
        ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml", finance_keywords),
        ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews", finance_keywords),
        ("CNN Business", "http://rss.cnn.com/rss/money_latest.rss", finance_keywords),
        ("Yahoo Finance", "https://feeds.finance.yahoo.com/rss/2.0/headline", finance_keywords),
        ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", finance_keywords),
        ("Financial Times", "https://www.ft.com/rss/home", finance_keywords),
        ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", finance_keywords),
        ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss&rss=finance", finance_keywords),
    ]
    
    results = []
    
    for name, url, keywords in sources:
        success, item_count = test_rss_source(name, url, keywords)
        results.append((name, url, success, item_count))
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    working_sources = []
    for name, url, success, item_count in results:
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"{name:20} | {status:10} | {item_count:3} 条目")
        if success:
            working_sources.append((name, url))
    
    print("\n🎯 推荐使用的 RSS 源:")
    if working_sources:
        for name, url in working_sources:
            print(f"  • {name}: {url}")
        print(f"\n💡 找到 {len(working_sources)} 个可用的新闻源")
    else:
        print("  ❌ 没有找到可用的 RSS 源")

if __name__ == "__main__":
    main()
