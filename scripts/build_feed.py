#!/usr/bin/env python3
"""Build the static RSS + JSON API for CCD-AIGC/daily-hotlist.

Reads data/*.json (ai-intel / repo-radar / content-radar / ai-news /
hotlist / tracker) and writes, all under the repo root:

  feed.xml, feed/ai-intel.xml, feed/repo-radar.xml,
  feed/content-radar.xml, feed/indie-sites.xml, feed/daily.xml,
  api/v1/latest.json, api/v1/hot.json, api/v1/daily/YYYY-MM-DD.json,
  api/v1/search.json, api/v1/ai-news.json, api/v1/index.json,
  openapi.json, agent.md, feed.html

Stdlib only. No network. No arguments. Dates are never hardcoded:
everything is scanned from data/*.json, windows are relative to the
latest date found in the data.

Usage: python3 scripts/build_feed.py
"""
import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://ccd-aigc.github.io/daily-hotlist"
CST = timezone(timedelta(hours=8))

# Fallback slot time per series, used only when the source JSON has no
# usable fetched_at_cst / generated_at_cst. Never the script run time.
SLOT = {"ai-intel": (8, 30), "repo-radar": (8, 30),
        "content-radar": (12, 0), "ai-news": (9, 51)}
PRIORITY = {"ai-intel": 0, "repo-radar": 1, "content-radar": 2, "indie": 3}
CATEGORY = {"ai-intel": "AI商业情报", "repo-radar": "GitHub早期爆款",
            "content-radar": "AI内容格式", "indie": "AI独立站",
            "ai-news": "AI创业信息流"}
ARCHIVE = {"ai-intel": "archive/ai-intel-{d}.html",
           "repo-radar": "archive/repo-radar-{d}.html",
           "content-radar": "archive/content-radar-{d}.html",
           "indie": "archive/content-radar-{d}.html"}

CSS = """
:root{color-scheme:light;--bg:#f4f5f7;--card:#fff;--ink:#1c2333;--muted:#667085;--line:#e6e8ee;--blue:#2563eb}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.65}
.wrap{max-width:980px;margin:0 auto;padding:0 16px 56px}
.hero{background:linear-gradient(135deg,#0f172a,#2563eb 60%,#0ea5e9);color:#fff;padding:36px 0 28px}
.hero h1{margin:0 0 8px;font-size:30px;line-height:1.25}
.hero p{margin:4px 0;color:#dbeafe;font-size:15px}
.date-pill{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);padding:4px 12px;border-radius:999px;font-size:14px;margin-bottom:14px}
h2{font-size:21px;margin:34px 0 12px}h2 small{display:block;font-size:13px;color:var(--muted);font-weight:400;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 1px 3px rgba(16,24,40,.06)}
.card-top{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:8px}
.card h3{margin:0 0 6px;font-size:17px;line-height:1.5}.card h3 a{color:var(--ink);text-decoration:none}
.card p{margin:6px 0;color:var(--muted);font-size:14px}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}
.row{display:flex;align-items:center;gap:10px;padding:13px 0;border-bottom:1px solid #f0f1f4}
.row:last-child{border-bottom:0}
.rank{flex:0 0 28px;height:28px;line-height:28px;text-align:center;border-radius:50%;background:#eef0f4;color:#475467;font-weight:800;font-size:14px}
.row-title{flex:1;font-size:16px;line-height:1.55}.row-title a{color:var(--ink);text-decoration:none}
.src{flex:0 0 auto;color:var(--muted);font-size:12px;max-width:150px;text-align:right}
.badge{flex:0 0 auto;font-size:12px;padding:3px 8px;border-radius:999px;white-space:nowrap}
.badge.new{background:#dcfce7;color:#166534;font-weight:700}.badge.up{background:#dbeafe;color:#1e40af}
.badge.down{background:#fee2e2;color:#991b1b}.badge.same{background:#f2f4f7;color:#667085}
.btn{display:inline-block;padding:8px 14px;border-radius:999px;background:var(--blue);color:#fff;text-decoration:none;font-size:14px}
.btn.ghost{background:#fff;color:var(--blue);border:1px solid var(--line)}
.note-box{background:#fffbeb;border:1px solid #fde68a;border-radius:16px;padding:16px}
.note-box li{margin:6px 0}
.chips a{display:inline-block;margin:0 8px 8px 0;padding:8px 14px;border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--blue);text-decoration:none}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden}
th,td{border-bottom:1px solid #f0f1f4;padding:10px 12px;text-align:left;font-size:14px;vertical-align:top}
th{background:#f8fafc;color:#475467;white-space:nowrap}
tr:last-child td{border-bottom:0}
footer{margin-top:36px;color:var(--muted);font-size:13px;text-align:center}
@media(max-width:560px){.hero h1{font-size:25px}.row-title{font-size:15px}.src{display:none}}
"""


def esc(s):
    import html as _h
    return _h.escape(str(s or ""), quote=True)


def trunc(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def parse_time(raw, date, source):
    """Parse 'YYYY-MM-DD HH:MM' (tolerates a leading '约'). Falls back
    to the series' daily slot time on the file date. Never now()."""
    if raw:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s*(?:约\s*)?(\d{1,2}):(\d{2})",
                      str(raw))
        if m:
            y, mo, d, h, mi = map(int, m.groups())
            return datetime(y, mo, d, h, mi, tzinfo=CST)
    h, mi = SLOT[source]
    y, mo, d = map(int, date.split("-"))
    return datetime(y, mo, d, h, mi, tzinfo=CST)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def rfc2822(dt):
    return format_datetime(dt.astimezone(timezone.utc))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def yyyymmdd(date):
    return date.replace("-", "")


# ---------------------------------------------------------------- items

def build_items():
    """Scan all history data/*.json -> unified items (unsorted)."""
    items = []
    seq = [0]

    def add(source, date, dt, title, summary, link, source_url="",
            score=None, verdict=None, item_id=None, category=None):
        seq[0] += 1
        items.append({
            "id": item_id, "title": title, "summary": summary,
            "link": BASE + "/" + link, "source_url": source_url or "",
            "category": category or CATEGORY[source], "source": source,
            "score": score, "verdict": verdict,
            "published_at": iso(dt), "date": date,
            "_dt": dt, "_pri": PRIORITY[source], "_seq": seq[0],
        })

    data_dir = ROOT / "data"
    if not data_dir.is_dir():
        return items

    # ---- ai-intel: top7 + opportunities
    for path in sorted(data_dir.glob("ai-intel-[0-9]*.json")):
        m = re.fullmatch(r"ai-intel-(\d{4}-\d{2}-\d{2})\.json", path.name)
        if not m:
            continue
        date = m.group(1)
        try:
            d = load_json(path)
        except Exception:
            continue
        dt = parse_time(d.get("fetched_at_cst"), date, "ai-intel")
        for i, t in enumerate(d.get("top7", [])):
            title = trunc((t.get("company", "") + "：" +
                           t.get("event", "")), 60)
            if not title.strip("："):
                continue
            add("ai-intel", date, dt, title,
                trunc(t.get("commercial_value", ""), 300),
                ARCHIVE["ai-intel"].format(d=date),
                t.get("source_url", ""), score=None,
                item_id=f"ai-intel-{yyyymmdd(date)}-{i:02d}")
        for i, o in enumerate(d.get("opportunities", [])):
            t = o.get("title", "")
            if not t:
                continue
            add("ai-intel", date, dt,
                trunc(f"[AI商业情报 机会 {o.get('score', '')}分] {t}", 80),
                trunc(o.get("need", ""), 300),
                ARCHIVE["ai-intel"].format(d=date), "",
                score=o.get("score"),
                item_id=f"ai-intel-opp-{yyyymmdd(date)}-{i:02d}")

    # ---- repo-radar: top_potential + new_projects (dedup repo+date)
    for path in sorted(data_dir.glob("repo-radar-[0-9]*.json")):
        m = re.fullmatch(r"repo-radar-(\d{4}-\d{2}-\d{2})\.json", path.name)
        if not m:
            continue
        date = m.group(1)
        try:
            d = load_json(path)
        except Exception:
            continue
        dt = parse_time(d.get("generated_at_cst"), date, "repo-radar")
        seen_repos = set()
        for i, t in enumerate(d.get("top_potential", [])):
            repo = t.get("repo", "")
            if not repo or repo in seen_repos:
                continue
            seen_repos.add(repo)
            stars = t.get("stars", "")
            summary = trunc(f"{stars}★ · {t.get('basis', '')} · "
                            f"上手：{t.get('setup', '')}", 300)
            add("repo-radar", date, dt,
                trunc(f"[GitHub雷达 {t.get('score', '')}分] {repo} — "
                      f"{t.get('what', '')}", 90),
                summary, ARCHIVE["repo-radar"].format(d=date),
                f"https://github.com/{repo}",
                score=t.get("score"),
                item_id=f"repo-radar-{yyyymmdd(date)}-{i:02d}")
        for i, t in enumerate(d.get("new_projects", [])):
            repo = t.get("repo", "")
            if not repo or repo in seen_repos:
                continue
            seen_repos.add(repo)
            add("repo-radar", date, dt,
                trunc(f"[GitHub雷达 {t.get('score', '')}分] {repo} — "
                      f"{t.get('what', '')}", 90),
                trunc(t.get("what", ""), 300),
                ARCHIVE["repo-radar"].format(d=date),
                f"https://github.com/{repo}",
                score=t.get("score"),
                item_id=f"repo-radar-new-{yyyymmdd(date)}-{i:02d}")

    # ---- content-radar: formats (worth trying only) + indie_sites
    for path in sorted(data_dir.glob("content-radar-[0-9]*.json")):
        m = re.fullmatch(r"content-radar-(\d{4}-\d{2}-\d{2})\.json",
                         path.name)
        if not m:
            continue
        date = m.group(1)
        try:
            d = load_json(path)
        except Exception:
            continue
        dt = parse_time(d.get("generated_at_cst"), date, "content-radar")
        seen_fmt = set()
        for i, f in enumerate(d.get("formats", [])):
            if f.get("verdict") != "值得低成本试":
                continue
            name = f.get("name", "")
            if not name or name in seen_fmt:
                continue
            seen_fmt.add(name)
            add("content-radar", date, dt,
                trunc(f"[内容雷达 {f.get('score', '')}分] {name} — "
                      f"值得低成本试", 90),
                trunc(f.get("verdict_note", ""), 300),
                ARCHIVE["content-radar"].format(d=date), "",
                score=f.get("score"), verdict="值得低成本试",
                item_id=f"content-radar-{yyyymmdd(date)}-{i:02d}")
        seen_dom = set()
        for i, s in enumerate(d.get("indie_sites", [])):
            dom = s.get("domain", "")
            if not dom or dom in seen_dom:
                continue
            seen_dom.add(dom)
            summary = trunc(s.get("verdict_note", ""), 300)
            if "创始人自述" in str(s.get("verification", "")):
                summary += "（创始人自述，未独立核实）"
            add("indie", date, dt,
                trunc(f"[新站 {s.get('verdict', '')}] {s.get('name', '')}"
                      f"（{dom}）— {s.get('what', '')}", 90),
                summary, ARCHIVE["indie"].format(d=date),
                s.get("url", ""), verdict=s.get("verdict"),
                item_id=f"indie-{yyyymmdd(date)}-{i:02d}")

    # ---- dedup by id (keep first), then sort
    seen, uniq = set(), []
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        uniq.append(it)
    uniq.sort(key=lambda x: (-x["_dt"].timestamp(), x["_pri"], x["_seq"]))
    return uniq


def pub(item):
    return {k: v for k, v in item.items() if not k.startswith("_")}


# ---------------------------------------------------------------- rss

def rss_doc(title, desc, self_path, items):
    last = rfc2822(items[0]["_dt"]) if items else rfc2822(
        datetime.now(CST))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
           "<channel>", f"<title>{esc(title)}</title>",
           f"<link>{BASE}/hub.html</link>",
           f"<description>{esc(desc)}</description>",
           "<language>zh-CN</language>",
           f'<atom:link href="{BASE}/{self_path}" rel="self" '
           'type="application/rss+xml" />',
           f"<lastBuildDate>{last}</lastBuildDate>"]
    for it in items:
        out.append("<item>")
        out.append(f"<title>{esc(it['title'])}</title>")
        out.append(f"<link>{esc(it['link'])}</link>")
        out.append(f"<guid isPermaLink=\"false\">{esc(it['id'])}</guid>")
        out.append(f"<pubDate>{rfc2822(it['_dt'])}</pubDate>")
        out.append(f"<category>{esc(it['category'])}</category>")
        out.append(f"<description>{esc(it['summary'])}</description>")
        out.append("</item>")
    out += ["</channel>", "</rss>", ""]
    return "\n".join(out)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump_json(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


# ---------------------------------------------------------------- html

def feed_html(all_items, ref_date, per_day):
    feeds = [
        ("主源 feed.xml", "三个主力系列混合，按时间倒序", "feed.xml"),
        ("AI商业情报 feed/ai-intel.xml", "每天 08:30 的 TOP7 + 机会",
         "feed/ai-intel.xml"),
        ("GitHub早期爆款 feed/repo-radar.xml", "每天 08:30 的雷达 TOP10",
         "feed/repo-radar.xml"),
        ("AI内容雷达 feed/content-radar.xml", "每天 12:00 值得低成本试的格式",
         "feed/content-radar.xml"),
        ("新爆款AI独立站 feed/indie-sites.xml", "每天 0–5 个首次发现",
         "feed/indie-sites.xml"),
        ("日报 feed/daily.xml", "一天一条，各系列条数汇总",
         "feed/daily.xml"),
    ]
    cards = []
    for name, note, url in feeds:
        full = f"{BASE}/{url}"
        cards.append(
            f'<article class="card"><span class="tag">RSS 2.0</span>'
            f"<h3>{esc(name)}</h3><p>{esc(note)}</p>"
            f'<p><code>{esc(full)}</code></p>'
            f'<p><button class="btn" data-copy="{esc(full)}">一键复制订阅地址'
            f"</button> "
            f'<a class="btn ghost" href="{esc(url)}">打开</a></p></article>')
    recent = sorted(per_day.keys(), reverse=True)[:7]
    arch = "".join(
        f'<a href="./archive/{d}.html">{d}</a> ' for d in recent)
    latest = all_items[0] if all_items else None
    latest_line = (f"最新一条：{latest['title']}（{latest['published_at']}）"
                   if latest else "暂无条目")
    js = """
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){
  b.addEventListener('click', function(){
    var t = b.getAttribute('data-copy');
    function done(){ b.textContent = '已复制'; setTimeout(function(){ b.textContent = '一键复制订阅地址'; }, 1500); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t).then(done, function(){ fallback(); });
    } else { fallback(); }
    function fallback(){
      var ta = document.createElement('textarea');
      ta.value = t; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch(e) {}
      document.body.removeChild(ta); done();
    }
  });
});
</script>
"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Radar RSS 订阅 — CCD-AIGC daily-hotlist</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">更新于 {esc(ref_date)}</span>
<h1>AI Radar RSS 订阅</h1>
<p>每天的原创筛选，不是转载聚合：AI商业情报 TOP7、GitHub 24h 快涨仓库、海外先火国内未火的 AI 视频格式、新爆款 AI 独立站。</p>
<p>{esc(latest_line)}</p>
</div></header>
<div class="wrap">
<h2>这是什么<small>订阅方式、多久更新、给谁用</small></h2>
<div class="note-box"><ul>
<li>主源 feed.xml 每天更新：AI 商业情报（08:30）、GitHub 早期爆款雷达（08:30）、AI 内容雷达（12:00）三个主力系列混合，按发布时间倒序，近 30 天、最多 50 条。</li>
<li>给 agent 用的 JSON API 在 api/v1/：latest.json（近 7 天，最多 100 条）、hot.json（当天评分最高前 10 条）、daily/ 按天拆分、search.json 全量索引、ai-news.json（最新一期标题 + 原文链接）。说明见 agent.md，接口定义见 openapi.json。</li>
<li>这是静态文件托管，没有服务器：?limit= / ?window= / ?q= 不是服务器端参数，客户端拿到 JSON 后自己按 limit / window / category 过滤。建议 30 分钟刷一次，不要每分钟刷。</li>
<li>GitHub Pages 的静态文件没有精细的 Cache-Control / ETag 控制；feed.xml 的 Content-Type 可能是 application/xml 而不是 application/rss+xml，这是 GitHub Pages 的默认行为，订阅器一般都能正常解析。</li>
<li>标题和摘要全部来自我们自己的筛选原文；LearnPrompt 等来源只学接口形态，不转载原文；ai-news 只给标题 + 原文链接，不写我们没核实的摘要。</li>
</ul></div>
<h2>订阅源<small>点按钮复制地址，粘贴到 RSS 阅读器或 agent 配置里</small></h2>
<div class="grid">
{''.join(cards)}
</div>
<h2>给 agent 的文档<small>JSON API 与调用说明</small></h2>
<div class="grid">
<article class="card"><span class="tag">说明</span><h3>agent.md</h3>
<p>订阅方式、刷新频率、字段含义、示例 curl。</p>
<p><a class="btn" href="agent.md">打开 agent.md</a></p></article>
<article class="card"><span class="tag">OpenAPI 3.1</span><h3>openapi.json</h3>
<p>全部静态端点的机器可读定义。</p>
<p><a class="btn" href="openapi.json">打开 openapi.json</a></p></article>
<article class="card"><span class="tag">JSON API</span><h3>api/v1/latest.json</h3>
<p>近 7 天全部条目，最多 100 条，按时间倒序。</p>
<p><a class="btn" href="api/v1/latest.json">打开 latest.json</a>
<a class="btn ghost" href="api/v1/index.json">端点目录</a></p></article>
</div>
<h2>往期存档入口<small>最近 7 天的日榜存档，全部系列见 hub</small></h2>
<p class="chips">{arch}<a href="hub.html">全部系列入口 hub →</a></p>
</div>
{js}
</body>
</html>
"""


def agent_md():
    return f"""# CCD-AIGC daily-hotlist — 给 agent 的订阅与调用说明

> 每天的原创筛选，不是转载聚合：AI 商业情报 TOP7、GitHub 24h 快涨仓库、海外先火国内未火的 AI 视频格式、新爆款 AI 独立站。
> 全部内容由 CCD-AIGC/daily-hotlist 每天定时生成，托管在 GitHub Pages 上。

## 订阅（RSS 2.0）

主源（三个主力系列混合，按发布时间倒序，近 30 天、最多 50 条）：

```
{BASE}/feed.xml
```

分类源：

```
{BASE}/feed/ai-intel.xml      # AI 商业情报，每天 08:30
{BASE}/feed/repo-radar.xml    # GitHub 早期爆款雷达，每天 08:30
{BASE}/feed/content-radar.xml # AI 内容雷达（只含“值得低成本试”），每天 12:00
{BASE}/feed/indie-sites.xml   # 新爆款 AI 独立站，每天 0–5 个首次发现
{BASE}/feed/daily.xml         # 一天一条，各系列条数汇总
```

展示页（给人看的订阅入口）：{BASE}/feed.html

## JSON API（静态文件，不是动态服务器）

```
{BASE}/api/v1/latest.json            # 近 7 天全部条目，最多 100 条，按时间倒序
{BASE}/api/v1/hot.json               # 当天评分最高的前 10 条
{BASE}/api/v1/daily/2026-11-19.json  # 按天拆分，一天一个文件
{BASE}/api/v1/search.json            # 全量索引：id / title / summary / category / date
{BASE}/api/v1/ai-news.json           # 最新一期 AI 创业信息流：标题 + 原文链接
{BASE}/api/v1/index.json             # 端点目录 + 各系列最新数据文件链接
```

**诚实说明：这是静态文件托管，没有服务器。** `?limit=` / `?window=` / `?q=` 不是服务器端参数——
客户端拿到 `latest.json` 或 `search.json` 后自己按 `limit` / `window` / `category` 过滤。
机器可读的接口定义见 `{BASE}/openapi.json`（OpenAPI 3.1）。

## 刷新频率

建议 30 分钟刷一次，不要每分钟刷。GitHub Pages 的静态文件没有精细的
Cache-Control / ETag 控制。每天的新内容在北京时间 08:30（情报、雷达）、
09:51（信息流）、12:00（内容雷达）、21:10（跟踪器）前后陆续上线。

## 字段含义（统一条目模型）

| 字段 | 含义 |
|---|---|
| id | 稳定编号，格式 `{{source}}-{{YYYYMMDD}}-{{序号}}`，重复生成不变 |
| title | 标题；ai-intel 是 `公司：事件` 前 60 字；雷达是 `[GitHub雷达 89分] 仓库 — 一句话做什么`；内容雷达是 `[内容雷达 87分] 格式名 — 值得低成本试` |
| summary | 摘要，不超过 300 字；ai-intel 用 commercial_value 原文，雷达用 `星数★ · 增速依据 · 上手：做法` |
| link | 链回我们自己的存档页（`archive/...-YYYY-MM-DD.html`），不要直接当原文链接用 |
| source_url | 外部原文链接，有就填，没有为空 |
| category | AI商业情报 / GitHub早期爆款 / AI内容格式 / AI独立站 |
| source | ai-intel / repo-radar / content-radar / indie |
| score | 评分（有就填）；ai-intel TOP7 本身没有评分，填 null，不要自己编一个 |
| verdict | 结论，如“值得低成本试”；没有就不填 |
| published_at | 发布时间，`YYYY-MM-DDTHH:MM:SS+08:00`，取各 JSON 的 fetched_at_cst / generated_at_cst，没有就用当天档期时间（08:30 / 12:00），不是生成脚本的运行时间 |
| date | 所属日期 `YYYY-MM-DD` |

## 示例

```bash
# 取最近 7 天的全部条目
curl -s {BASE}/api/v1/latest.json | head -c 1000

# 取当天评分最高的 10 条
curl -s {BASE}/api/v1/hot.json

# 按天取
curl -s {BASE}/api/v1/daily/2026-11-19.json

# 全量索引用客户端自己搜（示例：找标题含“Agent”的条目）
curl -s {BASE}/api/v1/search.json | python3 -c "import json,sys; d=json.load(sys.stdin); print([x for x in d['items'] if 'Agent' in x['title']][:3])"

# 订阅主源
curl -s {BASE}/feed.xml | head -20
```

## 原始数据（只链，不复制内容）

热榜与跟踪器是原始榜单，不是分析，不进主源；需要原始数据直接取：

- 每日热榜：`{BASE}/data/YYYY-MM-DD.json`
- B站跟踪器：`{BASE}/data/tracker-YYYY-MM-DD.json`
- 各系列最新数据文件链接见 `{BASE}/api/v1/index.json` 的 `series` 一节。

## 注意

- 没有的数据写“未核实”，创始人自述的会写明“创始人自述，未独立核实”；不要把这里的“未核实”当成“已核实”用。
- ai-news 只给标题 + 原文链接，不写我们没核实的摘要；不要把标题包装成我们自己的分析。
- 内容来自 CCD-AIGC/daily-hotlist 的原创筛选；如需转载或商用，请先联系仓库维护者。
"""


def openapi_doc():
    desc = ("CCD-AIGC daily-hotlist 的静态 RSS + JSON API：每天的原创筛选——"
            "AI商业情报 TOP7、GitHub 24h 快涨仓库、海外先火的 AI 视频格式、"
            "新爆款 AI 独立站。\n\n"
            "诚实说明：这是静态文件托管在 GitHub Pages 上，没有服务器。"
            "?limit= / ?window= / ?q= 不是服务器端参数，客户端拿到 "
            "latest.json / search.json 后自己按 limit / window / category "
            "过滤。不要假装是动态 API。\n\n"
            "缓存建议：30 分钟刷一次，不要每分钟刷。GitHub Pages 的静态"
            "文件没有精细的 Cache-Control / ETag 控制。")
    paths = {}
    for p, d in [
        ("/feed.xml", "主源 RSS：三个主力系列混合，近 30 天、最多 50 条"),
        ("/feed/ai-intel.xml", "分类源 RSS：AI 商业情报"),
        ("/feed/repo-radar.xml", "分类源 RSS：GitHub 早期爆款雷达"),
        ("/feed/content-radar.xml", "分类源 RSS：AI 内容雷达（值得低成本试）"),
        ("/feed/indie-sites.xml", "分类源 RSS：新爆款 AI 独立站"),
        ("/feed/daily.xml", "日报 RSS：一天一条，各系列条数汇总"),
        ("/api/v1/latest.json", "近 7 天全部条目，最多 100 条"),
        ("/api/v1/hot.json", "当天评分最高的前 10 条"),
        ("/api/v1/daily/{date}.json", "按天拆分，一天一个文件，{date} 如 2026-11-19"),
        ("/api/v1/search.json", "全量索引：id / title / summary / category / date"),
        ("/api/v1/ai-news.json", "最新一期 AI 创业信息流：标题 + 原文链接"),
        ("/api/v1/index.json", "端点目录 + 各系列最新数据文件链接"),
        ("/agent.md", "给 agent 的订阅与调用说明"),
        ("/feed.html", "给人看的订阅展示页"),
    ]:
        paths[p] = {"get": {
            "summary": d,
            "responses": {"200": {"description": "OK，静态文件内容"}},
        }}
    return {
        "openapi": "3.1.0",
        "info": {"title": "CCD-AIGC daily-hotlist RSS + JSON API",
                 "version": "1.0.0", "description": desc},
        "servers": [{"url": BASE}],
        "paths": paths,
    }


# ---------------------------------------------------------------- main

def latest_file(pattern):
    files = sorted((ROOT / "data").glob(pattern))
    return files[-1] if files else None


def main():
    items = build_items()
    if not items:
        raise SystemExit("no items built from data/*.json")
    ref_date = max(it["date"] for it in items)
    ref_dt = datetime.fromisoformat(ref_date + "T00:00:00+08:00")
    win30 = ref_dt - timedelta(days=29)
    win7 = ref_dt - timedelta(days=6)
    by_date = {}
    for it in items:
        by_date.setdefault(it["date"], []).append(it)
    per_day = {d: v for d, v in by_date.items()}

    def in30(it):
        return it["_dt"] >= win30

    def in7(it):
        return it["_dt"] >= win7

    main_items = [it for it in items if in30(it)][:50]
    write(ROOT / "feed.xml", rss_doc(
        "CCD-AIGC AI Radar — 每日AI商业情报 / GitHub早期爆款 / AI内容格式",
        "每天的原创筛选，不是转载聚合：AI商业情报TOP7、GitHub 24h快涨仓库、"
        "海外先火国内未火的AI视频格式、新爆款AI独立站。",
        "feed.xml", main_items))

    feeds = {
        "ai-intel": ("feed/ai-intel.xml",
                     "CCD-AIGC AI Radar — AI商业情报",
                     "每天 08:30 的 AI 商业情报 TOP7 与机会。"),
        "repo-radar": ("feed/repo-radar.xml",
                       "CCD-AIGC AI Radar — GitHub早期爆款",
                       "每天 08:30 的 GitHub 早期爆款雷达 TOP10。"),
        "content-radar": ("feed/content-radar.xml",
                          "CCD-AIGC AI Radar — AI内容格式",
                          "每天 12:00 值得低成本试的 AI 视频格式。"),
        "indie": ("feed/indie-sites.xml",
                  "CCD-AIGC AI Radar — 新爆款AI独立站",
                  "每天 0–5 个首次发现的新爆款 AI 独立站。"),
    }
    for src, (path, title, desc) in feeds.items():
        sub = [it for it in items if it["source"] == src and in30(it)][:50]
        write(ROOT / path, rss_doc(title, desc, path, sub))

    # feed/daily.xml: one item per day
    daily_items = []
    for d in sorted(per_day.keys(), reverse=True):
        day = per_day[d]
        counts = {s: sum(1 for it in day if it["source"] == s)
                  for s in ("ai-intel", "repo-radar", "content-radar",
                            "indie")}
        title = (f"{d}：AI商业情报 {counts['ai-intel']} 条 · "
                 f"GitHub雷达 {counts['repo-radar']} 条 · "
                 f"内容雷达 {counts['content-radar']} 条 · "
                 f"新独立站 {counts['indie']} 个")
        latest_dt = max(it["_dt"] for it in day)
        daily_items.append({
            "id": f"daily-{yyyymmdd(d)}",
            "title": title,
            "summary": (f"{d} 各系列条数：AI商业情报 "
                        f"{counts['ai-intel']} 条、GitHub雷达 "
                        f"{counts['repo-radar']} 条、内容雷达 "
                        f"{counts['content-radar']} 条、新独立站 "
                        f"{counts['indie']} 个。"
                        f"当日存档：情报 archive/ai-intel-{d}.html，"
                        f"雷达 archive/repo-radar-{d}.html，"
                        f"内容 archive/content-radar-{d}.html。"),
            "link": f"{BASE}/archive/{d}.html",
            "source_url": "", "category": "日报汇总",
            "source": "daily", "score": None, "verdict": None,
            "published_at": iso(latest_dt), "date": d,
            "_dt": latest_dt, "_pri": 9, "_seq": 0,
        })
    write(ROOT / "feed" / "daily.xml", rss_doc(
        "CCD-AIGC AI Radar — 日报",
        "一天一条：当天各系列的条数汇总。",
        "feed/daily.xml", daily_items))

    now = datetime.now(CST)
    latest7 = [pub(it) for it in items if in7(it)][:100]
    dump_json(ROOT / "api" / "v1" / "latest.json", {
        "generated_at": iso(now), "window_days": 7,
        "count": len(latest7), "items": latest7})

    today = [it for it in items if it["date"] == ref_date
             and it["score"] is not None]
    today.sort(key=lambda x: (-x["score"], -x["_dt"].timestamp()))
    dump_json(ROOT / "api" / "v1" / "hot.json", {
        "date": ref_date, "count": min(10, len(today)),
        "items": [pub(it) for it in today[:10]]})

    for d, day in sorted(per_day.items()):
        dump_json(ROOT / "api" / "v1" / "daily" / f"{d}.json", {
            "date": d, "count": len(day),
            "items": [pub(it) for it in day]})

    dump_json(ROOT / "api" / "v1" / "search.json", {
        "generated_at": iso(now), "count": len(items),
        "items": [{"id": it["id"], "title": it["title"],
                   "summary": it["summary"], "category": it["category"],
                   "date": it["date"]} for it in items]})

    # ai-news: latest data/ai-YYYY-MM-DD.json, titles + links only
    ai_news = latest_file("ai-[0-9]*.json")
    if ai_news is not None:
        d = load_json(ai_news)
        m = re.fullmatch(r"ai-(\d{4}-\d{2}-\d{2})\.json", ai_news.name)
        nd = m.group(1) if m else d.get("date", "")
        dump_json(ROOT / "api" / "v1" / "ai-news.json", {
            "date": nd, "fetched_at_cst": d.get("fetched_at_cst", ""),
            "source": "ai-news",
            "note": "标题 + 原文链接，不写我们没核实的摘要。",
            "count": len(d.get("items", [])),
            "items": [{"title": i.get("title", ""),
                       "url": i.get("url", ""),
                       "category": i.get("category", ""),
                       "source": i.get("source", "")}
                      for i in d.get("items", [])]})

    # index.json: endpoint directory + latest raw data links (links only)
    def latest_data(pattern, archive_fmt):
        f = latest_file(pattern)
        if f is None:
            return None
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        d = m.group(1) if m else ""
        return {"latest_data": f"data/{f.name}",
                "latest_archive": archive_fmt.format(d=d),
                "latest_date": d}

    series = {}
    for name, pat, fmt in [
        ("ai-intel", "ai-intel-[0-9]*.json", "archive/ai-intel-{d}.html"),
        ("repo-radar", "repo-radar-[0-9]*.json",
         "archive/repo-radar-{d}.html"),
        ("content-radar", "content-radar-[0-9]*.json",
         "archive/content-radar-{d}.html"),
        ("ai-news", "ai-[0-9]*.json", "archive/ai-{d}.html"),
        ("hotlist", "[0-9]*.json", "archive/{d}.html"),
        ("tracker", "tracker-[0-9]*.json", "tracker.html"),
    ]:
        v = latest_data(pat, fmt)
        if v:
            series[name] = v
    dump_json(ROOT / "api" / "v1" / "index.json", {
        "title": "CCD-AIGC daily-hotlist API 目录",
        "updated_at": iso(now), "base": BASE,
        "endpoints": {
            "feed": "feed.xml",
            "feed_ai_intel": "feed/ai-intel.xml",
            "feed_repo_radar": "feed/repo-radar.xml",
            "feed_content_radar": "feed/content-radar.xml",
            "feed_indie_sites": "feed/indie-sites.xml",
            "feed_daily": "feed/daily.xml",
            "latest": "api/v1/latest.json",
            "hot": "api/v1/hot.json",
            "daily": "api/v1/daily/{YYYY-MM-DD}.json",
            "search": "api/v1/search.json",
            "ai_news": "api/v1/ai-news.json",
            "openapi": "openapi.json",
            "agent": "agent.md",
            "feed_html": "feed.html",
        },
        "series": series,
        "note": ("hotlist / tracker 是原始榜单，不进主源；"
                 "这里只给原始 data 文件链接，不复制其内容。"),
    })

    dump_json(ROOT / "openapi.json", openapi_doc())
    write(ROOT / "agent.md", agent_md())
    write(ROOT / "feed.html", feed_html(items, ref_date, per_day))

    print(f"items total: {len(items)}")
    print(f"feed.xml: {len(main_items)} items")
    for src, (path, _t, _d) in feeds.items():
        n = len([it for it in items if it["source"] == src and in30(it)])
        print(f"{path}: {min(n, 50)} items")
    print(f"feed/daily.xml: {len(daily_items)} days")
    print(f"api/v1/latest.json: {len(latest7)} items, "
          f"latest: {latest7[0]['published_at'] if latest7 else '-'}")
    print(f"api/v1/hot.json: {min(10, len(today))} items")
    print(f"api/v1/daily: {len(per_day)} files")
    print(f"api/v1/search.json: {len(items)} items")
    print(f"ref_date: {ref_date}")


if __name__ == "__main__":
    main()
