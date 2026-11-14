#!/usr/bin/env python3
"""从 data/content-radar-YYYY-MM-DD.json 渲染 AI 内容雷达：最新一天为 content-radar.html，往期只新增、不覆盖。

逻辑：海外先火的 AI 视频格式 -> 国内状态（已传入 / 未传入 / 已传入且正热）
-> 滞后估计 -> 复刻配方（工具、效果、时长、成本、难度）-> 结论（值得低成本试 / 观望 / 已传入别追了）。
评分三维度：海外热度 40 / 复刻容易度 30 / 新颖度 30。
AIHOT（aihot.news）只作“新模型 / 新工具 -> 新格式浪潮”的早期信号源，不当作视频趋势源。
"""
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
    for p in sorted(DATA.glob("content-radar-????-??-??.json")):
        days.append(json.loads(p.read_text(encoding="utf-8")))
    days.sort(key=lambda d: d["date"])
    return days


CSS = """
:root{color-scheme:light;--bg:#f4f5f7;--card:#fff;--ink:#1c2333;--muted:#667085;--line:#e6e8ee;--blue:#2563eb;--green:#166534;--amber:#92400e;--red:#991b1b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.65}
.wrap{max-width:980px;margin:0 auto;padding:0 16px 56px}
.hero{background:linear-gradient(135deg,#3b0764,#7c3aed 60%,#db2777);color:#fff;padding:36px 0 28px}
.hero h1{margin:0 0 8px;font-size:30px;line-height:1.25}
.hero p{margin:4px 0;color:#ede9fe;font-size:15px}
.date-pill{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);padding:4px 12px;border-radius:999px;font-size:14px;margin-bottom:14px}
h2{font-size:21px;margin:34px 0 12px}h2 small{display:block;font-size:13px;color:var(--muted);font-weight:400;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 1px 3px rgba(16,24,40,.06)}
.card-top{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap}
.card h3{margin:0 0 6px;font-size:17px;line-height:1.5}
.card p{margin:6px 0;color:var(--muted);font-size:14px}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}
.tag.green{background:#dcfce7;color:var(--green)}
.tag.amber{background:#fef3c7;color:var(--amber)}
.tag.red{background:#fee2e2;color:var(--red)}
.tag.grey{background:#f2f4f7;color:#475467}
.note-box{background:#fffbeb;border:1px solid #fde68a;border-radius:16px;padding:16px}
.note-box li{margin:6px 0}
.chips a{display:inline-block;margin:0 8px 8px 0;padding:8px 14px;border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--blue);text-decoration:none}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden}
th,td{border-bottom:1px solid #f0f1f4;padding:10px 12px;text-align:left;font-size:14px;vertical-align:top}
th{background:#f8fafc;color:#475467;white-space:nowrap}
tr:last-child td{border-bottom:0}
footer{margin-top:36px;color:var(--muted);font-size:13px;text-align:center}
@media(max-width:560px){.hero h1{font-size:25px}}
"""

VERDICT_TAG = {
    "值得低成本试": "green",
    "观望": "amber",
    "已传入别追了": "red",
}

STATUS_TAG = {
    "未传入": "green",
    "已传入": "red",
    "已传入且正热": "amber",
}


def format_cards(day):
    cards = []
    for f in day.get("formats", []):
        v = f.get("verdict", "")
        vcls = VERDICT_TAG.get(v, "grey")
        s = f.get("domestic_status", "")
        scls = STATUS_TAG.get(s, "grey")
        r = f.get("recipe", {})
        sc = f.get("scores", {})
        cards.append(
            f'<article class="card"><div class="card-top">'
            f'<span class="tag">机会评分 {f["score"]} / 100</span>'
            f'<span class="tag {vcls}">{esc(v)}</span>'
            f'<span class="tag {scls}">国内：{esc(s)}</span></div>'
            f'<h3>{esc(f["name"])}</h3>'
            f'<p>海外：{esc(", ".join(f.get("platforms_overseas", [])))} · 国内：{esc(", ".join(f.get("platforms_domestic", [])))}</p>'
            f'<p><strong>海外热度</strong>（{sc.get("heat", "")}/40）：{esc(f.get("overseas_heat", ""))}</p>'
            f'<p><strong>国内状态</strong>：{esc(f.get("domestic_evidence", ""))}</p>'
            f'<p><strong>滞后估计</strong>：{esc(f.get("lag", ""))}</p>'
            f'<p><strong>复刻配方</strong>：工具 {esc(r.get("tool", ""))}；效果 {esc(r.get("effect", ""))}；时长 {esc(r.get("length", ""))}；成本 {esc(r.get("cost", ""))}；难度 {esc(r.get("difficulty", ""))}</p>'
            f'<p><strong>结论</strong>：{esc(f.get("verdict_note", ""))}</p></article>'
        )
    try_count = sum(1 for f in day.get("formats", []) if f.get("verdict") == "值得低成本试")
    return ('<section><h2>01 今天值得低成本试的格式<small>'
            f'共 {len(day.get("formats", []))} 个格式，其中 {try_count} 个值得低成本试；'
            '评分是主观判断，依据写在每条理由里，不是真实市场统计数字</small></h2>'
            '<div class="grid">\n' + "\n".join(cards) + '\n</div></section>')


def aihot_section(day):
    rows = []
    for s in day.get("aihot_signals", []):
        rows.append(
            f'<tr><td>{esc(s["date"])}</td><td>{esc(s["item"])}</td>'
            f'<td>{esc(s["signal"])}</td><td>{esc(s["source"])}</td></tr>'
        )
    return ('<section><h2>02 AIHOT 新模型 / 新工具信号<small>'
            'AIHOT 是 AI 资讯聚合，不是视频趋势源；这里只取“新模型、新工具发布”作为下一波格式的早期信号，'
            '数据来自 aihot.news RSS 与 /api/v1/agent（匿名只读，无需 Key）</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>日期</th><th>事件</th><th>对格式的意义</th><th>来源</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def domestic_section(day):
    d = day.get("domestic_today", {})
    return ('<section><h2>03 国内今日热榜里的 AI 视频<small>以当日 repo 热榜 data/&lt;date&gt;.json 快照为准</small></h2>'
            f'<div class="note-box"><ul><li><strong>Bilibili：</strong>{esc(d.get("bilibili_ai", ""))}</li>'
            f'<li><strong>抖音：</strong>{esc(d.get("douyin_ai", ""))}</li>'
            f'<li>{esc(d.get("note", ""))}</li>'
            f'<li>来源：{esc(d.get("source", ""))}</li></ul></div></section>')


def indie_seed_section(day):
    """One-off seed library table (2026-11-14 only): the 36 verified sites already in the
    registry, rendered as a compact table, not full cards. Later editions omit indie_seed."""
    seed = day.get("indie_seed")
    if not seed:
        return ""
    verdict_cls = {"跟进": "green", "观望": "amber", "别追了": "red"}
    rows = []
    for s in seed:
        v = s.get("verdict", "")
        vcls = verdict_cls.get(v, "grey")
        domain = s.get("domain", "")
        url = s.get("url") or ("https://" + domain if domain else "")
        link = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(domain)}</a>' if url else esc(domain)
        rows.append(
            f'<tr><td>{link}</td><td>{esc(s.get("name", ""))}</td>'
            f'<td>{esc(s.get("category", ""))}</td><td>{esc(s.get("industry", ""))}</td>'
            f'<td>{esc(s.get("what", ""))}</td><td><span class="tag {vcls}">{esc(v)}</span></td></tr>'
        )
    return ('<section><h2>05b 建库首批 36 站<small>'
            '2026-11-13 三份调研合并建库（中文 14 + B站 UP 新发现 9 + 英文 13；重叠 2 站只记一次）；'
            '只做一次分类汇总，之后每日只报新站，不重复入表</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>域名</th><th>站名</th><th>业务分类</th>'
            '<th>行业</th><th>做什么</th><th>结论</th></tr>'
            + "\n".join(rows) + "</table></div></section>")


def indie_sites_section(day):
    sites = day.get("indie_sites")
    if sites is None:
        return ('<section><h2>05 新出现爆款 AI 独立站<small>'
                '本节自 2026-11-14 起新增；往期无此章节</small></h2>'
                '<div class="note-box"><ul><li>本期未设此章节。</li></ul></div></section>')
    if not sites:
        return ('<section><h2>05 新出现爆款 AI 独立站<small>'
                '只列今日首次发现的站；无新发现不拿旧站凑数</small></h2>'
                '<div class="note-box"><ul><li><strong>今日无新发现。</strong></li></ul></div></section>')
    verdict_cls = {"跟进": "green", "观望": "amber", "别追了": "red"}
    rows = []
    cards = []
    for s in sites:
        v = s.get("verdict", "")
        vcls = verdict_cls.get(v, "grey")
        domain = s.get("domain", "")
        url = s.get("url") or ("https://" + domain if domain else "")
        link = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(domain)}</a>' if url else esc(domain)
        rows.append(
            f'<tr><td>{link}</td><td>{esc(s.get("category", ""))}</td>'
            f'<td>{esc(s.get("industry", ""))}</td><td>{esc(s.get("what", ""))}</td>'
            f'<td>{esc(s.get("viral_channel", ""))}</td>'
            f'<td><span class="tag {vcls}">{esc(v)}</span></td></tr>'
        )
        srcs = "".join(f"<li>{esc(x)}</li>" for x in s.get("sources", []))
        cards.append(
            f'<article class="card"><div class="card-top">'
            f'<span class="tag">{esc(s.get("category", ""))} · {esc(s.get("industry", ""))}</span>'
            f'<span class="tag {vcls}">{esc(v)}</span>'
            f'<span class="tag grey">{esc(s.get("verification", ""))}</span></div>'
            f'<h3>{esc(s.get("name", ""))} — {link}</h3>'
            f'<p><strong>做什么</strong>：{esc(s.get("what", ""))}</p>'
            f'<p><strong>作者</strong>：{esc(s.get("maker", ""))}</p>'
            f'<p><strong>爆火</strong>：{esc(s.get("viral_channel", ""))} · {esc(s.get("viral_date", ""))}；'
            f'证据：{esc(s.get("traction", ""))}</p>'
            f'<p><strong>商业模式</strong>：{esc(s.get("model", ""))}；定价：{esc(s.get("pricing", ""))}</p>'
            f'<p><strong>结论</strong>：{esc(s.get("verdict_note", ""))}</p>'
            f'<p><strong>来源</strong>：</p><ul>{srcs}</ul></article>'
        )
    return ('<section><h2>05 新出现爆款 AI 独立站<small>'
            f'今日首次发现 {len(sites)} 个；分类按“付费点是什么”定，行业按“为谁服务”定；'
            '创始人自述的数字已标注，未独立核实</small></h2>'
            '<div style="overflow-x:auto"><table><tr><th>域名</th><th>业务分类</th><th>行业</th>'
            '<th>做什么</th><th>爆火渠道</th><th>结论</th></tr>'
            + "\n".join(rows) + "</table></div>"
            '<div class="grid" style="margin-top:14px">\n' + "\n".join(cards) + '\n</div></section>')


def backtest_section(day):
    b = day.get("backtest", {})
    rows = []
    for r in b.get("timeline", []):
        rows.append(f'<tr><td>{esc(r["date"])}</td><td>{esc(r["event"])}</td></tr>')
    return ('<section><h2>04 武松打虎回测<small>海外先火、国内后火的完整时间线；“未见”与“未核实”如实标注，不编造播放量</small></h2>'
            f'<p>{esc(b.get("title", ""))}</p>'
            '<div style="overflow-x:auto"><table><tr><th>时间</th><th>事件</th></tr>'
            + "\n".join(rows) + "</table></div>"
            f'<div class="note-box" style="margin-top:12px"><ul>'
            f'<li><strong>结论：</strong>{esc(b.get("conclusion", ""))}</li>'
            f'<li><strong>口径说明：</strong>{esc(b.get("note", ""))}</li>'
            '</ul></div></section>')


def render(day, all_dates):
    m = day.get("method", {})
    verdicts = "".join(f"<li>{esc(x)}</li>" for x in m.get("verdicts", []))
    ch = day.get("channel_health", {})
    ch_items = "".join(f"<li><strong>{esc(k)}：</strong>{esc(v)}</li>" for k, v in ch.items())
    src_items = "".join(f"<li>{esc(x)}</li>" for x in day.get("sources", []))
    archive_links = "\n".join(f'<a href="./archive/content-radar-{d}.html">{d}</a>' for d in all_dates)
    body = format_cards(day) + aihot_section(day) + domestic_section(day) + backtest_section(day) + indie_sites_section(day) + indie_seed_section(day)
    body += f"""<section><h2>方法与口径<small>评分三维度：海外热度 40 / 复刻容易度 30 / 新颖度 30</small></h2>
<div class="note-box"><ul>
<li><strong>海外核查：</strong>{esc(m.get("overseas_check", ""))}</li>
<li><strong>国内核查：</strong>{esc(m.get("domestic_check", ""))}</li>
<li><strong>评分：</strong>{esc(m.get("scoring", ""))}</li>
<li><strong>结论分级：</strong><ul>{verdicts}</ul></li>
</ul></div></section>
<section><h2>渠道健康状态<small>来源打不开时如实记失败，不编造榜单、不报警</small></h2>
<div class="note-box"><ul>{ch_items}</ul></div></section>
<section><h2>来源清单</h2><div class="note-box"><ul>{src_items}</ul></div></section>
<section><h2>往期存档</h2><div class="chips">{archive_links}</div></section>
"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 内容雷达｜{esc(day["date"])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">{esc(day["date"])} · 生成于 {esc(day.get("generated_at_cst", ""))} CST</span>
<h1>AI 内容雷达</h1>
<p>{esc(day.get("tagline", ""))}</p>
</div></header>
<div class="wrap">
{body}
<footer>数据来源：AIHOT（RSS 与 /api/v1/agent，匿名只读）、repo 当日热榜快照、公开指南与检索结果 · 往期只新增、不覆盖 · 评分是主观判断，不是真实市场统计数字</footer>
</div>
</body>
</html>
"""


def main():
    days = load_days()
    if not days:
        raise SystemExit("no content-radar data found")
    all_dates = [d["date"] for d in days]
    latest = days[-1]
    html_text = render(latest, all_dates)
    (ROOT / "content-radar.html").write_text(html_text, encoding="utf-8")
    (ARCHIVE / f"content-radar-{latest['date']}.html").write_text(html_text, encoding="utf-8")
    print(f"rendered {latest['date']} -> content-radar.html + archive/content-radar-{latest['date']}.html")


if __name__ == "__main__":
    main()
