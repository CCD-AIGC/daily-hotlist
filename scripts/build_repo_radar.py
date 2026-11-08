#!/usr/bin/env python3
"""从 data/repo-radar-YYYY-MM-DD.json 渲染 GitHub 早期爆款雷达：最新一天为 repo-radar.html，往期只新增、不覆盖。"""
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
    for p in sorted(DATA.glob("repo-radar-????-??-??.json")):
        days.append(json.loads(p.read_text(encoding="utf-8")))
    days.sort(key=lambda d: d["date"])
    return days


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


def repo_link(repo):
    return f'<a href="https://github.com/{esc(repo)}">{esc(repo)}</a>'


def potential_cards(day):
    cards = []
    cats = {}
    for o in day.get("top_potential", []):
        c = o.get("category", "")
        if c:
            cats[c] = cats.get(c, 0) + 1
        cat_chip = f'<span class="tag">{esc(c)}</span>' if c else ""
        setup_line = f'<p>上手：{esc(o["setup"].removeprefix("上手："))}</p>' if o.get("setup") else ""
        cards.append(
            f'<article class="card"><div class="card-top"><span class="tag">潜力评分 {o["score"]} / 100</span>'
            f'<span class="badge same">★ {o["stars"]:,}</span></div>'
            f'<h3>{repo_link(o["repo"])}</h3>'
            + (f'<p>{cat_chip}</p>' if cat_chip else "")
            + f'<p>{esc(o["what"])}</p>'
            + setup_line
            + f'<p>{esc(o["basis"])}</p></article>'
        )
    cat_line = ("<p>分类速览：" + " · ".join(f"{esc(k)} {v} 个" for k, v in cats.items()) + "</p>") if cats else ""
    return ('<section><h2>01 尚未大规模爆红但最有潜力的 TOP 10<small>星数只代表关注度，不代表可用性与收入；评分是主观判断，依据写在每条理由里</small></h2>\n'
            + cat_line + '<div class="grid">\n'
            + "\n".join(cards) + '\n</div></section>')


def fastest_table(day):
    rows = []
    for i, f in enumerate(day.get("fastest_24h", []), 1):
        rows.append(
            f'<tr><td>{i}</td><td>{repo_link(f["repo"])}</td><td>★ {f["stars"]:,}</td>'
            f'<td>{esc(f["delta"])}</td><td>{esc(f["status"])}</td></tr>'
        )
    return ('<section><h2>02 最近 24 小时增长最快的 TOP 10<small>“基线核实”为自有连续快照增量（本版约 23 小时）；“Trending 今日”为 GitHub 官方 Trending 页 UTC 日增量，两者口径不同，不可直接比较</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>排名</th><th>项目</th><th>当前星数</th><th>增量</th><th>状态</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def new_table(day):
    rows = []
    for n in day.get("new_projects", []):
        rows.append(
            f'<tr><td>{repo_link(n["repo"])}</td><td>{esc(n["created"])}</td><td>★ {n["stars"]:,}</td>'
            f'<td>潜力 {n["score"]} / 100</td><td>{esc(n["what"])}</td></tr>'
        )
    return ('<section><h2>03 新创建的潜力项目 TOP 5<small>创建 7 天内；今日首次发现的项目无增速基线，待下一轮快照确认加速</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>项目</th><th>创建时间</th><th>当前星数</th><th>评分</th><th>它是做什么的</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def revived_table(day):
    rows = []
    for r in day.get("revived", []):
        rows.append(
            f'<tr><td>{repo_link(r["repo"])}</td><td>★ {r["stars"]:,}</td>'
            f'<td>{esc(r["age"])}</td><td>{esc(r["status"])}</td></tr>'
        )
    return ('<section><h2>04 沉寂后重新爆发的项目 TOP 5<small>年龄 &gt;90 天的老仓库，沉寂后恢复发布或重新上榜；REA 是典型：创建于 2026-04-14，沉寂近 2 个月后爆发</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>项目</th><th>当前星数</th><th>背景</th><th>最新表现</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def trending_table(day):
    rows = []
    for t in day.get("trending_major", []):
        rows.append(
            f'<tr><td>{repo_link(t["repo"])}</td><td>★ {t["stars"]:,}</td>'
            f'<td>{esc(t["today_gain"])}</td><td>{esc(t["what"])}</td></tr>'
        )
    return ('<section><h2>05 已经上 Trending、但值得研究的重大项目<small>Trending 本身已是爆发后榜单，只作对照，不当作早期发现</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>项目</th><th>当前星数</th><th>今日新增</th><th>它是做什么的</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def alerts_table(day):
    rows = []
    for a in day.get("yesterday_alerts", []):
        rows.append(
            f'<tr><td>{repo_link(a["repo"])}</td><td>★ {a["stars"]:,}</td><td>{esc(a["follow"])}</td></tr>'
        )
    return ('<section><h2>06 昨天预警项目的最新表现<small>2026 年 11 月 7 日 AL 轮已报警的项目；同一仓库不重复报警</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>项目</th><th>当前星数</th><th>最新表现</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def entrepreneur_cards(day):
    cards = []
    for o in day.get("entrepreneur_top3", []):
        cat_chip = f'<span class="tag">{esc(o["category"])}</span>' if o.get("category") else ""
        setup_line = f'<p>上手：{esc(o["setup"].removeprefix("上手："))}</p>' if o.get("setup") else ""
        cards.append(
            f'<article class="card"><div class="card-top"><span class="tag">机会评分 {o["score"]} / 100</span>'
            f'<span class="badge same">★ {o["stars"]:,}</span></div>'
            f'<h3>{repo_link(o["repo"])}</h3>'
            + (f'<p>{cat_chip}</p>' if cat_chip else "")
            + f'<p>{esc(o["what"])}</p>' + setup_line + f'<p>{esc(o["basis"])}</p></article>'
        )
    return ('<section><h2>07 今天值得试 / 值得研究的 AI 项目 TOP 3<small>评分是主观判断，不是真实市场统计数字；“上手”只写一句话部署门槛</small></h2>\n<div class="grid">\n'
            + "\n".join(cards) + '\n</div></section>')


def backtest_section(day):
    b = day.get("rea_backtest", {})
    rows = []
    for r in b.get("daily", []):
        rows.append(f'<tr><td>{esc(r["date"])}</td><td>+{r["gain"]:,}</td><td>{r["cum"]:,}</td></tr>')
    trig = b.get("first_trigger", {})
    return ('<section><h2>08 REA 历史回测<small>官方 Star History API 为准；用户原给的关键值 41/123/1,550/5,139/103,644 与官方还原 414/540/2,962/6,107/118,211 不符，不以原值校准阈值</small></h2>'
            f'<p>{esc(b.get("title", ""))}。{esc(b.get("source", ""))}</p>'
            '<div style="overflow-x:auto"><table><tr><th>日期（10 月）</th><th>当日新增</th><th>累计星数</th></tr>'
            + "\n".join(rows) + "</table></div>"
            f'<div class="note-box" style="margin-top:12px"><ul>'
            f'<li><strong>P2 首次：</strong>{esc(trig.get("p2", ""))}</li>'
            f'<li><strong>P1 首次：</strong>{esc(trig.get("p1", ""))}</li>'
            f'<li><strong>P0 首次：</strong>{esc(trig.get("p0", ""))}</li>'
            f'<li><strong>引爆点：</strong>{esc(b.get("trigger", ""))}</li>'
            f'<li><strong>误报教训：</strong>{esc(b.get("warning", ""))}</li>'
            f'<li><strong>结论：</strong>{esc(b.get("conclusion", ""))}</li>'
            '</ul></div></section>')


def render(day, all_dates):
    lv = day.get("levels_today", {})
    p2 = "".join(f"<li>{esc(x)}</li>" for x in lv.get("p2_triggered", []))
    m = day.get("method", {})
    th = "".join(f"<li>{esc(x)}</li>" for x in m.get("thresholds_v1_revised", []))
    ch = day.get("channel_health", {})
    ch_items = "".join(f"<li><strong>{esc(k)}：</strong>{esc(v)}</li>" for k, v in ch.items())
    archive_links = "\n".join(f'<a href="./archive/repo-radar-{d}.html">{d}</a>' for d in all_dates)
    body = f"""<section><h2>今日预警定级<small>快照窗口约 23.6 小时（2026-11-07 08:35 → 2026-11-08 08:10 CST）；P1 推送前须二次确认，本版新增 P1 2 个（bang-motion、niubigeo，均已发主聊天）</small></h2>
<div class="note-box"><ul>
<li><strong>P0 新增：</strong>{esc(lv.get("p0_new", ""))}</li>
<li><strong>P1 待二次确认：</strong>{esc(lv.get("p1_pending", ""))}</li>
<li><strong>P2 已触发（进重点观察池）：</strong><ul>{p2}</ul></li>
</ul></div></section>
"""
    body += potential_cards(day) + fastest_table(day) + new_table(day) + revived_table(day)
    body += trending_table(day) + alerts_table(day) + entrepreneur_cards(day) + backtest_section(day)
    body += f"""<section><h2>方法与阈值（v3 增长池 · v4 实用版）<small>按 REA 回测修正；小时级增速必须用自有连续快照计算；评分三维度：增速 40 / 能用度 30 / 新颖度 30</small></h2>
<div class="note-box"><ul>{th}</ul><p>{esc(m.get("note", ""))}</p></div></section>
<section><h2>渠道健康状态<small>第三方数字只作线索，不直接当结论；口径冲突已实证（同日 REA 增量 ossradar 称 +3.5k，ghtrends 称 +1,988）</small></h2>
<div class="note-box"><ul>{ch_items}</ul></div></section>
<section><h2>反刷星与质量检查<small>星数只代表关注度，不代表可用性与收入</small></h2>
<div class="note-box"><p>{esc(day.get("spam_note", ""))}</p><p>{esc(day.get("scores_note", ""))}</p><p>{esc(day.get("archive_note", ""))}</p></div></section>
<section><h2>往期存档</h2><div class="chips">{archive_links}</div></section>
"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub早期爆款雷达｜{esc(day["date"])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">{esc(day["date"])} · 生成于 {esc(day.get("generated_at_cst", ""))} CST</span>
<h1>GitHub早期爆款雷达</h1>
<p>在仓库成为 Trending 爆款之前发现它：Trending + Search + Star History + 第三方雷达 + 传播信号，五条渠道并行；星数以 GitHub 连接器核实值为准。</p>
</div></header>
<div class="wrap">
{body}
<footer>数据来源：GitHub 官方页面与连接器（星数核实值）、官方 Star History API、RepoTrending / ossradar / ghtrends / whatstrending.ai（线索）、Hacker News（传播佐证） · 往期只新增、不覆盖</footer>
</div>
</body>
</html>
"""


def main():
    days = load_days()
    if not days:
        raise SystemExit("no repo-radar data found")
    all_dates = [d["date"] for d in days]
    latest = days[-1]
    html_text = render(latest, all_dates)
    (ROOT / "repo-radar.html").write_text(html_text, encoding="utf-8")
    (ARCHIVE / f"repo-radar-{latest['date']}.html").write_text(html_text, encoding="utf-8")
    print(f"rendered {latest['date']} -> repo-radar.html + archive/repo-radar-{latest['date']}.html")


if __name__ == "__main__":
    main()
