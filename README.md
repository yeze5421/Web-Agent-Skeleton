# Web-Agent-Skeleton
一个基于 Python 的轻量级网页信息搜集工具。
输入一个问题后，程序会自动完成这几步：
1. 用浏览器搜索网页
2. 获取搜索结果标题、链接和摘要
3. 抓取网页正文
4. 按关键词做简单相关性评分
5. 导出 CSV 和 Markdown 报告

这个项目的重点不是大模型，而是先搭一个**不依赖大模型的 Web Agent 雏形**。
---
## 项目结构

```bash
plus_2/
├── main.py            # 程序入口，负责调度整体流程
├── searcher.py        # 浏览器搜索模块，支持翻页搜索
├── extractor.py       # 网页正文提取与简单打分
├── report_writer.py   # 导出 CSV 和 Markdown 报告
├── config.py          # 配置文件
└── README.md
