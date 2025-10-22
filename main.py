"""
Reddit Telegram 自动推送机器人主程序
每天北京时间 09:00 自动抓取 Reddit 财经板块热门帖子并推送到 Telegram
"""

import os
import sys
from datetime import datetime
from datetime import timedelta
import sqlite3
from dotenv import load_dotenv

from reddit_fetcher import fetch_multiple_subreddits
from summarizer import summarize_post, format_summary_for_telegram
from social_fetcher import fetch_youtube_rss, fetch_nitter_rss
from truth_social_fetcher import fetch_truth_social
from truth_social_playwright import fetch_truth_social_playwright
from telegram_sender import send_message_with_retry, format_message_for_telegram, validate_telegram_config


def load_configuration():
    """加载环境配置"""
    load_dotenv()
    
    config = {
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('CHAT_ID'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'dry_run': os.getenv('DRY_RUN', '0') == '1',
        'filter_keywords': os.getenv('FILTER_KEYWORDS', ''),
    }
    
    # 验证必需配置
    if not config['telegram_bot_token'] and not config['dry_run']:
        print("❌ 错误: 未设置 TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    
    if not config['chat_id'] and not config['dry_run']:
        print("❌ 错误: 未设置 CHAT_ID")
        sys.exit(1)
    
    print("✅ 配置加载成功")
    return config


def get_target_subreddits():
    """获取目标 Reddit 板块列表"""
    return [
        'stocks',
        'wallstreetbets', 
        'investing',
        'cryptocurrency',
        'bitcoin',
        # 中美关系相关板块
        'China',
        'Sino',
        'China_News',
        'geopolitics',
        'worldnews',
        'politics',
        'news'
    ]


def process_posts(posts, gemini_api_key=None):
    """处理帖子,生成摘要"""
    processed_posts = []
    
    for post in posts:
        print(f"处理帖子: {post['title'][:50]}...")
        
        # 生成摘要
        summary = summarize_post(
            title=post['title'],
            text=post['selftext'],
            api_key=gemini_api_key
        )
        
        # 格式化摘要
        formatted_summary = format_summary_for_telegram(summary)
        
        # 添加到处理后的帖子
        processed_post = post.copy()
        processed_post['summary'] = formatted_summary
        processed_posts.append(processed_post)
    
    return processed_posts


def get_beijing_timestamp():
    """获取北京时间戳"""
    # GitHub Actions 运行在 UTC 时间
    # 北京时间 = UTC + 8
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    
    return beijing_time.strftime("%Y-%m-%d %H:%M")


def ensure_cache_table(conn):
    """确保去重缓存表存在"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pushed_posts (
            url TEXT PRIMARY KEY,
            pushed_at_utc INTEGER
        )
        """
    )
    conn.commit()


def is_recent(created_utc: float, freshness_hours: int = 2) -> bool:
    """判断帖子是否在指定小时内新鲜"""
    try:
        post_time = datetime.utcfromtimestamp(created_utc)
        return (datetime.utcnow() - post_time) <= timedelta(hours=freshness_hours)
    except Exception:
        return False


def filter_fresh_posts(posts, freshness_hours: int = 6):
    """智能过滤新鲜帖子，根据内容类型调整新鲜度要求"""
    current_time = datetime.now()
    fresh_posts = []
    
    for post in posts:
        try:
            created_time = datetime.fromtimestamp(post.get('created_utc', 0))
            hours_old = (current_time - created_time).total_seconds() / 3600
            
            # 智能新鲜度判断
            if hours_old <= 2:
                post['freshness_score'] = 3  # 非常新鲜
            elif hours_old <= 6:
                post['freshness_score'] = 2  # 比较新鲜
            elif hours_old <= 24:
                post['freshness_score'] = 1  # 一般新鲜
            else:
                post['freshness_score'] = 0  # 过时
            
            # 根据内容类型调整新鲜度要求
            title = post.get('title', '').lower()
            if any(keyword in title for keyword in ['breaking', 'urgent', 'live', 'just in']):
                # 突发新闻放宽到12小时
                if hours_old <= 12:
                    fresh_posts.append(post)
            elif any(keyword in title for keyword in ['analysis', 'opinion', 'review']):
                # 分析类文章放宽到48小时
                if hours_old <= 48:
                    fresh_posts.append(post)
            elif hours_old <= freshness_hours:
                fresh_posts.append(post)
                
        except Exception as e:
            print(f"⚠️ 时间解析错误: {e}")
            # 如果时间解析失败，默认包含
            fresh_posts.append(post)
    
    return fresh_posts


def filter_by_keywords(posts, keyword_csv: str):
    """按关键词过滤，仅对 Truth Social/Nitter 应用；为空不筛选。若筛空则自动放宽为“仅标题匹配”。"""
    kw = [k.strip().lower() for k in keyword_csv.split(',') if k.strip()]
    if not kw:
        return posts

    def is_social(p):
        src = (p.get('subreddit') or '').lower()
        return src in ('truth-social', 'trump-x')

    social, others = [], []
    for p in posts:
        (social if is_social(p) else others).append(p)

    # 严格：标题+正文
    strict = []
    for p in social:
        text = (p.get('title','') + "\n" + p.get('selftext','')).lower()
        if any(k in text for k in kw):
            strict.append(p)

    if strict:
        return strict + others

    # 放宽：仅标题
    relaxed = []
    for p in social:
        title = p.get('title','').lower()
        if any(k in title for k in kw):
            relaxed.append(p)

    return (relaxed if relaxed else social) + others


def filter_dedup(conn, posts, dedupe_hours: int = 24):
    """基于 SQLite 的去重，默认 24 小时内相同 URL 不重复推送"""
    now_ts = int(datetime.utcnow().timestamp())
    cutoff = now_ts - dedupe_hours * 3600

    # 清理过期记录
    conn.execute("DELETE FROM pushed_posts WHERE pushed_at_utc < ?", (cutoff,))
    conn.commit()

    results = []
    for p in posts:
        url = p.get('url')
        if not url:
            continue
        cur = conn.execute("SELECT 1 FROM pushed_posts WHERE url = ?", (url,))
        if cur.fetchone():
            continue
        results.append(p)
    return results


def calculate_content_score(post):
    """智能计算内容质量评分"""
    score = 0
    
    # 来源权重评分（更全面的权重体系）
    source_weights = {
        'UN News': 8, 'NATO News': 8, 'EU News': 7,
        'BBC World': 7, 'Reuters': 7, 'South China Morning Post': 6,
        'Foreign Policy': 6, 'Al Jazeera': 5, 'CNN': 5,
        'Wall Street Journal': 6, 'Financial Times': 6,
        'truth-social': 4, 'trump-youtube': 3, 'reddit': 2
    }
    
    source = post.get('source', post.get('subreddit', '')).lower()
    for key, weight in source_weights.items():
        if key.lower() in source:
            score += weight
            break
    else:
        score += 1  # 默认权重
    
    # 新鲜度评分（使用之前计算的分数）
    freshness_score = post.get('freshness_score', 0)
    score += freshness_score * 2  # 新鲜度权重加倍
    
    # 关键词重要性评分（更智能的关键词检测）
    title = post.get('title', '').lower()
    content = post.get('selftext', '').lower()
    text = f"{title} {content}"
    
    # 高优先级关键词
    high_priority_keywords = [
        'breaking', 'urgent', 'crisis', 'emergency', 'alert',
        'war', 'conflict', 'attack', 'bomb', 'explosion',
        'election', 'vote', 'president', 'congress', 'senate',
        'market crash', 'recession', 'inflation', 'fed', 'interest rate'
    ]
    
    # 中优先级关键词
    medium_priority_keywords = [
        'analysis', 'report', 'study', 'research', 'data',
        'policy', 'law', 'regulation', 'trade', 'tariff',
        'technology', 'ai', 'artificial intelligence', 'cyber'
    ]
    
    # 检查高优先级关键词
    for keyword in high_priority_keywords:
        if keyword in text:
            score += 4
            break
    
    # 检查中优先级关键词
    for keyword in medium_priority_keywords:
        if keyword in text:
            score += 2
            break
    
    # 内容质量评分
    content_length = len(post.get('selftext', ''))
    if content_length > 200:
        score += 2
    elif content_length > 100:
        score += 1
    
    # 标题质量评分
    title_length = len(title)
    if 20 <= title_length <= 100:  # 标题长度适中
        score += 1
    
    # 互动度评分（如果有的话）
    upvotes = post.get('ups', 0)
    comments = post.get('num_comments', 0)
    if upvotes > 100:
        score += 2
    elif upvotes > 50:
        score += 1
    
    if comments > 50:
        score += 1
    
    # 避免重复内容评分
    if 'repost' in text or 're:' in title.lower():
        score -= 2
    
    return max(0, score)  # 确保分数不为负


def score_and_sort_posts(posts):
    """对帖子进行评分和排序"""
    scored_posts = []
    for post in posts:
        score = calculate_content_score(post)
        post['quality_score'] = score
        scored_posts.append(post)
    
    # 按质量评分排序，评分相同时按时间排序
    return sorted(scored_posts, key=lambda x: (x['quality_score'], x.get('created_utc', 0)), reverse=True)


def smart_content_filter(posts):
    """智能内容过滤，去除低质量和重复内容"""
    if not posts:
        return posts
    
    filtered_posts = []
    seen_titles = set()
    seen_urls = set()
    
    for post in posts:
        # 基本质量检查
        quality_score = post.get('quality_score', 0)
        if quality_score < 3:  # 质量分数太低
            continue
        
        # 标题去重
        title = post.get('title', '').lower().strip()
        if not title or title in seen_titles:
            continue
        
        # URL去重
        url = post.get('url', '')
        if url in seen_urls:
            continue
        
        # 内容长度检查
        content = post.get('selftext', '')
        if len(content) < 20 and quality_score < 8:  # 内容太短且质量不高
            continue
        
        # 标题质量检查
        if len(title) < 10:  # 标题太短
            continue
        
        # 避免明显的垃圾内容
        spam_keywords = ['click here', 'free money', 'guaranteed', 'make money fast']
        if any(keyword in title for keyword in spam_keywords):
            continue
        
        # 通过所有检查
        filtered_posts.append(post)
        seen_titles.add(title)
        seen_urls.add(url)
    
    return filtered_posts


def mark_pushed(conn, posts):
    """将已推送的帖子写入去重表"""
    now_ts = int(datetime.utcnow().timestamp())
    for p in posts:
        url = p.get('url')
        if not url:
            continue
        try:
            conn.execute(
                "INSERT OR REPLACE INTO pushed_posts(url, pushed_at_utc) VALUES(?, ?)",
                (url, now_ts),
            )
        except Exception:
            pass
    conn.commit()


def main():
    """主程序入口"""
    print("🚀 Reddit Telegram Bot 启动")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        config = load_configuration()
        
        # 2. 验证 Telegram 配置
        if not config['dry_run']:
            print("🔍 验证 Telegram 配置...")
            if not validate_telegram_config(config['telegram_bot_token'], config['chat_id']):
                print("❌ Telegram 配置验证失败")
                sys.exit(1)
        else:
            print("🧪 DRY_RUN 模式：跳过 Telegram 校验与发送")
        
        # 3. 获取目标板块
        subreddits = get_target_subreddits()
        print(f"🎯 目标板块: {', '.join(subreddits)}")
        
        # 4. 抓取 Reddit 帖子（若受限可暂时跳过，仅抓取社交源）
        posts = []
        try:
            print("\n📡 开始抓取 Reddit 帖子...")
            reddit_posts = fetch_multiple_subreddits(
                subreddits,
                posts_per_subreddit=5,
                sort='new',
                time_period='day',
            )
            posts.extend(reddit_posts)
        except Exception:
            print("⚠️ Reddit 抓取异常，继续处理其他来源")

        # 4.1 抓取社交平台 (YouTube RSS 与 Nitter 备选)
        print("\n📺 抓取 YouTube 频道...")
        yt_channel = os.getenv('TRUMP_YT_CHANNEL_ID', '').strip()
        if not yt_channel:
            # 默认使用特朗普官方频道 ID，免配置可用
            yt_channel = 'UCp0hYYBW6IMayGgR-WeoCvQ'
            print("ℹ️ 未配置 TRUMP_YT_CHANNEL_ID，已使用默认频道ID")
        yt_posts = fetch_youtube_rss(channel_id=yt_channel, limit=5)
        if yt_posts:
            print(f"✅ YouTube: {len(yt_posts)} 条")
            posts.extend(yt_posts)
        else:
            print("⚠️ YouTube 未获取内容")

        print("\n🐦 抓取 Nitter (X 镜像)...")
        x_username = os.getenv('TRUMP_X_USERNAME', 'realDonaldTrump').strip()
        x_posts = fetch_nitter_rss(username=x_username, limit=5)
        if x_posts:
            print(f"✅ Nitter: {len(x_posts)} 条")
            posts.extend(x_posts)
        else:
            print("⚠️ Nitter 未获取内容 (可能限流/网络问题)")

        # 4.2 抓取中美关系新闻
        print("\n🇺🇸🇨🇳 抓取中美关系新闻...")
        try:
            from us_china_news_fetcher import fetch_us_china_news, filter_us_china_posts
            
            # 抓取专门的新闻源
            us_china_news = fetch_us_china_news(max_items=3)
            if us_china_news:
                print(f"✅ 中美关系新闻: {len(us_china_news)} 条")
                posts.extend(us_china_news)
            
            # 从 Reddit 帖子中过滤中美关系相关内容
            us_china_reddit = filter_us_china_posts(posts)
            if us_china_reddit:
                print(f"✅ Reddit 中美关系帖子: {len(us_china_reddit)} 条")
                # 移除原帖子中的中美关系内容，避免重复
                posts = [p for p in posts if not p.get('category') == '中美关系']
                posts.extend(us_china_reddit)
                
        except Exception as e:
            print(f"⚠️ 中美关系新闻抓取失败: {e}")

        # 4.3 抓取国际关系动态
        print("\n🌍 抓取国际关系动态...")
        try:
            from international_relations_fetcher import fetch_international_organizations, fetch_conflict_news
            
            # 抓取国际组织动态
            intl_org_news = fetch_international_organizations(max_items=2)
            if intl_org_news:
                print(f"✅ 国际组织动态: {len(intl_org_news)} 条")
                posts.extend(intl_org_news)
            
            # 抓取地区冲突动态
            conflict_news = fetch_conflict_news(max_items=2)
            if conflict_news:
                print(f"✅ 地区冲突动态: {len(conflict_news)} 条")
                posts.extend(conflict_news)
                
        except Exception as e:
            print(f"⚠️ 国际关系动态抓取失败: {e}")

        # 4.4 Truth Social（优先第三方数据集；无配置则使用 Playwright 抓取）
        print("\n📰 抓取 Truth Social...")
        ts_dataset = os.getenv('TRUTH_SOCIAL_DATASET_URL', '').strip()
        ts_token = os.getenv('APIFY_TOKEN', '').strip() or None
        if ts_dataset:
            ts_posts = fetch_truth_social(ts_dataset, limit=10, token=ts_token)
            if ts_posts:
                print(f"✅ Truth Social: {len(ts_posts)} 条")
                posts.extend(ts_posts)
            else:
                print("⚠️ Truth Social 未获取内容")
        else:
            print("ℹ️ 未配置数据集，尝试本地无头抓取（Playwright）...")
            ts_pw_posts = fetch_truth_social_playwright(username='realDonaldTrump', limit=10)
            if ts_pw_posts:
                print(f"✅ Truth Social(Playwright): {len(ts_pw_posts)} 条")
                posts.extend(ts_pw_posts)
            else:
                print("⚠️ Truth Social(Playwright) 未获取内容（已回退缓存策略）")
        
        # 4.3 智能新鲜度过滤
        fresh_posts = filter_fresh_posts(posts, freshness_hours=6)
        print(f"🕒 智能新鲜度过滤后: {len(fresh_posts)} 个帖子")

        # 4.4 关键词过滤（可选）
        filtered_posts = filter_by_keywords(fresh_posts, config.get('filter_keywords',''))
        if config.get('filter_keywords'):
            print(f"🔎 关键词过滤后: {len(filtered_posts)} 个（关键词: {config.get('filter_keywords')}）")
        else:
            filtered_posts = fresh_posts

        # 4.5 基于 SQLite 的去重（24 小时）；DRY_RUN 下跳过去重，便于本地预览
        conn = sqlite3.connect('news_cache.db')
        ensure_cache_table(conn)
        if config['dry_run']:
            posts = filtered_posts
            print(f"♻️ DRY_RUN 跳过去重: {len(posts)} 个帖子")
        else:
            unique_posts = filter_dedup(conn, filtered_posts, dedupe_hours=24)
            print(f"♻️ 去重后: {len(unique_posts)} 个帖子")
            posts = unique_posts

        # 4.6 智能内容质量评分和排序
        posts = score_and_sort_posts(posts)
        print(f"📊 智能内容质量评分完成，最高分: {posts[0]['quality_score'] if posts else 0}")
        
        # 4.7 智能去重和内容质量过滤
        posts = smart_content_filter(posts)
        print(f"🧠 智能内容过滤后: {len(posts)} 个帖子")
        
        # 4.7 动态推送数量控制
        base_limit = 15  # 基础限制从10增加到15
        time_of_day = datetime.now().hour
        if 6 <= time_of_day <= 12:  # 早上推送更多
            push_limit = min(base_limit + 5, len(posts))
        elif 18 <= time_of_day <= 22:  # 晚上正常推送
            push_limit = min(base_limit, len(posts))
        else:  # 其他时间适中推送
            push_limit = min(base_limit + 2, len(posts))
        
        posts = posts[:push_limit]
        print(f"📊 动态推送限制: {push_limit} 条（原始: {len(posts)} 条）")

        # 4.7 兜底策略：如果没有任何内容，尝试从缓存获取
        if not posts:
            print("🔄 所有抓取源都失败，尝试从缓存获取内容...")
            try:
                from truth_social_playwright import load_truth_cache
                cached_posts = load_truth_cache(max_age_hours=48)
                if cached_posts:
                    print(f"📦 从缓存获取到 {len(cached_posts)} 个帖子")
                    posts = cached_posts[:5]  # 限制缓存内容数量
                else:
                    print("❌ 缓存也为空，无法获取任何内容")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ 缓存获取失败: {e}")
                sys.exit(1)
        
        print(f"✅ 成功获取 {len(posts)} 个帖子")
        
        # 5. 处理帖子 (生成摘要)
        print("\n🤖 开始处理帖子...")
        processed_posts = process_posts(posts, config['gemini_api_key'])
        
        # 6. 格式化消息
        print("\n📝 格式化消息...")
        timestamp = get_beijing_timestamp()
        message = format_message_for_telegram(processed_posts, timestamp)
        
        # 7. 发送到 Telegram 或打印
        if config['dry_run']:
            print("\n📤 DRY_RUN：打印消息，不发送 Telegram")
            print("\n====== 预览开始 ======")
            print(message)
            print("====== 预览结束 ======\n")
            # DRY_RUN 下不写入已推送标记，避免影响下次预览
            print("🎉 任务完成! DRY_RUN 预览成功")
        else:
            print("\n📤 发送消息到 Telegram...")
            success = send_message_with_retry(
                config['telegram_bot_token'],
                config['chat_id'],
                message
            )
            
            if success:
                # 7.1 标记已推送用于后续去重
                try:
                    mark_pushed(conn, processed_posts)
                except Exception:
                    pass
                print("🎉 任务完成! 消息已成功发送到 Telegram")
            else:
                print("❌ 任务失败! 消息发送失败")
                sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
