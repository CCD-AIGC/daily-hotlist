#!/usr/bin/env python3
"""从 data/*.json 渲染静态站：首页永远是最新一天，往期只新增、不删除。"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARCHIVE = ROOT / "archive"


def esc(s):
    return html.escape(str(s), quote=True)


def load_days():
    days = []
    for p in sorted(DATA.glob("????-??-??.json")):
        days.append(json.loads(p.read_text(encoding="utf-8")))
    days.sort(key=lambda d: d["date"])
    return days


def views_text(views):
    if views >= 10000:
        return f"{views / 10000:.1f}万播放"
    return f"{views:,} 播放"


def source_rows(day):
    rows = []
    for s in day.get("sources", []):
        status = {"ok": "正常", "failed": "当日未采用"}.get(s.get("status"), esc(s.get("status", "")))
        cls = "ok" if s.get("status") == "ok" else "bad"
        rows.append(
            f'<div class="source"><div class="source-head"><strong>{esc(s.get("platform", ""))} · {esc(s.get("name", ""))}</strong>'
            f'<span class="pill {cls}">{status}</span></div>'
            f'<p>更新：{esc(s.get("updated", ""))}</p><p>{esc(s.get("note", ""))}</p></div>'
        )
    return "\n".join(rows)


def diff_stats(prev_items, items):
    """按标题精确比对昨日同一来源：新进、升≥10位、掉出前50。"""
    if prev_items is None:
        return None
    prev = {x["title"]: x["rank"] for x in prev_items}
    cur = {x["title"] for x in items}
    new = [x for x in items if x["title"] not in prev]
    up = [
        {"title": x["title"], "old_rank": prev[x["title"]], "rank": x["rank"]}
        for x in items
        if x["title"] in prev and prev[x["title"]] - x["rank"] >= 10
    ]
    up.sort(key=lambda u: (u["old_rank"] - u["rank"]), reverse=True)
    dropped = [t for t in prev if t not in cur]
    return {"new": new, "up": up, "dropped_count": len(dropped), "prev": prev}


def list_rows(items, with_views, prev_items=None):
    rows = []
    prev = None
    if prev_items is not None:
        prev = {x["title"]: x["rank"] for x in prev_items}
    for it in items:
        rank = it["rank"]
        rank_cls = "r1" if rank == 1 else "r2" if rank == 2 else "r3" if rank == 3 else "rn"
        views = f'<span class="views">{views_text(it["views"])}</span>' if with_views and "views" in it else ""
        badge = ""
        if prev is not None:
            if it["title"] not in prev:
                badge = '<span class="badge new">新上榜</span>'
            else:
                old = prev[it["title"]]
                if old - rank >= 10:
                    badge = f'<span class="badge up">升{old - rank}位 · 昨日第{old}位</span>'
                elif old > rank:
                    badge = f'<span class="badge up">昨日第{old}位</span>'
                elif old < rank:
                    badge = f'<span class="badge down">昨日第{old}位</span>'
                else:
                    badge = f'<span class="badge same">昨日第{old}位</span>'
        rows.append(
            f'<div class="row"><span class="rank {rank_cls}">{rank}</span>'
            f'<span class="row-title">{esc(it["title"])}</span>{badge}{views}</div>'
        )
    return "\n".join(rows)


def diff_section(day, prev_day):
    if prev_day is None:
        return '<section id="diff"><h2>昨日对比<small>与昨日同一来源、同一口径比较</small></h2><div class="note-box"><p>首版基线：没有昨日可比，不标注新上榜 / 增速。</p></div></section>'
    b = diff_stats(prev_day.get("bilibili", []), day.get("bilibili", []))
    d = diff_stats(prev_day.get("douyin", []), day.get("douyin", []))
    def movers(up):
        if not up:
            return "无"
        return "；".join(f'{esc(u["title"])}（昨日第{u["old_rank"]}位 → 今日第{u["rank"]}位）' for u in up[:3])
    return f'''<section id="diff"><h2>昨日对比<small>与昨日同一来源、同一口径比较，按标题精确比对；标题加后缀的系列变体会计为新进，见说明</small></h2>
<div class="card"><p><strong>B站：</strong>新进 {len(b["new"])} 条，升 ≥10 位 {len(b["up"])} 条，掉出前 50 {b["dropped_count"]} 条。升幅最大的：{movers(b["up"])}。</p>
<p><strong>抖音：</strong>新进 {len(d["new"])} 条，升 ≥10 位 {len(d["up"])} 条，掉出前 50 {d["dropped_count"]} 条。升幅最大的：{movers(d["up"])}。</p>
<p class="note">每条榜单后都标了昨日排名：新上榜、升位、降位、持平一眼可见，不只罗列今日排名。</p></div></section>'''


def highlight_rows(day):
    rows = []
    for h in day.get("highlights", []):
        rows.append(
            f'<article class="hl"><div class="hl-top"><span class="tag">{esc(h.get("platform", ""))}</span>'
            f'<span class="hl-rank">第 {h.get("rank", "?")} 位</span></div>'
            f'<h3>{esc(h.get("title", ""))}</h3><p>{esc(h.get("note", ""))}</p></article>'
        )
    return "\n".join(rows)


CSS = """
:root{color-scheme:light;--bg:#f4f5f7;--card:#fff;--ink:#1c2333;--muted:#667085;--line:#e6e8ee;--blue:#2563eb;--pink:#fb7299}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.65}
.wrap{max-width:980px;margin:0 auto;padding:0 16px 56px}
.hero{background:linear-gradient(135deg,#1e3a8a,#2563eb 60%,#0ea5e9);color:#fff;padding:36px 0 28px}
.hero h1{margin:0 0 8px;font-size:30px;line-height:1.25;letter-spacing:.2px}
.hero p{margin:4px 0;color:#dbeafe;font-size:15px}
.date-pill{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);padding:4px 12px;border-radius:999px;font-size:14px;margin-bottom:14px}
.nav{position:sticky;top:0;z-index:5;background:rgba(244,245,247,.94);backdrop-filter:blur(8px);padding:12px 0;border-bottom:1px solid var(--line)}
.nav a{display:inline-block;margin:0 6px 6px 0;padding:7px 13px;border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--ink);text-decoration:none;font-size:14px}
.nav a:hover{border-color:var(--blue);color:var(--blue)}
h2{font-size:21px;margin:34px 0 12px}
h2 small{display:block;font-size:13px;color:var(--muted);font-weight:400;margin-top:4px}
.hl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.hl{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 1px 3px rgba(16,24,40,.06)}
.hl-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.tag{background:#eef2ff;color:#3730a3;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700}
.hl-rank{color:var(--muted);font-size:13px}
.hl h3{margin:0 0 6px;font-size:17px;line-height:1.5}
.hl p{margin:0;color:var(--muted);font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:8px 16px;box-shadow:0 1px 3px rgba(16,24,40,.06)}
.row{display:flex;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid #f0f1f4}
.row:last-child{border-bottom:0}
.rank{flex:0 0 30px;height:30px;line-height:30px;text-align:center;border-radius:50%;background:#eef0f4;color:#475467;font-weight:800;font-size:14px}
.rank.r1{background:#fef3c7;color:#92400e}.rank.r2{background:#e5e7eb;color:#374151}.rank.r3{background:#ffedd5;color:#9a3412}
.row-title{flex:1;font-size:16px;line-height:1.55}
.views{flex:0 0 auto;color:var(--muted);font-size:13px;background:#f2f4f7;padding:4px 9px;border-radius:999px;white-space:nowrap}
.badge{flex:0 0 auto;font-size:12px;padding:3px 8px;border-radius:999px;white-space:nowrap}
.badge.new{background:#dcfce7;color:#166534;font-weight:700}
.badge.up{background:#dbeafe;color:#1e40af}
.badge.down{background:#fee2e2;color:#991b1b}
.badge.same{background:#f2f4f7;color:#667085}
.source{border-top:1px solid #f0f1f4;padding:14px 0}
.source:first-child{border-top:0}
.source-head{display:flex;justify-content:space-between;gap:10px;align-items:center}
.source p{margin:5px 0 0;color:var(--muted);font-size:14px}
.pill{font-size:12px;padding:3px 9px;border-radius:999px;white-space:nowrap}
.pill.ok{background:#dcfce7;color:#166534}.pill.bad{background:#fee2e2;color:#991b1b}
.note-box{background:#fffbeb;border:1px solid #fde68a;border-radius:16px;padding:16px}
.note-box li{margin:6px 0}
.chips a{display:inline-block;margin:0 8px 8px 0;padding:8px 14px;border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--blue);text-decoration:none}
.search{width:100%;padding:13px 16px;font-size:16px;border:1px solid var(--line);border-radius:12px;background:#fff;margin-top:18px}
.search:focus{outline:2px solid var(--blue);outline-offset:1px}
.empty{display:none;padding:18px;text-align:center;color:var(--muted)}
footer{margin-top:36px;color:var(--muted);font-size:13px;text-align:center}
@media(max-width:560px){.hero h1{font-size:25px}.row-title{font-size:15px}.views{display:none}}
"""


def render(day, all_dates, prev_day=None):
    baseline = "首版基线：没有昨日可比，不标注新上榜 / 增速。" if day.get("is_baseline") else "与昨日同一来源、同一口径比较，每条后标昨日排名。"
    archive_links = "\n".join(
        f'<a href="./archive/{d}.html">{d}</a>' for d in all_dates
    )
    notes = "\n".join(f"<li>{esc(n)}</li>" for n in day.get("notes", []))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>每日热点榜单 · {esc(day['date'])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">{esc(day['date'])}</span>
<h1>每日热点榜单</h1>
<p>B站 + 抖音 · 每天早上更新 · 只看值得注意的变化</p>
<p>抓取时间（北京时间）：{esc(day.get('fetched_at_cst', ''))} · {baseline}</p>
</div></header>
<div class="wrap">
<nav class="nav"><a href="#diff">昨日对比</a><a href="#highlights">值得看</a><a href="#bilibili">B站热门</a><a href="#douyin">抖音热榜</a><a href="#sources">来源与口径</a><a href="#archive">往期存档</a></nav>
<input class="search" id="q" type="search" placeholder="搜榜单里的标题，比如：大肥鱼、DeepSeek…" aria-label="搜索榜单标题">
<p class="empty" id="empty">没有匹配的标题，换个关键词试试。</p>
{diff_section(day, prev_day)}
<section id="highlights"><h2>值得看<small>和 AI、知识、虚拟主播、鲸鱼娘、DeepSeek 直接相关的条目</small></h2>
<div class="hl-grid">
{highlight_rows(day)}
</div></section>
<section id="bilibili"><h2>B站热门前 50<small>含播放量，播放量已换算为“万”为单位</small></h2>
<div class="card">
{list_rows(day.get('bilibili', []), True, prev_day.get('bilibili') if prev_day else None)}
</div></section>
<section id="douyin"><h2>抖音热榜前 50<small>标题榜单，来源页未给热度值</small></h2>
<div class="card">
{list_rows(day.get('douyin', []), False, prev_day.get('douyin') if prev_day else None)}
</div></section>
<section id="sources"><h2>来源与口径</h2>
<div class="card">
{source_rows(day)}
</div></section>
<section><h2>说明与局限</h2>
<div class="note-box"><ul>
{notes}
<li>只记录榜单快照与差分，不声称全站统计；低粉爆款需要对同一视频连续采样，本版尚未上线该功能。</li>
</ul></div></section>
<section id="archive"><h2>往期存档<small>只新增、不覆盖</small></h2>
<div class="chips">
{archive_links}
</div></section>
<footer><a href="./">最新一天</a> · 每日热点榜单（B站 + 抖音）</footer>
</div>
<script>
var q=document.getElementById('q'),empty=document.getElementById('empty');
q.addEventListener('input',function(){{
  var v=q.value.trim().toLowerCase(),n=0;
  document.querySelectorAll('.row').forEach(function(r){{
    var show=!v||r.textContent.toLowerCase().indexOf(v)>-1;
    r.style.display=show?'':'none'; if(show)n++;
  }});
  empty.style.display=(v&&!n)?'block':'none';
}});
</script>
</body>
</html>
"""


def main():
    days = load_days()
    if not days:
        raise SystemExit("data/ 下没有 YYYY-MM-DD.json")
    ARCHIVE.mkdir(exist_ok=True)
    dates = [d["date"] for d in days]
    for i, day in enumerate(days):
        prev_day = days[i - 1] if i > 0 else None
        (ARCHIVE / f"{day['date']}.html").write_text(
            render(day, dates, prev_day), encoding="utf-8"
        )
    (ROOT / "index.html").write_text(render(days[-1], dates, days[-2] if len(days) > 1 else None), encoding="utf-8")
    print(f"rendered {len(days)} day(s), latest={dates[-1]}")


if __name__ == "__main__":
    main()
