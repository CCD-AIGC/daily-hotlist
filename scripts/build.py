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


def source_rows(day):
    rows = []
    for s in day.get("sources", []):
        status = {"ok": "正常", "failed": "当日未采用"}.get(s.get("status"), esc(s.get("status", "")))
        rows.append(
            f"<li><strong>{esc(s.get('platform',''))} · {esc(s.get('name',''))}</strong>"
            f"（更新：{esc(s.get('updated',''))}，状态：{status}）"
            f"——{esc(s.get('note',''))}</li>"
        )
    return "\n".join(rows)


def list_rows(items, with_views):
    rows = []
    for it in items:
        views = f" · {it['views']:,} 播放" if with_views and "views" in it else ""
        rows.append(f"<li><span>{it['rank']}</span> {esc(it['title'])}{views}</li>")
    return "\n".join(rows)


def highlight_rows(day):
    rows = []
    for h in day.get("highlights", []):
        rows.append(
            f"<li><strong>{esc(h.get('title',''))}</strong>"
            f"（{esc(h.get('platform',''))} 第 {h.get('rank','?')} 位）"
            f"——{esc(h.get('note',''))}</li>"
        )
    return "\n".join(rows)


def render(day, all_dates):
    baseline = "首版基线：没有昨日可比，不标注新上榜 / 增速。" if day.get("is_baseline") else "与昨日同一来源、同一口径比较。"
    archive_links = "\n".join(
        f'<li><a href="./archive/{d}.html">{d}</a></li>' for d in all_dates
    )
    notes = "\n".join(f"<li>{esc(n)}</li>" for n in day.get("notes", []))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>每日热点榜单 · {esc(day['date'])}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;max-width:860px;margin:0 auto;padding:24px 16px 48px;line-height:1.7;color:#1a1a1a}}
h1{{font-size:26px}} h2{{font-size:20px;margin-top:32px;border-bottom:1px solid #ddd;padding-bottom:6px}}
li{{margin:6px 0}} li span{{color:#888;display:inline-block;width:2em}}
.meta,.note{{color:#555}} .box{{background:#f6f6f6;padding:12px 16px;border-radius:8px}}
a{{color:#0b5cad}}
</style>
</head>
<body>
<p><a href="./">最新一天</a> · 往期存档见页面底部</p>
<h1>每日热点榜单 · {esc(day['date'])}</h1>
<p class="meta">抓取时间（北京时间）：{esc(day.get('fetched_at_cst',''))} · {baseline}</p>
<div class="box">
<h2>值得看的</h2>
<ul>
{highlight_rows(day)}
</ul>
</div>
<h2>来源与口径</h2>
<ul>
{source_rows(day)}
</ul>
<h2>B站热门前 50</h2>
<ol>
{list_rows(day.get('bilibili', []), True)}
</ol>
<h2>抖音热榜前 50</h2>
<ol>
{list_rows(day.get('douyin', []), False)}
</ol>
<h2>说明与局限</h2>
<ul>
{notes}
</ul>
<p class="note">只记录榜单快照与差分，不声称全站统计；低粉爆款需要对同一视频连续采样，本版尚未上线该功能。</p>
<h2>往期存档（只新增、不覆盖）</h2>
<ul>
{archive_links}
</ul>
</body>
</html>
"""


def main():
    days = load_days()
    if not days:
        raise SystemExit("data/ 下没有 YYYY-MM-DD.json")
    ARCHIVE.mkdir(exist_ok=True)
    dates = [d["date"] for d in days]
    for day in days:
        (ARCHIVE / f"{day['date']}.html").write_text(
            render(day, dates), encoding="utf-8"
        )
    (ROOT / "index.html").write_text(render(days[-1], dates), encoding="utf-8")
    print(f"rendered {len(days)} day(s), latest={dates[-1]}")


if __name__ == "__main__":
    main()
