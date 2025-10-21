"""
Truth Social 抓取模块（基于第三方爬虫数据集）

推荐通过 Apify 等第三方服务抓取 Truth Social，并暴露为 Dataset Items API：
  TRUTH_SOCIAL_DATASET_URL = https://api.apify.com/v2/datasets/<DATASET_ID>/items?clean=true
  可选 APIFY_TOKEN 用于私有数据集访问（Bearer 头）。

返回与 reddit_fetcher 兼容的结构字段：
  title, url, score, selftext, subreddit, author, created_utc, num_comments
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional


def _to_ts(dt_text: str) -> int:
    if not dt_text:
        return 0
    try:
        # 兼容 ISO8601，例如 2025-01-01T12:34:56.000Z
        dt = datetime.fromisoformat(dt_text.replace('Z', '+00:00'))
        if dt.tzinfo:
            dt = dt.astimezone(tz=None).replace(tzinfo=None)
        return int(dt.timestamp())
    except Exception:
        return 0


def fetch_truth_social(dataset_url: str, *, limit: int = 10, token: Optional[str] = None) -> List[Dict]:
    """
    从第三方数据集接口读取 Truth Social 帖子

    期望数据集每项包含：
      - text / content
      - url / link（原帖链接）
      - createdAt / publishedAt
      - author / username（可选）
    """
    if not dataset_url:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36',
        'Accept': 'application/json',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        resp = requests.get(dataset_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []
        items = resp.json()
        posts: List[Dict] = []
        for it in items[:limit]:
            text = it.get('text') or it.get('content') or ''
            url = it.get('url') or it.get('link') or ''
            created = it.get('createdAt') or it.get('publishedAt') or ''
            author = it.get('author') or it.get('username') or 'truth-social'

            title = text.strip().split('\n', 1)[0][:120] if text else 'Truth Social 更新'
            created_ts = _to_ts(created)

            posts.append({
                'title': title,
                'url': url,
                'score': 0,
                'selftext': text,
                'subreddit': 'truth-social',
                'author': author,
                'created_utc': created_ts,
                'num_comments': 0,
            })
        return posts
    except Exception:
        return []


