"""
Reddit 数据抓取模块
从 Reddit 公开 JSON API 获取指定板块的热门帖子
"""

import requests
import time
from typing import List, Dict, Optional


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
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    
    # 设置请求参数
    params = {
        'limit': limit,
        't': time_period
    }
    
    # 设置 User-Agent 避免被 Reddit 拒绝
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print(f"正在获取 r/{subreddit} 的 {sort} 帖子...")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
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
        
        print(f"成功获取 r/{subreddit} 的 {len(posts)} 个帖子")
        return posts
        
    except requests.exceptions.RequestException as e:
        print(f"获取 r/{subreddit} 帖子失败: {e}")
        return []
    except (KeyError, ValueError) as e:
        print(f"解析 r/{subreddit} 数据失败: {e}")
        return []
    except Exception as e:
        print(f"获取 r/{subreddit} 时发生未知错误: {e}")
        return []


def fetch_multiple_subreddits(subreddits: List[str], posts_per_subreddit: int = 2) -> List[Dict]:
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
        posts = fetch_subreddit_posts(subreddit, limit=posts_per_subreddit)
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
    posts = fetch_multiple_subreddits(test_subreddits, posts_per_subreddit=2)
    
    print(f"\n获取到 {len(posts)} 个帖子:")
    for i, post in enumerate(posts[:5], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   评分: {post['score']} | 板块: r/{post['subreddit']}")
        print(f"   链接: {post['url']}")
