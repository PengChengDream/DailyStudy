from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

from common import code_line_count, load_json, month_key, parse_date, project_path
from generate_daily import build_daily


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_bank(month_dir: Path) -> None:
    iq = load_json(month_dir / "iq.json")
    ml_dl = load_json(month_dir / "ml_dl.json")
    hot = load_json(month_dir / "hot_tech.json")
    coding = load_json(month_dir / "coding.json")

    assert_true(len(iq) >= 7, "IQ bank needs at least 7 items.")
    assert_true(len(ml_dl) >= 7, "ML/DL bank needs at least 7 items.")
    assert_true(len(hot) >= 14, "Hot tech bank needs at least 14 items for a 7-day sample.")
    assert_true(len(coding.get("leetcode", [])) >= 4, "LeetCode bank needs at least 4 items.")
    assert_true(len(coding.get("ml", [])) >= 4, "ML coding bank needs at least 4 items.")
    for item in coding.get("ml", []):
        lines = code_line_count(item.get("reference_solution", ""))
        assert_true(lines <= 30, f"ML coding solution exceeds 30 non-empty lines: {item.get('id')} has {lines}.")
        url = item.get("source", {}).get("url", "")
        assert_true("deep-ml.com/problems/" in url, f"ML coding item must link to a Deep-ML problem page: {item.get('id')}.")
    for item in coding.get("leetcode", []):
        url = item.get("source", {}).get("url", "")
        assert_true("leetcode.com/problems/" in url, f"LeetCode item must link to a LeetCode problem page: {item.get('id')}.")


def validate_daily_sample(start_date: str, days: int, bank_root: Path, log_dir: Path) -> None:
    start = parse_date(start_date)
    previous_coding = None
    for offset in range(days):
        day = start + timedelta(days=offset)
        content, log_row = build_daily(
            target_day=day,
            bank_root=bank_root,
            daily_dir=Path("daily-preview"),
            log_dir=log_dir,
            strict_new_tech=False,
            offline_new_tech=True,
        )
        questions = log_row["questions"]
        assert_true([q["type"] for q in questions[:5]] == ["iq", "ml_dl", "hot_tech", "hot_tech", "new_tech"], "Daily question order is wrong.")
        assert_true(questions[5]["type"] in {"leetcode", "ml"}, "Coding slot must be leetcode or ml.")
        if previous_coding:
            assert_true(previous_coding != questions[5]["type"], "Coding questions must alternate daily.")
        previous_coding = questions[5]["type"]
        assert_true(content.startswith("# "), "Daily file must start with a hook heading.")
        assert_true(f"日期：{day.isoformat()}" in content, "Daily file must include the date after hook.")
        assert_true("<summary>参考答案</summary>" in content, "Daily file must include answers.")
        assert_true("趣味短文" not in content, "Daily file should not include fun essay.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the daily AI interview plan implementation.")
    parser.add_argument("--start-date", default=None, help="YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--bank-root", default="question_bank")
    parser.add_argument("--log-dir", default="logs")
    args = parser.parse_args()

    start = parse_date(args.start_date)
    bank_root = project_path(args.bank_root)
    month_dir = bank_root / month_key(start)
    validate_bank(month_dir)
    validate_daily_sample(args.start_date, args.days, bank_root, project_path(args.log_dir))
    print(f"Validation passed for {args.days} day sample starting {start.isoformat()}.")


if __name__ == "__main__":
    main()
