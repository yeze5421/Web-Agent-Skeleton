from pathlib import Path
import csv
from datetime import datetime

import config


def ensure_output_dir() -> Path:
    out = Path(config.OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_csv(rows: list[dict], filename: str = "search_results.csv") -> Path:
    out_dir = ensure_output_dir()
    path = out_dir / filename

    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return path


def save_markdown(question: str, rows: list[dict], filename: str = "report.md") -> Path:
    out_dir = ensure_output_dir()
    path = out_dir / filename
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# 搜索报告\n",
        f"- 问题：{question}\n",
        f"- 时间：{now}\n",
        f"- 结果数：{len(rows)}\n\n",
        "## 结论速览\n",
    ]

    if not rows:
        lines.append("没有拿到结果。\n")
    else:
        for i, row in enumerate(rows, 1):
            lines.append(f"### {i}. {row.get('title', '无标题')}\n")
            lines.append(f"- 链接：{row.get('url', '')}\n")
            lines.append(f"- 匹配分：{row.get('score', 0)}\n")
            lines.append(f"- 搜索标题：{row.get('search_title', '')}\n")
            lines.append(f"- 搜索摘要：{row.get('snippet', '')}\n")
            lines.append(f"- 摘要：{row.get('short_summary', '')}\n\n")

        lines.append("## 原始正文摘录\n")
        for i, row in enumerate(rows, 1):
            lines.append(f"### {i}. {row.get('title', '无标题')}\n")
            lines.append(f"{row.get('text', '')[:2000]}\n\n")

    path.write_text("".join(lines), encoding="utf-8")
    return path