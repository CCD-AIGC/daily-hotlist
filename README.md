# 每日热点榜单（B站 + 抖音）

公开静态站：首页永远显示最新一天，往期按天存档，只新增、不覆盖。

## 内容口径

- B站：996Token 今日热榜前 50（标题与播放量）。
- 抖音：SnailDev/douyin-hot-hub 热榜前 50（标题；该来源不给热度值）。
- 首版（2026-10-28）为基线，没有昨日可比，不标注新上榜 / 增速。
- 差分规则：昨日不在前 50、今日新进；或排名上升 ≥10 位（同一来源、同一口径）；与 AI / 知识可视化 / 虚拟主播 / 鲸鱼娘 / DeepSeek 直接相关的单列“值得看”。
- 只记录榜单快照与样本内观察，不声称全站统计。低粉爆款雷达（对同一视频连续采样算增速）尚未上线，本站目前不发布低粉爆款结论。

## 每日协同方式

1. GitHub Actions 每天 08:36（北京时间）运行：检查来源是否可达、从 `data/*.json` 渲染页面、发布到 GitHub Pages。来源检查失败时不编造数据，保留已有页面。
2. Muse 每天核对榜单来源后，把核对过的新一天数据写成 `data/YYYY-MM-DD.json` 并提交；Actions 随后渲染与发布。Muse 同时巡检 Actions 运行状态，失败时在聊天里先发一版、不让更新断档。
3. 新增一天时只新增 `data/YYYY-MM-DD.json` 和对应的 `archive/YYYY-MM-DD.html`，不要修改已发布往期的数据文件；如需更正，在新一天的说明里写明更正。

## AI 创业 / 商业化信息流（2026-10-29 新增）

- 每日一页：`ai-news.html`（最新一天）+ `archive/ai-YYYY-MM-DD.html`（往期，只新增、不覆盖），数据在 `data/ai-YYYY-MM-DD.json`，渲染用 `scripts/build_ai.py`。
- 主力每日源（2026-10-29 上午 GitHub 连接器核实）：LearnPrompt/ai-news-radar（★1,796，24h 雷达，daily-brief 20 条）、zhuyansen/new-term-radar（★1,922，新词/新模型/新产品雷达）、alvinreal/awesome-opensource-ai（★4,948，每日更新的开源 AI 清单）。
- 周更与工具源：ruanyf/weekly（★107,143，每周五）、sansan0/TrendRadar（★63,266，自建舆情监控）、Thysrael/Horizon（★11,048，自建日报）。
- 参考库（不计入每日新增）：XiaomingX/ai-money-maker-handbook（★6,619，近 5 次提交仅为时间戳文件）、bleedline/aimoneyhunter（★18,320，最近实质提交 2025-10-20）。
- 口径与热榜一致：只转录源站精选标题与原文链接，不复制全文；次日与昨日对比新上榜标题、源仓库星数涨跌与新提交；来源失败或未证实每日更新时不冒充为每日源。

## 本地渲染

```bash
python3 scripts/build.py
python3 scripts/build_ai.py
```

## 来源健康状态

`data/source-health.json` 只记录来源是否可达，不包含榜单内容。
