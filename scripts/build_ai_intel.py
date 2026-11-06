#!/usr/bin/env python3
"""从 data/ai-intel-YYYY-MM-DD.json 渲染 AI商业情报日报：最新一天为 ai-intel.html，往期只新增、不覆盖。"""
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
    for p in sorted(DATA.glob("ai-intel-????-??-??.json")):
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


def top7_table(day):
    rows = []
    for t in day.get("top7", []):
        badge = ' <span class="badge same">近 7 天</span>' if t.get("is_7day") else ""
        rows.append(
            f'<tr><td>{t["rank"]}</td><td><strong>{esc(t["company"])}</strong>{badge}<br>{esc(t["date"])}</td>'
            f'<td>{esc(t["event"])}</td><td>{esc(t["commercial_value"])}</td>'
            f'<td>{esc(t["key_data"])}</td><td>{esc(t["judgement"])}</td>'
            f'<td><a href="{esc(t["source_url"])}">原文</a></td></tr>'
        )
    return ("<section><h2>02 全球 AI 商业化 TOP 7<small>只收有收入 / 定价 / 付费客户 / 成本证据的新闻；近 7 天的重要财报与报告已标注实际日期</small></h2>"
            '<div style="overflow-x:auto"><table><tr><th>排名</th><th>公司 / 项目</th><th>重要事件</th><th>商业价值</th><th>关键数据</th><th>我的判断</th><th>原文链接</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def opp_cards(day):
    cards = []
    for o in day.get("opportunities", []):
        cards.append(
            f'<article class="card"><div class="card-top"><span class="tag">机会评分 {o["score"]} / 100</span>'
            f'<span class="badge same">证据：{esc(o["evidence_strength"])}</span></div>'
            f'<h3>{esc(o["title"])}</h3>'
            f'<p><strong>客户：</strong>{esc(o["customer"])}；<strong>真实需求：</strong>{esc(o["need"])}</p>'
            f'<p><strong>谁在付费：</strong>{esc(o["who_pays"])}</p>'
            f'<p><strong>竞争者：</strong>{esc(o["competitors"])}</p>'
            f'<p><strong>中国与海外：</strong>{esc(o["china_vs_overseas"])}</p>'
            f'<p><strong>大公司威胁：</strong>{esc(o["big_company_threat"])}</p>'
            f'<p><strong>1–5 人团队能否进入：</strong>{esc(o["solo_entry"])}</p>'
            f'<p><strong>首个 MVP：</strong>{esc(o["mvp"])}</p>'
            f'<p><strong>初期成本：</strong>{esc(o["cost"])}</p>'
            f'<p><strong>获客与定价：</strong>{esc(o["acquisition_pricing"])}</p></article>'
        )
    return ('<section><h2>03 新 AI 创业机会 TOP 3<small>评分 0–100 为主观判断依据，不是真实市场统计数字</small></h2>\n<div class="grid">\n'
            + "\n".join(cards) + '\n</div></section>')


def gh_table(day):
    rows = []
    for g in day.get("github_projects", []):
        rows.append(
            f'<tr><td><a href="{esc(g["repo_url"])}">{esc(g["project"])}</a></td>'
            f'<td>{esc(g["change"])}</td><td>{esc(g["solves"])}</td>'
            f'<td>{esc(g["commercial_scenario"])}</td><td>{esc(g["low_cost"])}</td>'
            f'<td>{esc(g["attention"])}</td></tr>'
        )
    note = esc(day.get("github_notes", ""))
    return ("<section><h2>04 GitHub / Gitee 值得关注的项目<small>按 7 天 / 30 天星增、新版本与提交活跃度判断，不只看总星数；Gitee 镜像同步不算原创发布</small></h2>"
            '<div style="overflow-x:auto"><table><tr><th>项目</th><th>实际新增变化</th><th>解决什么问题</th><th>商业应用场景</th><th>能否低成本使用</th><th>建议关注程度</th></tr>'
            + "\n".join(rows) + "</table></div>"
            + (f'<div class="note-box" style="margin-top:12px"><p>{note}</p></div>' if note else "") + "</section>")


def render(day, all_dates, prev_day=None):
    conclusions = "\n".join(f"<li>{esc(c)}</li>" for c in day.get("conclusions", []))
    mc = day.get("money_case", {})
    watch = "\n".join(f"<li>{esc(w)}</li>" for w in day.get("watchlist", []))
    sq = day.get("sources_quality", {})
    sq_notes = "\n".join(f"<li>{esc(n)}</li>" for n in sq.get("notes", []))
    archive_links = "\n".join(f'<a href="./archive/ai-intel-{d}.html">{d}</a>' for d in all_dates)
    diff = ('<section><h2>昨日对比<small>与昨日同一口径比较</small></h2><div class="note-box"><p>首版基线：没有昨日可比，不标注新上榜 / 星数涨跌。</p></div></section>'
            if prev_day is None else
            '<section><h2>昨日对比<small>与昨日同一口径比较</small></h2><div class="note-box"><p>'
            f'本期 TOP 7 共 {len(day.get("top7", []))} 条，机会 {len(day.get("opportunities", []))} 个，GitHub 项目 {len(day.get("github_projects", []))} 个；'
            f'观察清单变化：{esc(day.get("watchlist_change", ""))}</p></div></section>')
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI商业情报日报 · {esc(day['date'])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">{esc(day['date'])}</span>
<h1>AI商业情报日报</h1>
<p>每天 08:30 的商业判断版日报：只收有收入 / 定价 / 付费客户证据的新闻</p>
<p>窗口：{esc(day.get('window', ''))} · 抓取时间（北京时间）：{esc(day.get('fetched_at_cst', ''))}</p>
</div></header>
<div class="wrap">
{diff}
<section><h2>01 今日最重要的 3 个结论<small>说人话：变了什么、有什么新机会、竞争格局怎么变</small></h2>
<div class="note-box"><ol>
{conclusions}
</ol></div></section>
{top7_table(day)}
{opp_cards(day)}
{gh_table(day)}
<section><h2>05 每日一个 AI 赚钱案例：{esc(mc.get('company', ''))}<small>只写公开可核实的收入与价格，关键数据不公开就明说</small></h2>
<div class="card">
<p><strong>产品卖给谁：</strong>{esc(mc.get('sells_to', ''))}</p>
<p><strong>收费方式：</strong>{esc(mc.get('pricing', ''))}</p>
<p><strong>用户主要从哪里来：</strong>{esc(mc.get('where_users_from', ''))}</p>
<p><strong>公开营收信号：</strong>{esc(mc.get('public_revenue_signal', ''))}</p>
<p><strong>竞争优势：</strong>{esc(mc.get('advantage', ''))}</p>
<p><strong>可能成本结构：</strong>{esc(mc.get('cost_structure', ''))}</p>
<p><strong>可复制的经验：</strong>{esc(mc.get('replicable_lessons', ''))}</p>
<p><strong>不适合个人创业者的经验：</strong>{esc(mc.get('not_for_solo', ''))}</p>
</div></section>
<section><h2>06 对我最有价值的一个行动<small>具体、可执行、低成本</small></h2>
<div class="note-box"><p>{esc(day.get('action', ''))}</p></div></section>
<section><h2>07 观察清单<small>持续跟踪的公司 / 项目 / 机会，以及与上次判断的变化</small></h2>
<div class="card"><ul>
{watch}
</ul><p>{esc(day.get('watchlist_change', ''))}</p></div></section>
<section><h2>08 来源与数据质量<small>原文链接、发布日期与证据级别见正文各条</small></h2>
<div class="note-box"><ul>
<li>RSS 检查：{sq.get('rss_total', '未核实')} 个源，{sq.get('rss_available', '未核实')} 个可用，{sq.get('rss_dead', '未核实')} 个失效。{esc(sq.get('rss_dead_detail', ''))}</li>
<li>{esc(sq.get('rss_stale', ''))}</li>
<li>{esc(sq.get('agents_radar_mcp', ''))}</li>
{sq_notes}
</ul></div></section>
<section><h2>往期存档<small>只新增、不覆盖</small></h2>
<div class="chips">
{archive_links}
</div></section>
<footer><a href="./hub.html">汇总入口</a> · AI商业情报日报</footer>
</div>
</body>
</html>
"""


def main():
    days = load_days()
    if not days:
        raise SystemExit("data/ 下没有 ai-intel-YYYY-MM-DD.json")
    ARCHIVE.mkdir(exist_ok=True)
    dates = [d["date"] for d in days]
    for i, day in enumerate(days):
        prev_day = days[i - 1] if i > 0 else None
        (ARCHIVE / f"ai-intel-{day['date']}.html").write_text(render(day, dates, prev_day), encoding="utf-8")
    (ROOT / "ai-intel.html").write_text(render(days[-1], dates, days[-2] if len(days) > 1 else None), encoding="utf-8")
    print(f"rendered {len(days)} ai-intel day(s), latest={dates[-1]}")


if __name__ == "__main__":
    main()
