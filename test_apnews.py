#!/usr/bin/env python3
"""
测试 AP News RSS 源
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def test_apnews_rss():
    """测试 AP News RSS 源"""
    print("🔍 测试 AP News RSS 源...")
    print("=" * 50)
    
    rss_url = "https://apnews.com/index.rss"
    
    try:
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        print(f"📡 请求 URL: {rss_url}")
        response = requests.get(rss_url, headers=headers, timeout=15)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📏 内容长度: {len(response.text)} 字符")
        
        if response.status_code == 200:
            print("✅ RSS 源可访问")
            
            # 解析 XML
            try:
                root = ET.fromstring(response.text)
                print("✅ XML 解析成功")
                
                # 查找所有 item 元素
                items = root.findall('.//item')
                print(f"📰 找到 {len(items)} 个新闻条目")
                
                if items:
                    print("\n📋 前 5 个新闻标题:")
                    for i, item in enumerate(items[:5], 1):
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        pub_date_elem = item.find('pubDate')
                        description_elem = item.find('description')
                        
                        title = title_elem.text if title_elem is not None else "无标题"
                        link = link_elem.text if link_elem is not None else "无链接"
                        pub_date = pub_date_elem.text if pub_date_elem is not None else "无日期"
                        description = description_elem.text if description_elem is not None else "无描述"
                        
                        print(f"\n{i}. {title}")
                        print(f"   🔗 {link}")
                        print(f"   📅 {pub_date}")
                        print(f"   📝 {description[:100]}..." if len(description) > 100 else f"   📝 {description}")
                
                # 检查是否有财经相关新闻
                finance_keywords = ['stock', 'market', 'economy', 'finance', 'bitcoin', 'crypto', 'trading', 'investment', 'earnings', 'revenue']
                finance_items = []
                
                for item in items:
                    title_elem = item.find('title')
                    description_elem = item.find('description')
                    
                    if title_elem is not None and description_elem is not None:
                        title = title_elem.text.lower()
                        description = description_elem.text.lower()
                        
                        for keyword in finance_keywords:
                            if keyword in title or keyword in description:
                                finance_items.append(item)
                                break
                
                print(f"\n💰 找到 {len(finance_items)} 个财经相关新闻")
                
                if finance_items:
                    print("\n📈 财经新闻示例:")
                    for i, item in enumerate(finance_items[:3], 1):
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        title = title_elem.text if title_elem is not None else "无标题"
                        link = link_elem.text if link_elem is not None else "无链接"
                        print(f"{i}. {title}")
                        print(f"   🔗 {link}")
                
                return True, len(items), len(finance_items)
                
            except ET.ParseError as e:
                print(f"❌ XML 解析失败: {e}")
                return False, 0, 0
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False, 0, 0
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False, 0, 0
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False, 0, 0

def main():
    print("🚀 AP News RSS 源测试")
    print("=" * 50)
    
    success, total_items, finance_items = test_apnews_rss()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"✅ RSS 源状态: {'可用' if success else '不可用'}")
    print(f"📰 总新闻数: {total_items}")
    print(f"💰 财经新闻数: {finance_items}")
    
    if success and finance_items > 0:
        print("\n🎉 推荐使用此 RSS 源！")
        print("💡 可以集成到每日推送中")
    elif success:
        print("\n⚠️ RSS 源可用，但财经新闻较少")
        print("💡 可以考虑使用，但可能需要过滤")
    else:
        print("\n❌ RSS 源不可用")
        print("💡 需要寻找其他数据源")

if __name__ == "__main__":
    main()
