"""
Truth Social 抓取（Playwright 无头浏览器）
默认抓取 @realDonaldTrump 主页最近若干条帖子（静态文本与链接），不登录。
强化：多选择器回退、滚动加载、UA/超时/重试与本地缓存回退。
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os


CACHE_FILE = "truth_cache.json"


def _save_truth_cache(posts: List[Dict]) -> None:
    try:
        payload = [{
            'title': p.get('title',''),
            'url': p.get('url',''),
            'selftext': p.get('selftext',''),
            'author': p.get('author','truth-social'),
            'created_utc': p.get('created_utc', 0),
        } for p in posts if p.get('url')]
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'saved_at': int(datetime.utcnow().timestamp()), 'items': payload}, f, ensure_ascii=False)
    except Exception:
        pass


def load_truth_cache(max_age_hours: int = 24) -> List[Dict]:
    try:
        if not os.path.exists(CACHE_FILE):
            return []
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        saved_at = int(data.get('saved_at', 0))
        if saved_at <= 0:
            return []
        if int(datetime.utcnow().timestamp()) - saved_at > max_age_hours * 3600:
            return []
        items = data.get('items', [])
        results: List[Dict] = []
        for it in items:
            results.append({
                'title': it.get('title',''),
                'url': it.get('url',''),
                'score': 0,
                'selftext': it.get('selftext',''),
                'subreddit': 'truth-social',
                'author': it.get('author','truth-social'),
                'created_utc': it.get('created_utc', 0),
                'num_comments': 0,
            })
        return results
    except Exception:
        # 强制回退到本地缓存
        cached = load_truth_cache(max_age_hours=24)
        return cached


def fetch_truth_social_playwright(username: str = 'realDonaldTrump', limit: int = 10) -> List[Dict]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        # 未安装浏览器依赖时，返回缓存
        return load_truth_cache(max_age_hours=48)

    url = f"https://truthsocial.com/@{username}"
    results: List[Dict] = []

    try:
        with sync_playwright() as p:
            # 使用更稳定的浏览器配置
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            page = context.new_page()
            page.set_default_timeout(30000)

            # 增强重试机制
            for attempt in range(3):
                try:
                    print(f"🔄 Truth Social 抓取尝试 {attempt + 1}/3...")
                    page.goto(url, wait_until='networkidle')
                    
                    # 等待页面完全加载
                    page.wait_for_timeout(2000)
                    
                    # 更全面的选择器策略
                    sel_candidates = [
                        "article",
                        "[role='article']", 
                        "div[data-testid='post']",
                        "div[role='feed']",
                        ".post",
                        "[class*='post']",
                        "[class*='tweet']",
                        "[class*='status']",
                        "div[class*='timeline'] > div",
                        "main div[class*='feed'] > div",
                    ]
                    
                    # 渐进式滚动加载更多内容
                    print("📜 开始滚动加载内容...")
                    for i in range(10):  # 增加滚动次数
                        page.mouse.wheel(0, 1500)
                        page.wait_for_timeout(800)
                        
                        # 检查是否有新内容加载
                        current_cards = page.locator(", ".join(sel_candidates)).count()
                        if i > 3 and current_cards >= limit * 2:  # 有足够内容就停止
                            break
                    
                    # 等待内容稳定
                    page.wait_for_timeout(1500)
                    
                    # 尝试多种选择器策略
                    cards = None
                    for sel in sel_candidates:
                        try:
                            cards = page.locator(sel).all()
                            if cards and len(cards) > 0:
                                print(f"✅ 使用选择器: {sel}, 找到 {len(cards)} 个元素")
                                break
                        except Exception:
                            continue
                    
                    if not cards or len(cards) == 0:
                        print("⚠️ 未找到任何帖子元素，尝试备用策略...")
                        # 备用策略：查找包含文本的元素
                        cards = page.locator("div:has-text('Truth')").all()
                        if not cards:
                            cards = page.locator("div:has-text('Trump')").all()
                    
                    if not cards:
                        print("❌ 所有选择器都失败，继续下次尝试...")
                        continue

                    print(f"📝 开始解析 {min(len(cards), limit)} 个帖子...")
                    for i, card in enumerate(cards[:limit]):
                        try:
                            # 等待元素可见
                            card.wait_for(state='visible', timeout=5000)
                            
                            # 获取文本内容
                            text = card.inner_text()
                            if not text or len(text.strip()) < 10:  # 跳过太短的内容
                                continue
                                
                            # 获取链接
                            link_selectors = [
                                "a[href*='/@']",
                                "a[href*='/posts/']", 
                                "a[href*='/statuses/']",
                                "a"
                            ]
                            link = None
                            for link_sel in link_selectors:
                                try:
                                    link_el = card.locator(link_sel).first
                                    if link_el.count() > 0:
                                        link = link_el.get_attribute('href')
                                        if link:
                                            break
                                except Exception:
                                    continue
                            
                            if link and link.startswith('/'):
                                link = 'https://truthsocial.com' + link
                            elif not link:
                                link = url
                            
                            # 解析时间
                            created_ts = int(datetime.utcnow().timestamp())
                            time_selectors = [
                                "time[datetime]",
                                "abbr[title]",
                                "[class*='time']",
                                "[class*='date']"
                            ]
                            
                            for time_sel in time_selectors:
                                try:
                                    time_el = card.locator(time_sel).first
                                    if time_el.count() > 0:
                                        time_attr = (time_el.get_attribute('datetime') or 
                                                  time_el.get_attribute('title') or
                                                  time_el.inner_text())
                                        if time_attr:
                                            # 尝试解析各种时间格式
                                            try:
                                                if 'T' in time_attr:
                                                    dt = datetime.fromisoformat(time_attr.replace('Z', '+00:00'))
                                                elif 'ago' in time_attr.lower():
                                                    # 处理相对时间，暂时用当前时间
                                                    pass
                                                else:
                                                    dt = datetime.fromisoformat(time_attr)
                                                
                                                if dt.tzinfo:
                                                    dt = dt.astimezone(tz=None).replace(tzinfo=None)
                                                created_ts = int(dt.timestamp())
                                                break
                                            except Exception:
                                                continue
                                except Exception:
                                    continue

                            # 生成标题
                            lines = text.strip().split('\n')
                            title = lines[0][:120] if lines[0] else 'Truth Social 更新'
                            
                            # 清理文本内容
                            selftext = text.strip()
                            if len(selftext) > 500:
                                selftext = selftext[:500] + "..."
                            
                            results.append({
                                'title': title,
                                'url': link,
                                'score': 0,
                                'selftext': selftext,
                                'subreddit': 'truth-social',
                                'author': username,
                                'created_utc': created_ts,
                                'num_comments': 0,
                            })
                            
                        except Exception as e:
                            print(f"⚠️ 解析第 {i+1} 个帖子失败: {e}")
                            continue
                    
                    if results:
                        print(f"✅ 成功抓取 {len(results)} 个 Truth Social 帖子")
                        break
                    else:
                        print("⚠️ 本轮未获取到有效内容，继续尝试...")
                        
                except Exception as e:
                    print(f"❌ 第 {attempt + 1} 次尝试失败: {e}")
                    if attempt == 2:  # 最后一次尝试
                        print("🔄 所有尝试失败，使用缓存内容...")
                        cached_results = load_truth_cache(max_age_hours=48)
                        if cached_results:
                            print(f"📦 使用缓存内容: {len(cached_results)} 个帖子")
                            return cached_results
                    page.wait_for_timeout(2000)

            context.close()
            browser.close()

        if results:
            _save_truth_cache(results)
            print(f"💾 已保存 {len(results)} 个帖子到缓存")
        return results
        
    except Exception as e:
        print(f"❌ Truth Social 抓取完全失败: {e}")
        # 最后回退到缓存
        cached_results = load_truth_cache(max_age_hours=48)
        if cached_results:
            print(f"📦 回退到缓存内容: {len(cached_results)} 个帖子")
        return cached_results


