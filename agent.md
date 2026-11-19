# CCD-AIGC daily-hotlist — 给 agent 的订阅与调用说明

> 每天的原创筛选，不是转载聚合：AI 商业情报 TOP7、GitHub 24h 快涨仓库、海外先火国内未火的 AI 视频格式、新爆款 AI 独立站。
> 全部内容由 CCD-AIGC/daily-hotlist 每天定时生成，托管在 GitHub Pages 上。

## 订阅（RSS 2.0）

主源（三个主力系列混合，按发布时间倒序，近 30 天、最多 50 条）：

```
https://ccd-aigc.github.io/daily-hotlist/feed.xml
```

分类源：

```
https://ccd-aigc.github.io/daily-hotlist/feed/ai-intel.xml      # AI 商业情报，每天 08:30
https://ccd-aigc.github.io/daily-hotlist/feed/repo-radar.xml    # GitHub 早期爆款雷达，每天 08:30
https://ccd-aigc.github.io/daily-hotlist/feed/content-radar.xml # AI 内容雷达（只含“值得低成本试”），每天 12:00
https://ccd-aigc.github.io/daily-hotlist/feed/indie-sites.xml   # 新爆款 AI 独立站，每天 0–5 个首次发现
https://ccd-aigc.github.io/daily-hotlist/feed/daily.xml         # 一天一条，各系列条数汇总
```

展示页（给人看的订阅入口）：https://ccd-aigc.github.io/daily-hotlist/feed.html

## JSON API（静态文件，不是动态服务器）

```
https://ccd-aigc.github.io/daily-hotlist/api/v1/latest.json            # 近 7 天全部条目，最多 100 条，按时间倒序
https://ccd-aigc.github.io/daily-hotlist/api/v1/hot.json               # 当天评分最高的前 10 条
https://ccd-aigc.github.io/daily-hotlist/api/v1/daily/2026-11-19.json  # 按天拆分，一天一个文件
https://ccd-aigc.github.io/daily-hotlist/api/v1/search.json            # 全量索引：id / title / summary / category / date
https://ccd-aigc.github.io/daily-hotlist/api/v1/ai-news.json           # 最新一期 AI 创业信息流：标题 + 原文链接
https://ccd-aigc.github.io/daily-hotlist/api/v1/index.json             # 端点目录 + 各系列最新数据文件链接
```

**诚实说明：这是静态文件托管，没有服务器。** `?limit=` / `?window=` / `?q=` 不是服务器端参数——
客户端拿到 `latest.json` 或 `search.json` 后自己按 `limit` / `window` / `category` 过滤。
机器可读的接口定义见 `https://ccd-aigc.github.io/daily-hotlist/openapi.json`（OpenAPI 3.1）。

## 刷新频率

建议 30 分钟刷一次，不要每分钟刷。GitHub Pages 的静态文件没有精细的
Cache-Control / ETag 控制。每天的新内容在北京时间 08:30（情报、雷达）、
09:51（信息流）、12:00（内容雷达）、21:10（跟踪器）前后陆续上线。

## 字段含义（统一条目模型）

| 字段 | 含义 |
|---|---|
| id | 稳定编号，格式 `{source}-{YYYYMMDD}-{序号}`，重复生成不变 |
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
curl -s https://ccd-aigc.github.io/daily-hotlist/api/v1/latest.json | head -c 1000

# 取当天评分最高的 10 条
curl -s https://ccd-aigc.github.io/daily-hotlist/api/v1/hot.json

# 按天取
curl -s https://ccd-aigc.github.io/daily-hotlist/api/v1/daily/2026-11-19.json

# 全量索引用客户端自己搜（示例：找标题含“Agent”的条目）
curl -s https://ccd-aigc.github.io/daily-hotlist/api/v1/search.json | python3 -c "import json,sys; d=json.load(sys.stdin); print([x for x in d['items'] if 'Agent' in x['title']][:3])"

# 订阅主源
curl -s https://ccd-aigc.github.io/daily-hotlist/feed.xml | head -20
```

## 原始数据（只链，不复制内容）

热榜与跟踪器是原始榜单，不是分析，不进主源；需要原始数据直接取：

- 每日热榜：`https://ccd-aigc.github.io/daily-hotlist/data/YYYY-MM-DD.json`
- B站跟踪器：`https://ccd-aigc.github.io/daily-hotlist/data/tracker-YYYY-MM-DD.json`
- 各系列最新数据文件链接见 `https://ccd-aigc.github.io/daily-hotlist/api/v1/index.json` 的 `series` 一节。

## 注意

- 没有的数据写“未核实”，创始人自述的会写明“创始人自述，未独立核实”；不要把这里的“未核实”当成“已核实”用。
- ai-news 只给标题 + 原文链接，不写我们没核实的摘要；不要把标题包装成我们自己的分析。
- 内容来自 CCD-AIGC/daily-hotlist 的原创筛选；如需转载或商用，请先联系仓库维护者。
