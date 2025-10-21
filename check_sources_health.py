#!/usr/bin/env python3
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def main():
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception as e:
        log(f"读取 sources.json 失败: {e}")
        return 1

    sources = []
    for s in cfg.get('primary', []):
        sources.append((s['name'], s['url']))
    for s in cfg.get('secondary', []):
        sources.append((s['name'], s['url']))

    social_groups = cfg.get('social_groups', {})
    nitter_mirrors = cfg.get('nitter_mirrors', ['https://nitter.net'])
    base = nitter_mirrors[0].rstrip('/')
    for _, group in social_groups.items():
        if group.get('enabled'):
            for handle in group.get('accounts', []):
                sources.append((f"Twitter-{handle}", f"{base}/{handle}/rss"))

    report = []
    freshness_cutoff = datetime.utcnow() - timedelta(hours=24)

    for name, url in sources:
        try:
            r = requests.get(url, timeout=10, headers={'User-Agent':'Mozilla/5.0','Accept':'application/rss+xml,application/xml,text/xml,*/*'})
            ok = r.status_code == 200
            if ok:
                try:
                    root = ET.fromstring(r.text)
                    # 新鲜度检查：若存在 pubDate/updated，至少有一条在24h内
                    fresh_ok = True
                    try:
                        items = root.findall('.//item') or root.findall('.//entry')
                        fresh_found = False
                        for item in items[:10]:  # 采样前10条
                            for tag in ('pubDate', '{http://www.w3.org/2005/Atom}updated', 'updated', 'date'):
                                elem = item.find(tag)
                                if elem is not None and elem.text:
                                    try:
                                        # 粗略多格式解析
                                        txt = elem.text.strip()
                                        # 常见 RSS/HTTP 日期格式
                                        from email.utils import parsedate_to_datetime
                                        dt = None
                                        try:
                                            dt = parsedate_to_datetime(txt)
                                        except Exception:
                                            pass
                                        if dt is None:
                                            # ISO
                                            try:
                                                dt = datetime.fromisoformat(txt.replace('Z', '+00:00'))
                                            except Exception:
                                                pass
                                        if dt and dt.tzinfo:
                                            dt = dt.astimezone(tz=None).replace(tzinfo=None)
                                        if dt and dt >= freshness_cutoff:
                                            fresh_found = True
                                            break
                                    except Exception:
                                        continue
                            if fresh_found:
                                break
                        fresh_ok = fresh_found  # 要求至少一条为24h内
                    except Exception:
                        fresh_ok = True  # 没法解析时不因新鲜度直接判死

                    ok = ok and fresh_ok
                except Exception as e:
                    ok = False
            report.append((name, url, ok, r.status_code))
            time.sleep(0.5)
        except Exception as e:
            report.append((name, url, False, str(e)))

    # 打印报告
    good = [x for x in report if x[2]]
    bad = [x for x in report if not x[2]]
    log(f"健康: {len(good)} 失效/异常: {len(bad)} 总计: {len(report)}")
    for name, url, ok, extra in bad[:50]:
        log(f"[FAIL] {name} -> {url} -> {extra}")

    return 0

if __name__ == '__main__':
    raise SystemExit(main())


