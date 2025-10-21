"""
Reddit 数据抓取模块
从 Reddit 公开 JSON API 获取指定板块的热门帖子
增强版：支持 OAuth 认证、多种 User-Agent、重试机制
"""

import requests
import time
import os
import random
from typing import List, Dict, Optional


def get_reddit_headers() -> Dict[str, str]:
    """获取 Reddit 请求头，包含多种 User-Agent 轮换"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }


def get_reddit_oauth_token() -> Optional[str]:
    """获取 Reddit OAuth token（如果配置了）"""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return None
    
    try:
        auth_url = 'https://www.reddit.com/api/v1/access_token'
        auth_data = {
            'grant_type': 'client_credentials',
            'device_id': 'DO_NOT_TRACK_THIS_DEVICE'
        }
        
        auth_response = requests.post(
            auth_url,
            data=auth_data,
            auth=(client_id, client_secret),
            headers={'User-Agent': 'RedditBot/1.0 by YourUsername'},
            timeout=10
        )
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            return token_data.get('access_token')
    except Exception as e:
        print(f"⚠️ OAuth 认证失败: {e}")
    
    return None


def fetch_subreddit_posts(subreddit: str, limit: int = 10, sort: str = 'top', time_period: str = 'day') -> List[Dict]:
    """
    从指定 Reddit 板块获取帖子
    
    Args:
        subreddit: 板块名称 (如 'stocks', 'bitcoin')
        limit: 获取帖子数量
        sort: 排序方式 ('top', 'hot', 'new')
        time_period: 时间范围 ('day', 'week', 'month', 'year', 'all')
    
    Returns:
        帖子列表,每个帖子包含 title, url, score, selftext, subreddit
    """
    # 尝试 OAuth 认证
    oauth_token = get_reddit_oauth_token()
    
    if oauth_token:
        # 使用 OAuth API
        url = f"https://oauth.reddit.com/r/{subreddit}/{sort}.json"
        headers = {
            'Authorization': f'bearer {oauth_token}',
            'User-Agent': 'RedditBot/1.0 by YourUsername'
        }
    else:
        # 使用公开 API
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
        headers = get_reddit_headers()
    
    # 设置请求参数
    params = {
        'limit': limit,
        't': time_period
    }
    
    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"正在获取 r/{subreddit} 的 {sort} 帖子... (尝试 {attempt + 1}/{max_retries})")
            
            # 添加随机延迟避免被限流
            if attempt > 0:
                delay = random.uniform(1, 3)
                print(f"⏳ 等待 {delay:.1f} 秒后重试...")
                time.sleep(delay)
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 403:
                print(f"❌ Reddit 403 错误: 可能被限制访问")
                if oauth_token:
                    print("🔄 OAuth token 可能已过期，尝试重新获取...")
                    oauth_token = get_reddit_oauth_token()
                    if oauth_token:
                        headers['Authorization'] = f'bearer {oauth_token}'
                        continue
                else:
                    print("💡 建议配置 REDDIT_CLIENT_ID 和 REDDIT_CLIENT_SECRET 使用 OAuth")
                break
            elif response.status_code == 429:
                print(f"⏳ Reddit 限流 (429)，等待更长时间...")
                time.sleep(random.uniform(5, 10))
                continue
            elif response.status_code == 200:
                break
            else:
                print(f"⚠️ HTTP {response.status_code}: {response.text[:100]}")
                if attempt == max_retries - 1:
                    break
                continue
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                break
            continue
        except requests.exceptions.RequestException as e:
            print(f"🌐 网络错误: {e} (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                break
            continue
    
    if response.status_code != 200:
        print(f"❌ 获取 r/{subreddit} 失败: HTTP {response.status_code}")
        return []
    
    try:
        data = response.json()
        
        posts = []
        for post_data in data['data']['children']:
            post = post_data['data']
            
            # 提取帖子信息
            post_info = {
                'title': post.get('title', ''),
                'url': f"https://reddit.com{post.get('permalink', '')}",
                'score': post.get('score', 0),
                'selftext': post.get('selftext', ''),
                'subreddit': post.get('subreddit', subreddit),
                'author': post.get('author', ''),
                'created_utc': post.get('created_utc', 0),
                'num_comments': post.get('num_comments', 0)
            }
            
            posts.append(post_info)
        
        print(f"✅ 成功获取 r/{subreddit} 的 {len(posts)} 个帖子")
        return posts
        
    except (KeyError, ValueError) as e:
        print(f"❌ 解析 r/{subreddit} 数据失败: {e}")
        return []
    except Exception as e:
        print(f"❌ 获取 r/{subreddit} 时发生未知错误: {e}")
        return []


def fetch_multiple_subreddits(
    subreddits: List[str],
    posts_per_subreddit: int = 2,
    *,
    sort: str = 'top',
    time_period: str = 'day',
) -> List[Dict]:
    """
    从多个 Reddit 板块获取帖子
    
    Args:
        subreddits: 板块名称列表
        posts_per_subreddit: 每个板块获取的帖子数量
    
    Returns:
        所有帖子的合并列表
    """
    all_posts = []
    
    for subreddit in subreddits:
        posts = fetch_subreddit_posts(
            subreddit,
            limit=posts_per_subreddit,
            sort=sort,
            time_period=time_period,
        )
        all_posts.extend(posts)
        
        # 添加延迟避免被限流
        time.sleep(0.5)
    
    # 按评分排序
    all_posts.sort(key=lambda x: x['score'], reverse=True)
    
    return all_posts


def format_post_for_display(post: Dict) -> str:
    """
    格式化单个帖子用于显示
    
    Args:
        post: 帖子数据字典
    
    Returns:
        格式化后的字符串
    """
    title = post['title']
    url = post['url']
    score = post['score']
    subreddit = post['subreddit']
    
    # 转义 Markdown 特殊字符
    title = title.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
    
    formatted = f"[{title}]({url})\n"
    formatted += f"⭐ 评分: {score} | 📍 r/{subreddit}"
    
    return formatted


if __name__ == "__main__":
    # 测试代码
    test_subreddits = ['stocks', 'bitcoin']
    posts = fetch_multiple_subreddits(
        test_subreddits,
        posts_per_subreddit=2,
        sort='new',
        time_period='day',
    )
    
    print(f"\n获取到 {len(posts)} 个帖子:")
    for i, post in enumerate(posts[:5], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   评分: {post['score']} | 板块: r/{post['subreddit']}")
        print(f"   链接: {post['url']}")
