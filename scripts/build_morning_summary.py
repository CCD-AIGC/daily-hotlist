#!/usr/bin/env python3
"""Render the daily morning summary archive.

Reads data/morning-summary-*.md (verbatim copies of the letters sent in
the main chat) and generates:
  morning-summary.html                  (latest edition, full text)
  archive/morning-summary-YYYY-MM-DD.html  (one page per edition)

Markdown subset supported: headings via fully-bold lines, bold, italic,
bare-URL lines, inline URLs, unordered lists, tables, horizontal rules,
paragraphs. Only Python standard library. No network access.

Usage: python3 scripts/build_morning_summary.py (no arguments).
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

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

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")


def esc(text):
    return html.escape(text)


def inline(text):
    """Escape, then apply bold / italic / autolinked URLs."""
    out = esc(text)
    out = BOLD_RE.sub(lambda m: "<strong>" + m.group(1) + "</strong>", out)
    out = ITALIC_RE.sub(lambda m: "<em>" + m.group(1) + "</em>", out)
    out = URL_RE.sub(lambda m: '<a href="' + m.group(0) + '">' + m.group(0) + "</a>", out)
    return out


def md_to_html(md_text):
    """Convert the letter's Markdown subset to HTML body fragments."""
    lines = md_text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            # drop the separator row (|---|---|)
            rows = [r for r in rows if not all(set(c) <= set("-: ") and c for c in r)]
            if not rows:
                continue
            head = rows[0]
            body_rows = rows[1:]
            parts = ['<div style="overflow-x:auto"><table><tr>']
            parts.append("".join("<th>" + inline(c) + "</th>" for c in head))
            parts.append("</tr>")
            for r in body_rows:
                parts.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>")
            parts.append("</table></div>")
            out.append("".join(parts))
            continue
        if stripped.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join("<li>" + inline(t) + "</li>" for t in items) + "</ul>")
            continue
        if re.fullmatch(r"\*\*.+\*\*", stripped):
            out.append("<h2>" + inline(stripped[2:-2]) + "</h2>")
            i += 1
            continue
        if re.fullmatch(r"https?://\S+", stripped):
            out.append('<p><a href="' + esc(stripped) + '">' + esc(stripped) + "</a></p>")
            i += 1
            continue
        # paragraph: gather consecutive non-blank, non-block lines
        buf = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if not nxt:
                break
            if nxt.startswith(("|", "- ")) or nxt in ("---", "***", "___"):
                break
            if re.fullmatch(r"\*\*.+\*\*", nxt):
                break
            if re.fullmatch(r"https?://\S+", nxt):
                break
            buf.append(nxt)
            i += 1
        out.append("<p>" + "<br>".join(inline(t) for t in buf) + "</p>")
    return "\n".join(out)


def load_editions():
    editions = []
    for path in sorted(DATA_DIR.glob("morning-summary-*.md")):
        m = re.fullmatch(r"morning-summary-(\d{4}-\d{2}-\d{2})\.md", path.name)
        if not m:
            continue
        date = m.group(1)
        text = path.read_text(encoding="utf-8")
        first = next((ln for ln in text.split("\n") if ln.strip()), "")
        title = first.strip().replace("**", "")
        editions.append({"date": date, "path": path, "text": text, "title": title})
    return editions


def archive_chips(editions, current_date, at_root):
    chips = []
    for e in editions:
        href = ("archive/" if at_root else "") + "morning-summary-" + e["date"] + ".html"
        label = e["date"] + ("（本期）" if e["date"] == current_date else "")
        chips.append('<a href="' + href + '">' + label + "</a>")
    return '<div class="chips">' + "".join(chips) + "</div>"


def render_page(edition, editions, at_root):
    rel_prefix = "" if at_root else "../"
    body = md_to_html("\n".join(edition["text"].split("\n")[1:]))
    chips = archive_chips(editions, edition["date"], at_root)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>每日早报汇总 · {esc(edition["date"])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="hero"><div class="wrap" style="padding-bottom:0">
<span class="date-pill">{esc(edition["date"])}</span>
<h1>{esc(edition["title"])}</h1>
<p><a href="{rel_prefix}hub.html" style="color:#dbeafe">← 回汇总入口</a></p>
</div></header>
<div class="wrap">
{body}
<section><h2>往期早报<small>每天一版，按天存档</small></h2>
{chips}
</section>
<footer>原文逐字存档于 data/morning-summary-{esc(edition["date"])}.md · <a href="{rel_prefix}hub.html">汇总入口</a></footer>
</div>
</body>
</html>
"""


def main():
    editions = load_editions()
    if not editions:
        raise SystemExit("no data/morning-summary-*.md found")
    (ROOT / "archive").mkdir(exist_ok=True)
    for e in editions:
        page = render_page(e, editions, at_root=False)
        out_path = ROOT / "archive" / ("morning-summary-" + e["date"] + ".html")
        out_path.write_text(page, encoding="utf-8")
        print("wrote", out_path)
    latest = editions[-1]
    latest_page = render_page(latest, editions, at_root=True)
    (ROOT / "morning-summary.html").write_text(latest_page, encoding="utf-8")
    print("wrote", ROOT / "morning-summary.html", "(latest:", latest["date"], ")")
    print("editions:", ", ".join(e["date"] for e in editions))


if __name__ == "__main__":
    main()
