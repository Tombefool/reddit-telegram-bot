"""
社交平台抓取模块
支持:
- YouTube 频道 RSS (推荐)
- Nitter 镜像 RSS (可选,稳定性较差)
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional


def _parse_datetime_to_utc_ts(text: str) -> int:
    """将 RSS 日期字符串解析为 UTC 时间戳"""
    try:
        # 优先使用 RFC822
        dt = None
        try:
            dt = parsedate_to_datetime(text)
        except Exception:
            dt = None
        if dt is None:
            # 尝试 ISO 格式
            try:
                dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            except Exception:
                return 0
        if dt.tzinfo:
            dt = dt.astimezone(tz=None).replace(tzinfo=None)
        return int(dt.timestamp())
    except Exception:
        return 0


def fetch_youtube_rss(channel_id: str, limit: int = 5) -> List[Dict]:
    """
    拉取 YouTube 频道 RSS 最近发布的视频
    返回结构与 reddit_fetcher 保持一致的字段:
    - title, url, score, selftext, subreddit, author, created_utc, num_comments
    """
    if not channel_id:
        return []

    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.text)
        # Atom feed namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        entries = root.findall('atom:entry', ns)
        posts: List[Dict] = []
        for e in entries[:limit]:
            title_elem = e.find('atom:title', ns)
            link_elem = e.find('atom:link', ns)
            updated_elem = e.find('atom:updated', ns)
            author_elem = e.find('atom:author/atom:name', ns)

            title = title_elem.text if title_elem is not None else ''
            link = link_elem.get('href') if link_elem is not None else ''
            created_ts = _parse_datetime_to_utc_ts(updated_elem.text) if updated_elem is not None else 0
            author = author_elem.text if author_elem is not None else 'YouTube'

            posts.append({
                'title': title,
                'url': link,
                'score': 0,
                'selftext': '',
                'subreddit': 'trump-youtube',  # 用作分组显示
                'author': author,
                'created_utc': created_ts,
                'num_comments': 0,
            })
        return posts
    except Exception:
        return []


def resolve_youtube_channel_id_from_url_or_handle(url_or_handle: str) -> Optional[str]:
    """
    通过 YouTube 频道 URL 或 @handle 解析出 channel_id (UC 开头)
    无需 API Key，解析页面中的 canonical 或 JSON 片段
    """
    if not url_or_handle:
        return None
    try:
        target = url_or_handle.strip()
        if target.startswith('@'):
            target = f"https://www.youtube.com/{target}"
        elif target.startswith('youtube.com') or target.startswith('www.youtube.com'):
            target = 'https://' + target
        elif target.startswith('http'):
            pass
        else:
            # 兜底认为是 handle
            target = f"https://www.youtube.com/@{target}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'
        }
        r = requests.get(target, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        html = r.text
        # 常见位置1: <link rel="canonical" href="https://www.youtube.com/channel/UCxxxx">
        import re
        m = re.search(r"https://www\.youtube\.com/channel/(UC[\w-]+)", html)
        if m:
            return m.group(1)
        # 常见位置2: "channelId":"UCxxxx"
        m = re.search(r'"channelId"\s*:\s*"(UC[\w-]+)"', html)
        if m:
            return m.group(1)
        return None
    except Exception:
        return None

def fetch_nitter_rss(username: str, limit: int = 5) -> List[Dict]:
    """
    通过 Nitter RSS 拉取用户推文 (稳定性较差,可能 429)
    """
    if not username:
        return []
    url = f"https://nitter.net/{username}/rss"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.text)
        items = root.findall('.//item')
        posts: List[Dict] = []
        for it in items[:limit]:
            title_elem = it.find('title')
            link_elem = it.find('link')
            pub_elem = it.find('pubDate')
            title = title_elem.text if title_elem is not None else ''
            link = link_elem.text if link_elem is not None else ''
            created_ts = _parse_datetime_to_utc_ts(pub_elem.text) if pub_elem is not None else 0
            posts.append({
                'title': title,
                'url': link,
                'score': 0,
                'selftext': '',
                'subreddit': 'trump-x',
                'author': username,
                'created_utc': created_ts,
                'num_comments': 0,
            })
        return posts
    except Exception:
        return []


