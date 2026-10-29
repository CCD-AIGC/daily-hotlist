#!/usr/bin/env python3
"""从 data/ai-YYYY-MM-DD.json 渲染 AI 创业/商业化信息流页：最新一天为 ai-news.html，往期只新增、不覆盖。"""
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
    for p in sorted(DATA.glob("ai-????-??-??.json")):
        days.append(json.loads(p.read_text(encoding="utf-8")))
    days.sort(key=lambda d: d["date"])
    return days


def fmt_num(n):
    if n is None:
        return "未核实"
    return f"{n:,}"


def source_rows(day, prev_day):
    prev = {}
    if prev_day:
        prev = {s["repo"]: s for s in prev_day.get("sources", [])}
    rows = []
    for s in day.get("sources", []):
        old = prev.get(s["repo"])
        delta = ""
        if old is None:
            delta = '<span class="badge new">本日新列入</span>' if not day.get("is_baseline") else ""
        else:
            ds = (s.get("stars") or 0) - (old.get("stars") or 0)
            if ds > 0:
                delta = f'<span class="badge up">较昨日 +{ds} 星</span>'
            elif ds < 0:
                delta = f'<span class="badge down">较昨日 {ds} 星</span>'
            elif s.get("last_commit_date") != old.get("last_commit_date"):
                delta = f'<span class="badge up">有新提交：{esc(s.get("last_commit_date", ""))}</span>'
            else:
                delta = '<span class="badge same">无新提交</span>'
        status = "每日/周更核实" if s.get("status") == "ok" else "参考库，不计入每日新增" if s.get("status") == "reference" else esc(s.get("status", ""))
        rows.append(
            f'<article class="card"><div class="card-top"><span class="tag">{esc(s.get("role", ""))}</span>{delta}</div>'
            f'<h3><a href="{esc(s.get("repo_url", ""))}">{esc(s.get("repo", ""))}</a></h3>'
            f'<p>★ {fmt_num(s.get("stars"))}'
            + (f' · fork {fmt_num(s.get("forks"))}' if s.get("forks") is not None else "")
            + (f' · open issues {fmt_num(s.get("open_issues"))}' if s.get("open_issues") is not None else "")
            + f' · 状态：{status}</p>'
            f'<p>最近提交：{esc(s.get("last_commit_date", ""))} · {esc(s.get("last_commit_msg", ""))}</p>'
            f'<p>{esc(s.get("note", ""))}</p>'
            f'<p><a class="btn ghost" href="{esc(s.get("live_url", ""))}">打开在线站 / 仓库</a></p></article>'
        )
    return "\n".join(rows)


def item_rows(day, prev_day):
    prev_titles = set()
    if prev_day:
        prev_titles = {x["title"] for x in prev_day.get("items", [])}
    rows = []
    for i, it in enumerate(day.get("items", []), 1):
        badge = ""
        if prev_day is not None:
            badge = '<span class="badge new">新上榜</span>' if it["title"] not in prev_titles else '<span class="badge same">昨日也有</span>'
        rows.append(
            f'<div class="row"><span class="rank">{i}</span>'
            f'<span class="row-title"><a href="{esc(it["url"])}">{esc(it["title"])}</a></span>'
            f'<span class="tag">{esc(it.get("category", ""))}</span>{badge}'
            f'<span class="src">{esc(it.get("source", ""))}</span></div>'
        )
    return "\n".join(rows)


def diff_section(day, prev_day):
    if prev_day is None:
        return '<section><h2>昨日对比<small>与昨日同一口径比较</small></h2><div class="note-box"><p>首版基线：没有昨日可比，不标注新上榜 / 星数涨跌。</p></div></section>'
    new_items = [x for x in day.get("items", []) if x["title"] not in {y["title"] for y in prev_day.get("items", [])}]
    prev_src = {s["repo"]: s for s in prev_day.get("sources", [])}
    star_moves = []
    new_commits = []
    for s in day.get("sources", []):
        old = prev_src.get(s["repo"])
        if old is None:
            continue
        ds = (s.get("stars") or 0) - (old.get("stars") or 0)
        if ds:
            star_moves.append(f'{esc(s["repo"])}（{ds:+,} 星）')
        if s.get("last_commit_date") != old.get("last_commit_date"):
            new_commits.append(f'{esc(s["repo"])}（{esc(s.get("last_commit_date", ""))}）')
    return f'''<section><h2>昨日对比<small>精选标题按标题精确比对；源仓库按星数与最后提交日期比对</small></h2>
<div class="card"><p><strong>精选 20 条：</strong>新进 {len(new_items)} 条，昨日也有 {len(day.get("items", [])) - len(new_items)} 条。</p>
<p><strong>源仓库星数变化：</strong>{'；'.join(star_moves) if star_moves else '无变化'}。</p>
<p><strong>源仓库有新提交：</strong>{'；'.join(new_commits) if new_commits else '无'}。</p></div></section>'''


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
footer{margin-top:36px;color:var(--muted);font-size:13px;text-align:center}
@media(max-width:560px){.hero h1{font-size:25px}.row-title{font-size:15px}.src{display:none}}
"""


def render(day, all_dates, prev_day=None):
    b = day.get("brief", {})
    archive_links = "\n".join(f'<a href="./archive/ai-{d}.html">{d}</a>' for d in all_dates)
    notes = "\n".join(f"<li>{esc(n)}</li>" for n in day.get("notes", []))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 创业 / 商业化信息流 · {esc(day['date'])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">{esc(day['date'])}</span>
<h1>AI 创业 / 商业化信息流</h1>
<p>GitHub 高星信息源 + 每日精选 20 条 · 只看值得注意的变化</p>
<p>抓取时间（北京时间）：{esc(day.get('fetched_at_cst', ''))} · 源站 daily-brief 生成：{esc(b.get('generated_at_cst', ''))}</p>
</div></header>
<div class="wrap">
{diff_section(day, prev_day)}
<section><h2>今日精选 20 条<small>来源：{esc(b.get('repo', ''))} 的 daily-brief，只转录标题与原文链接，不复制全文；分类是本页按标题与来源的归类</small></h2>
<div class="card">
{item_rows(day, prev_day)}
</div>
<p><a class="btn" href="{esc(b.get('live_url', ''))}">打开源站完整雷达</a><a class="btn ghost" href="{esc(b.get('repo_url', ''))}" style="margin-left:8px">打开源仓库</a></p></section>
<section><h2>信息源仓库<small>星数与最后提交以当日 GitHub 连接器返回为准；次日与本日对比涨跌与新提交</small></h2>
<div class="grid">
{source_rows(day, prev_day)}
</div></section>
<section><h2>说明与局限</h2>
<div class="note-box"><ul>
{notes}
<li>只记录公开仓库的星数、提交与源站精选标题，不声称全站统计；商业化判断请点开原文核实，不要只看标题。</li>
</ul></div></section>
<section><h2>往期存档<small>只新增、不覆盖</small></h2>
<div class="chips">
{archive_links}
</div></section>
<footer><a href="./hub.html">汇总入口</a> · AI 创业 / 商业化信息流</footer>
</div>
</body>
</html>
"""


def main():
    days = load_days()
    if not days:
        raise SystemExit("data/ 下没有 ai-YYYY-MM-DD.json")
    ARCHIVE.mkdir(exist_ok=True)
    dates = [d["date"] for d in days]
    for i, day in enumerate(days):
        prev_day = days[i - 1] if i > 0 else None
        (ARCHIVE / f"ai-{day['date']}.html").write_text(render(day, dates, prev_day), encoding="utf-8")
    (ROOT / "ai-news.html").write_text(render(days[-1], dates, days[-2] if len(days) > 1 else None), encoding="utf-8")
    print(f"rendered {len(days)} ai day(s), latest={dates[-1]}")


if __name__ == "__main__":
    main()
