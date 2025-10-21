#!/usr/bin/env python3
"""
测试新的新闻源
"""

import requests
import xml.etree.ElementTree as ET
import json

def test_rss_source(name, url):
    """测试 RSS 源"""
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
                
                if items:
                    print("📋 前 3 个新闻标题:")
                    for i, item in enumerate(items[:3], 1):
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        description_elem = item.find('description')
                        
                        if title_elem is not None:
                            title = title_elem.text
                            link = link_elem.text if link_elem is not None else "无链接"
                            description = description_elem.text if description_elem is not None else "无描述"
                            
                            print(f"  {i}. {title}")
                            print(f"     🔗 {link}")
                            if description:
                                print(f"     📝 {description[:100]}...")
                
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

def test_newsapi(api_key):
    """测试 NewsAPI"""
    print(f"\n🔍 测试 NewsAPI...")
    
    try:
        # 测试获取头条新闻
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'country': 'us',
            'pageSize': 5
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                print(f"✅ NewsAPI 可用: {len(articles)} 条新闻")
                
                print("📋 前 3 个新闻:")
                for i, article in enumerate(articles[:3], 1):
                    title = article.get('title', '无标题')
                    url = article.get('url', '无链接')
                    description = article.get('description', '无描述')
                    source = article.get('source', {}).get('name', '未知来源')
                    
                    print(f"  {i}. {title}")
                    print(f"     🔗 {url}")
                    print(f"     📰 来源: {source}")
                    if description:
                        print(f"     📝 {description[:100]}...")
                
                return True, len(articles)
            else:
                print(f"❌ NewsAPI 错误: {data.get('message')}")
                return False, 0
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            return False, 0
            
    except Exception as e:
        print(f"❌ NewsAPI 测试失败: {e}")
        return False, 0

def main():
    print("🚀 测试新的新闻源")
    print("=" * 50)
    
    # 测试 RSS 源
    rss_sources = [
        ("NPR News", "http://www.npr.org/rss/rss.php?id=1001"),
        ("HuffPost World", "https://www.huffpost.com/section/world-news/feed"),
        ("FOX News", "http://feeds.foxnews.com/foxnews/latest"),
    ]
    
    results = []
    for name, url in rss_sources:
        success, count = test_rss_source(name, url)
        results.append((name, "RSS", success, count))
    
    # 测试 NewsAPI
    api_key = "947e0ebd-201f-4870-851c-0e395403a397"
    success, count = test_newsapi(api_key)
    results.append(("NewsAPI", "API", success, count))
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("=" * 50)
    
    working_sources = []
    for name, source_type, success, count in results:
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"{name:15} | {source_type:5} | {status:10} | {count:3} 条目")
        if success:
            working_sources.append((name, source_type))
    
    print(f"\n🎯 推荐使用的新闻源: {len(working_sources)} 个")
    for name, source_type in working_sources:
        print(f"  • {name} ({source_type})")

if __name__ == "__main__":
    main()
