#!/usr/bin/env python3
"""
测试 GNews API
"""

import requests
import json

def test_gnews_api(api_key):
    """测试 GNews API"""
    print(f"\n🔍 测试 GNews API...")
    
    try:
        # 测试获取头条新闻
        url = "https://gnews.io/api/v4/top-headlines"
        params = {
            'token': api_key,
            'lang': 'en',
            'country': 'us',
            'max': 5
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✅ GNews API 可用: {len(articles)} 条新闻")
            
            print("📋 前 3 个新闻:")
            for i, article in enumerate(articles[:3], 1):
                title = article.get('title', '无标题')
                url = article.get('url', '无链接')
                description = article.get('description', '无描述')
                source = article.get('source', {}).get('name', '未知来源')
                published_at = article.get('publishedAt', '未知时间')
                
                print(f"  {i}. {title}")
                print(f"     🔗 {url}")
                print(f"     📰 来源: {source}")
                print(f"     📅 时间: {published_at}")
                if description:
                    print(f"     📝 {description[:100]}...")
            
            return True, len(articles)
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            return False, 0
            
    except Exception as e:
        print(f"❌ GNews API 测试失败: {e}")
        return False, 0

def main():
    print("🚀 测试 GNews API")
    print("=" * 30)
    
    api_key = "ab8fcdb83b3ba22fc4fd9d1c1bc97fa3"
    success, count = test_gnews_api(api_key)
    
    if success:
        print(f"\n✅ GNews API 测试成功！获取到 {count} 条新闻")
    else:
        print(f"\n❌ GNews API 测试失败")

if __name__ == "__main__":
    main()
