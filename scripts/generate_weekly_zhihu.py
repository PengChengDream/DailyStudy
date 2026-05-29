from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from common import iso_week_key, parse_date, project_path, read_generation_logs


def week_bounds(day: date) -> tuple[date, date]:
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)


def generate_weekly_draft(day: date, log_dir: Path, weekly_dir: Path) -> Path | None:
    start, end = week_bounds(day)
    rows = [
        row
        for row in read_generation_logs(log_dir)
        if row.get("date") and start.isoformat() <= row["date"] <= end.isoformat()
    ]
    if not rows:
        return None

    candidates = []
    for row in sorted(rows, key=lambda item: item.get("date", "")):
        for question in row.get("questions", []):
            if question.get("zhihu_candidate"):
                candidates.append((row, question))

    week = iso_week_key(day)
    path = weekly_dir / f"{week}-zhihu-draft.md"
    lines = [
        f"# AI 面试周精选（{week}）",
        "",
        f"范围：{start.isoformat()} 至 {end.isoformat()}",
        "",
        "这是一份手动发布知乎前的候选稿。请在发布前补充个人理解，删除不够精彩的问题，并确认所有外链可访问。",
        "",
        "## 本周精选问题",
        "",
    ]
    for index, (row, question) in enumerate(candidates[:8], start=1):
        source = question.get("source_url")
        source_line = f"\n- 来源：{source}" if source else ""
        lines.extend(
            [
                f"### {index}. {question.get('title')}",
                "",
                f"- 日期：{row.get('date')}",
                f"- 类型：{question.get('type')}",
                f"- 原文文件：`{row.get('daily_file')}`{source_line}",
                "",
            ]
        )
    if not candidates:
        lines.append("本周暂无标记为知乎候选的问题。")
        lines.append("")
    lines.extend(
        [
            "## 发布前检查",
            "",
            "- LeetCode 只保留题号、链接和自写摘要，不复制完整题面。",
            "- 外部短文只写摘要和读后问题，不全文转载。",
            "- 新技术题确认发布时间在发布日前 7 天内。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a weekly Zhihu candidate draft.")
    parser.add_argument("--date", default=None)
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--weekly-dir", default="weekly")
    parser.add_argument("--if-sunday", action="store_true", help="Skip unless the target date is Sunday.")
    args = parser.parse_args()

    target_day = parse_date(args.date)
    if args.if_sunday and target_day.weekday() != 6:
        print("Skipped weekly draft: target date is not Sunday.")
        return
    path = generate_weekly_draft(target_day, project_path(args.log_dir), project_path(args.weekly_dir))
    if path:
        print(f"Generated {path}")
    else:
        print("No logs found for this week.")


if __name__ == "__main__":
    main()
