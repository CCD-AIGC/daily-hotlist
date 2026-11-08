#!/usr/bin/env python3
"""从 data/ai-intel-weekly-YYYY-MM-DD.json 渲染 AI 商业机会周报：最新一期为 ai-intel-weekly.html，往期只新增、不覆盖。样式与结构沿用 scripts/build_ai_intel.py。"""
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_ai_intel import CSS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARCHIVE = ROOT / "archive"


def esc(s):
    return html.escape(str(s), quote=True)


def load_weeks():
    weeks = []
    for p in sorted(DATA.glob("ai-intel-weekly-????-??-??.json")):
        weeks.append(json.loads(p.read_text(encoding="utf-8")))
    weeks.sort(key=lambda d: d["date"])
    return weeks


def opp_cards(opps, title, note):
    cards = []
    for o in opps:
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
            f'<p><strong>获客与定价：</strong>{esc(o["acquisition_pricing"])}</p>'
            + (f'<p><strong>评分依据：</strong>{esc(o["basis"])}</p>' if o.get("basis") else "")
            + '</article>'
        )
    return (f'<section><h2>{title}<small>{note}</small></h2>\n<div class="grid">\n'
            + "\n".join(cards) + '\n</div></section>')


def render(week, all_dates):
    conclusions = "\n".join(f"<li>{esc(c)}</li>" for c in week.get("conclusions", []))
    acc = "\n".join(
        f'<tr><td>{esc(t["theme"])}</td><td>{esc(t["evidence"])}</td><td>{esc(t["source"])}</td></tr>'
        for t in week.get("trends_accelerating", []))
    dec = "\n".join(
        f'<tr><td>{esc(t["theme"])}</td><td>{esc(t["evidence"])}</td><td>{esc(t["source"])}</td></tr>'
        for t in week.get("trends_decelerating", []))
    ct = week.get("cost_trend", {})
    ct_ev = "\n".join(f"<li>{esc(e)}</li>" for e in ct.get("evidence", []))
    comp = "\n".join(
        f'<tr><td><strong>{esc(c["company"])}</strong></td><td>{esc(c["action"])}</td>'
        f'<td>{esc(c["impact"])}</td><td><a href="{esc(c["source_url"])}">原文</a></td></tr>'
        for c in week.get("competition", []))
    gh = week.get("github_weekly", {})
    gh_hot = "\n".join(
        f'<tr><td><a href="{esc(g["repo_url"])}">{esc(g["project"])}</a></td><td>{esc(g["change_2d"])}</td>'
        f'<td>{esc(g["solves"])}</td><td>{esc(g["verdict"])}</td></tr>'
        for g in gh.get("hot", []))
    gh_mon = "\n".join(
        f'<tr><td><a href="{esc(g["repo_url"])}">{esc(g["project"])}</a></td><td>{esc(g["change_2d"])}</td></tr>'
        for g in gh.get("monitored", []))
    gh_rel = "\n".join(f"<li>{esc(r)}</li>" for r in gh.get("releases", []))
    rr = "\n".join(
        f'<tr><td><strong>{esc(r["title"])}</strong></td><td>{r["prev_score"]} → {r["new_score"]}</td>'
        f'<td>{esc(r["change"])}</td><td>{esc(r["reason"])}</td><td>{esc(r["evidence"])}</td></tr>'
        for r in week.get("re_ratings", []))
    av = week.get("avoid", {})
    watch = "\n".join(f"<li>{esc(w)}</li>" for w in week.get("watchlist", []))
    sq = week.get("sources_quality", {})
    sq_notes = "\n".join(f"<li>{esc(n)}</li>" for n in sq.get("notes", []))
    sq_gaps = "\n".join(f"<li>{esc(n)}</li>" for n in sq.get("gaps", []))
    rc = sq.get("rss_checks", {})
    rc_rows = "\n".join(
        f"<tr><td>{d}</td><td>{v.get('total')}</td><td>{v.get('available')}</td><td>{v.get('dead')}</td></tr>"
        for d, v in sorted(rc.items()))
    archive_links = "\n".join(
        f'<a href="./archive/ai-intel-weekly-{d}.html">{d}</a>' for d in all_dates)
    daily_links = "\n".join(
        f'<a href="./archive/ai-intel-{d}.html">{d}</a>' for d in week.get("daily_editions", []))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI商业机会周报 · {esc(week['date'])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">周报 · {esc(week['week_window'])}</span>
<h1>AI商业机会周报</h1>
<p>日报的周度汇总与再评级，不是把 7 天日报简单拼起来：趋势、竞争、机会评分每周重算一次</p>
<p>窗口：{esc(week['week_window'])} · 抓取时间（北京时间）：{esc(week.get('fetched_at_cst', ''))}</p>
</div></header>
<div class="wrap">
<section><h2>覆盖说明<small>本周报基于哪些日报，缺了哪几天</small></h2>
<div class="note-box"><p>{esc(week.get('coverage', ''))}</p>
<p>本期依据的日报：</p><div class="chips">
{daily_links}
</div></div></section>
<section><h2>01 本周最重要的 3 个结论<small>变了什么、有什么新机会、竞争格局怎么变</small></h2>
<div class="note-box"><ol>
{conclusions}
</ol></div></section>
<section><h2>02 本周趋势：加速与减速<small>只收有收入 / 付费客户 / 合同额 / 大规模部署新增证据的判断</small></h2>
<h3 style="font-size:17px;margin:18px 0 8px">加速</h3>
<div style="overflow-x:auto"><table><tr><th>商业模式</th><th>新增证据</th><th>来源</th></tr>
{acc}
</table></div>
<h3 style="font-size:17px;margin:18px 0 8px">减速或证伪</h3>
<div style="overflow-x:auto"><table><tr><th>商业模式</th><th>新增证据</th><th>来源</th></tr>
{dec}
</table></div></section>
<section><h2>03 工具与模型成本<small>是否下降、降幅与来源</small></h2>
<div class="note-box"><p><strong>{esc(ct.get('verdict', ''))}</strong></p><ul>
{ct_ev}
</ul></div></section>
<section><h2>04 竞争变化：头部厂商本周动作<small>收购、定价、产品动作如何改变竞争格局</small></h2>
<div style="overflow-x:auto"><table><tr><th>公司</th><th>本周动作</th><th>对格局的影响</th><th>原文</th></tr>
{comp}
</table></div></section>
<section><h2>05 开源项目：本周 Trending 与监控仓库<small>星增为 11-06→11-08 两日核实增量（系列启动 11-06，尚无完整 7 天基线）</small></h2>
<div style="overflow-x:auto"><table><tr><th>项目</th><th>星增</th><th>解决什么问题</th><th>判断</th></tr>
{gh_hot}
</table></div>
<h3 style="font-size:17px;margin:18px 0 8px">监控大仓库（11-06→11-08 两日）</h3>
<div style="overflow-x:auto"><table><tr><th>项目</th><th>星增</th></tr>
{gh_mon}
</table></div>
<div class="note-box" style="margin-top:12px"><p>{esc(gh.get('note', ''))}</p>
<p>本周新发布：</p><ul>
{gh_rel}
</ul></div></section>
<section><h2>06 机会再评级<small>本周日报看好的机会，新增证据后上调 / 下调 / 维持，评分 0–100 为主观判断，不是市场统计</small></h2>
<div style="overflow-x:auto"><table><tr><th>机会</th><th>评分变化</th><th>调整</th><th>理由</th><th>新增证据</th></tr>
{rr}
</table></div></section>
{opp_cards(week.get('new_opportunities', []), '07 本周新出现的机会', '单列评分并写明依据，评分不是市场统计')}
{opp_cards(week.get('top3', []), '08 本周最值得进入的 3 个机会', '其中 DeepSeek Harness 插件开发为 11-08 新出现，本周最高分 74；客户、真实需求、谁在付费、竞争者、大公司威胁、1–5 人团队能否进入、首个 MVP、初期成本估算')}
<section><h2>09 本周应放弃或暂缓的 1 个方向</h2>
<div class="card"><h3>{esc(av.get('title', ''))}</h3>
<p><strong>理由：</strong>{esc(av.get('reason', ''))}</p>
<p><strong>替代做法：</strong>{esc(av.get('alternative', ''))}</p></div></section>
<section><h2>10 本周最有价值的一个行动<small>具体、可执行、低成本</small></h2>
<div class="note-box"><p>{esc(week.get('action', ''))}</p></div></section>
<section><h2>11 观察清单<small>持续跟踪的公司 / 项目 / 机会</small></h2>
<div class="card"><ul>
{watch}
</ul></div></section>
<section><h2>12 来源与数据质量<small>来源覆盖与缺口；重要源连续 3 天无法访问时报告异常</small></h2>
<div class="note-box">
<p><strong>异常报告：</strong>{esc(sq.get('anomaly', ''))}</p>
<p>RSS 检查逐日：</p>
<div style="overflow-x:auto"><table><tr><th>日期</th><th>源总数</th><th>可用</th><th>失效</th></tr>
{rc_rows}
</table></div>
<ul>
{sq_notes}
</ul>
<p>缺口与未采信项：</p><ul>
{sq_gaps}
</ul></div></section>
<section><h2>往期周报<small>只新增、不覆盖</small></h2>
<div class="chips">
{archive_links}
</div></section>
<footer><a href="./hub.html">汇总入口</a> · <a href="./ai-intel.html">AI商业情报日报</a> · AI商业机会周报</footer>
</div>
</body>
</html>
"""


def main():
    weeks = load_weeks()
    if not weeks:
        raise SystemExit("data/ 下没有 ai-intel-weekly-YYYY-MM-DD.json")
    ARCHIVE.mkdir(exist_ok=True)
    dates = [w["date"] for w in weeks]
    for week in weeks:
        (ARCHIVE / f"ai-intel-weekly-{week['date']}.html").write_text(
            render(week, dates), encoding="utf-8")
    (ROOT / "ai-intel-weekly.html").write_text(render(weeks[-1], dates), encoding="utf-8")
    print(f"rendered {len(weeks)} ai-intel weekly edition(s), latest={dates[-1]}")


if __name__ == "__main__":
    main()
