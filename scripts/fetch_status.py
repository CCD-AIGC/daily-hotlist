#!/usr/bin/env python3
"""只做来源健康检查：记录每个来源当日是否能拉到，不解析、不编造榜单。

榜单内容仍由人工/Muse 在核对后写入 data/YYYY-MM-DD.json；
本脚本失败时构建继续使用已有数据，绝不把失败算成“没有热点”。
"""
import datetime
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = [
    ("996token", "https://www.996token.com/"),
    ("douyin-hot-hub", "https://github.com/SnailDev/douyin-hot-hub"),
]


def check(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "hotlist-site-health-check"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"name": name, "url": url, "status": "reachable", "http": resp.status}
    except Exception as exc:  # noqa: BLE001 - 只记录，不中断构建
        return {"name": name, "url": url, "status": "failed", "error": type(exc).__name__}


def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    payload = {
        "checked_at_cst": now.strftime("%Y-%m-%d %H:%M"),
        "checks": [check(name, url) for name, url in SOURCES],
        "note": "本文件只记录来源是否可达，不包含榜单内容；榜单解析与差分需核对后另行写入。",
    }
    (ROOT / "data" / "source-health.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
