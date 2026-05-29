from __future__ import annotations

import argparse
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import PROJECT_ROOT, load_json, month_key, project_path, today_beijing, write_json


BANK_FILES = [
    "iq.json",
    "ml_dl.json",
    "hot_tech.json",
    "coding.json",
    "essays.json",
    "new_tech_manual.json",
]


def latest_existing_month(bank_root: Path, target_month: str) -> Path | None:
    candidates = [
        path
        for path in bank_root.iterdir()
        if path.is_dir() and path.name != "base" and path.name < target_month
    ]
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def copy_seed_files(seed_dir: Path, month_dir: Path, overwrite: bool) -> list[str]:
    copied: list[str] = []
    month_dir.mkdir(parents=True, exist_ok=True)
    for filename in BANK_FILES:
        source = seed_dir / filename
        target = month_dir / filename
        if not source.exists():
            continue
        if target.exists() and not overwrite:
            continue
        shutil.copyfile(source, target)
        copied.append(filename)
    return copied


def fetch_github_topic_candidates() -> list[dict[str, Any]]:
    query = "topic:machine-learning-interview-questions stars:>20"
    params = urllib.parse.urlencode(
        {"q": query, "sort": "stars", "order": "desc", "per_page": "10"}
    )
    request = urllib.request.Request(
        f"https://api.github.com/search/repositories?{params}",
        headers={"User-Agent": "daily-ai-interview-question-generator/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = load_bytes_json(response.read())
    repos = []
    for item in payload.get("items", []):
        repos.append(
            {
                "title": item.get("full_name"),
                "url": item.get("html_url"),
                "source_type": "github_topic",
                "stars": item.get("stargazers_count"),
                "description": item.get("description"),
            }
        )
    return repos


def load_bytes_json(payload: bytes) -> Any:
    import json

    return json.loads(payload.decode("utf-8"))


def render_source_report(month: str, sources: dict[str, Any], copied: list[str], errors: list[str]) -> str:
    lines = [
        f"# {month} 月度题库来源刷新",
        "",
        f"- 刷新时间：{sources['refreshed_at']}",
        f"- 复制/更新题库文件：{', '.join(copied) if copied else '无，已有文件保持不变'}",
        f"- 动态抓取错误：{'; '.join(errors) if errors else '无'}",
        "",
        "## 使用原则",
        "",
        "- 只保存标题、链接、发布时间、公司/方向、知识点和改写题目。",
        "- 不搬运平台原文、完整面经或 LeetCode 题面。",
        "- 每月人工浏览候选源，把高质量问题改写进对应 JSON 题库。",
        "",
        "## 候选来源",
        "",
    ]
    for group_name, items in sources.get("groups", {}).items():
        lines.append(f"### {group_name}")
        lines.append("")
        for item in items:
            title = item.get("title", "source")
            url = item.get("url", "")
            note = item.get("note") or item.get("description") or ""
            lines.append(f"- [{title}]({url})：{note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_monthly_bank(month: str, bank_root: Path, overwrite: bool, fetch_dynamic: bool) -> Path:
    base_dir = bank_root / "base"
    month_dir = bank_root / month
    seed_dir = latest_existing_month(bank_root, month) or base_dir
    if not seed_dir.exists():
        raise FileNotFoundError(f"Seed question bank not found: {seed_dir}")
    copied = copy_seed_files(seed_dir, month_dir, overwrite)

    registry = load_json(bank_root / "source_registry.json")
    groups = dict(registry.get("groups", {}))
    errors: list[str] = []
    if fetch_dynamic:
        try:
            groups.setdefault("GitHub 动态候选", []).extend(fetch_github_topic_candidates())
        except Exception as exc:
            errors.append(f"GitHub topic fetch failed: {exc}")

    sources = {
        "month": month,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "groups": groups,
        "notes": registry.get("notes", []),
        "errors": errors,
    }
    write_json(month_dir / "sources.json", sources)
    (month_dir / "source_refresh.md").write_text(
        render_source_report(month, sources, copied, errors),
        encoding="utf-8",
    )
    return month_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or refresh a monthly question bank folder.")
    parser.add_argument("--month", default=month_key(today_beijing()), help="YYYY-MM")
    parser.add_argument("--bank-root", default="question_bank")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--fetch-dynamic", action="store_true", help="Fetch dynamic source candidates from public APIs.")
    args = parser.parse_args()
    month_dir = build_monthly_bank(
        month=args.month,
        bank_root=project_path(args.bank_root),
        overwrite=args.overwrite,
        fetch_dynamic=args.fetch_dynamic,
    )
    print(f"Prepared {month_dir.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
