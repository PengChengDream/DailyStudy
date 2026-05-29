from __future__ import annotations

import argparse
import hashlib
import html
import re
import textwrap
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from common import (
    PROJECT_ROOT,
    append_jsonl,
    iso_week_key,
    load_json,
    markdown_list,
    month_key,
    parse_date,
    project_path,
    select_item,
    select_items,
    today_beijing,
    used_question_ids,
)


CHINESE_AI_MEDIA_SOURCES = [
    {
        "name": "量子位",
        "urls": [
            "https://www.qbitai.com/",
            "https://www.qbitai.com/category/%E8%B5%84%E8%AE%AF",
        ],
    },
    {
        "name": "机器之心",
        "urls": [
            "https://www.jiqizhixin.com/articles",
            "https://www.almosthuman.cn/",
        ],
    },
]

TECH_TITLE_KEYWORDS = [
    "AI",
    "大模型",
    "模型",
    "智能体",
    "Agent",
    "多模态",
    "机器人",
    "开源",
    "推理",
    "训练",
    "算力",
    "芯片",
    "DeepSeek",
    "Qwen",
    "通义",
    "Claude",
    "GPT",
    "Gemini",
    "具身",
]


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_tags(value: str) -> str:
    return clean_space(re.sub(r"<[^>]+>", " ", html.unescape(value or "")))


def absolutize_url(base_url: str, value: str) -> str:
    value = html.unescape(value or "").strip()
    if not value or value.startswith("#") or value.startswith("javascript:"):
        return ""
    return urllib.parse.urljoin(base_url, value)


def parse_media_date(text: str, target_day: date) -> date | None:
    text = html.unescape(text)
    match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if re.search(r"\d+\s*(小时|分钟)前|今天|刚刚", text):
        return target_day
    if "昨天" in text:
        return target_day - timedelta(days=1)
    if "前天" in text:
        return target_day - timedelta(days=2)
    match = re.search(r"(\d+)\s*天前", text)
    if match:
        return target_day - timedelta(days=int(match.group(1)))
    return None


def fetch_url_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 daily-ai-interview-question-generator/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="ignore")


def extract_media_candidates(source_name: str, page_url: str, body: str, target_day: date) -> list[dict[str, Any]]:
    start_day = target_day - timedelta(days=7)
    candidates: list[dict[str, Any]] = []
    anchor_pattern = re.compile(r"<a\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*?>(.*?)</a>", re.I | re.S)
    for match in anchor_pattern.finditer(body):
        title = strip_tags(match.group(2))
        if len(title) < 8 or not any(keyword in title for keyword in TECH_TITLE_KEYWORDS):
            continue
        url = absolutize_url(page_url, match.group(1))
        if not url or urllib.parse.urlparse(url).netloc not in {
            "www.qbitai.com",
            "qbitai.com",
            "www.jiqizhixin.com",
            "jiqizhixin.com",
            "www.almosthuman.cn",
            "almosthuman.cn",
        }:
            continue
        window = body[max(0, match.start() - 600) : min(len(body), match.end() + 600)]
        published = parse_media_date(window, target_day)
        if not published or not (start_day <= published <= target_day):
            continue
        candidates.append(
            {
                "id": f"new-tech-{source_name}-{published.isoformat()}-{hashlib.sha1((title + url).encode('utf-8')).hexdigest()[:10]}",
                "type": "new_tech",
                "title": title,
                "question": f"阅读近 7 天{source_name}报道《{title}》：如果面试官让你把它转成一个技术判断题，你会追问哪三个问题？",
                "points": ["热点识别", "技术本质", "商业落地", "风险边界"],
                "hint": "不要停在新闻标题，先判断它是模型能力、产品形态、基础设施、数据、开源生态还是产业落地的变化。",
                "answer": (
                    "可以追问三层：第一，它背后的技术变量是什么，例如模型结构、推理成本、数据闭环或交互范式；"
                    "第二，它和已有方案相比真正变化在哪里，是指标提升、成本下降、体验变化还是生态位变化；"
                    "第三，它的落地约束是什么，包括数据、算力、合规、延迟、可靠性和用户接受度。"
                ),
                "source": {
                    "title": f"{source_name}：{title}",
                    "url": url,
                    "published_at": published.isoformat(),
                },
                "zhihu_candidate": True,
            }
        )
    candidates.sort(key=lambda item: (item["source"]["published_at"], item["title"]), reverse=True)
    return candidates


def fetch_chinese_media_new_tech(target_day: date) -> dict[str, Any] | None:
    errors: list[str] = []
    for source in CHINESE_AI_MEDIA_SOURCES:
        for page_url in source["urls"]:
            try:
                body = fetch_url_text(page_url)
            except Exception as exc:
                errors.append(f"{source['name']} {page_url}: {exc}")
                continue
            candidates = extract_media_candidates(source["name"], page_url, body, target_day)
            if candidates:
                return candidates[0]
    if errors:
        raise RuntimeError("; ".join(errors))
    return None


def load_manual_new_tech(month_dir: Path, target_day: date) -> dict[str, Any] | None:
    items = load_json(month_dir / "new_tech_manual.json", default=[])
    start_day = target_day - timedelta(days=7)
    valid = []
    for item in items:
        published_at = item.get("source", {}).get("published_at")
        if not published_at:
            continue
        published = date.fromisoformat(published_at)
        if start_day <= published <= target_day:
            valid.append(item)
    return valid[0] if valid else None


def get_new_tech_question(
    month_dir: Path,
    target_day: date,
    strict: bool,
    offline_placeholder: bool,
) -> dict[str, Any]:
    manual = load_manual_new_tech(month_dir, target_day)
    if manual:
        return manual
    if not offline_placeholder:
        try:
            item = fetch_chinese_media_new_tech(target_day)
            if item:
                return item
        except Exception as exc:
            if strict:
                raise RuntimeError(f"Failed to fetch a recent Chinese AI media item: {exc}") from exc
    if strict:
        raise RuntimeError("No recent new-tech item found within 7 days.")
    return {
        "id": f"new-tech-manual-review-{target_day.isoformat()}",
        "type": "new_tech",
        "title": "近 7 天新技术题待人工复核",
        "question": "今天的新技术题需要从量子位、机器之心等近 7 天公开报道中补充：它解决了什么新问题，为什么值得面试讨论？",
        "points": ["近 7 天来源", "问题价值", "方法抓手", "面试追问"],
        "hint": "正式发布前请替换为真实来源；GitHub Actions 默认使用严格模式，抓不到中文科技媒体新技术会失败而不是发布占位内容。",
        "answer": "本地离线预览占位。正式日更必须附真实链接、发布时间和简短背景。",
        "source": {
            "title": "manual review required",
            "url": "https://www.qbitai.com/category/%E8%B5%84%E8%AE%AF",
            "published_at": target_day.isoformat(),
        },
        "zhihu_candidate": False,
        "manual_review": True,
    }


def render_details(answer: str) -> str:
    return f"<details>\n<summary>参考答案</summary>\n\n{answer.strip()}\n\n</details>"


def render_standard_question(index: int, label: str, item: dict[str, Any], include_answers: bool) -> str:
    lines = [
        f"## {index}. {label}：{item['title']}",
        "",
        f"- 题目：{item['question']}",
        f"- 考察点：{markdown_list(item.get('points', []))}",
    ]
    if include_answers:
        lines.extend(["", render_details(item.get("answer", "暂无参考答案。"))])
    return "\n".join(lines).strip()


def render_coding_question(index: int, item: dict[str, Any], coding_type: str, include_answers: bool) -> str:
    if coding_type == "leetcode":
        source = item.get("source", {})
        tags = markdown_list(item.get("tags", []))
        answer = item.get("answer", "")
        lines = [
            f"## {index}. 编程题（LeetCode）：{item['title']}",
            "",
            f"- 题号：{item['leetcode_no']}",
            f"- 链接：[{item['title']}]({source.get('url', '')})",
            f"- 难度：{item.get('difficulty', 'unknown')}",
            f"- 标签：{tags}",
            f"- 自写摘要：{item['summary']}",
            f"- 提示：{item.get('hint', '')}",
        ]
        if include_answers:
            lines.extend(["", render_details(answer)])
        return "\n".join(lines).strip()
    examples = "\n".join(f"  - `{example}`" for example in item.get("examples", []))
    answer = item.get("reference_solution", "")
    source = item.get("source", {})
    lines = [
        f"## {index}. 编程题（ML）：{item['title']}",
        "",
        f"- 链接：[{source.get('title', 'Deep-ML')}]({source.get('url', 'https://www.deep-ml.com/')})",
        f"- 面试场景：{item.get('interview_context', '常见 ML 编程小题')}",
        f"- 函数签名：`{item['function_signature']}`",
        f"- 题目：{item['prompt']}",
        "- 样例：",
        examples,
        f"- 约束：{item.get('constraints', '控制在 30 行以内，优先使用清晰的 NumPy/Python 思路。')}",
    ]
    if include_answers:
        lines.extend(
            [
                "",
                "<details>",
                "<summary>参考答案</summary>",
                "",
                "```python",
                textwrap.dedent(answer).strip(),
                "```",
                "",
                "</details>",
            ]
        )
    return "\n".join(lines).strip()


def build_daily(
    target_day: date,
    bank_root: Path,
    daily_dir: Path,
    log_dir: Path,
    strict_new_tech: bool = False,
    offline_new_tech: bool = False,
) -> tuple[str, str, dict[str, Any]]:
    month = month_key(target_day)
    month_dir = bank_root / month
    if not month_dir.exists():
        raise FileNotFoundError(
            f"Monthly question bank is missing: {month_dir}. Run scripts/build_monthly_bank.py first."
        )

    used_ids = used_question_ids(log_dir)
    iq = load_json(month_dir / "iq.json")
    ml_dl = load_json(month_dir / "ml_dl.json")
    hot_tech = load_json(month_dir / "hot_tech.json")
    coding = load_json(month_dir / "coding.json")

    day_salt = target_day.isoformat()
    iq_item = select_item(iq, used_ids, f"{day_salt}:iq")
    classic_item = select_item(ml_dl, used_ids, f"{day_salt}:ml_dl")
    hot_items = select_items(hot_tech, used_ids, 2, f"{day_salt}:hot_tech")
    new_tech_item = get_new_tech_question(month_dir, target_day, strict_new_tech, offline_new_tech)
    coding_type = "ml" if target_day.toordinal() % 2 else "leetcode"
    coding_item = select_item(coding[coding_type], used_ids, f"{day_salt}:{coding_type}")
    hook = iq_item.get("hook") or hot_items[0].get("hook") or f"为什么“{iq_item['title']}”会让直觉先输一次？"
    answer_file_for_link = daily_dir / f"{target_day.isoformat()}-answers.md"
    try:
        answer_file_for_link = answer_file_for_link.relative_to(PROJECT_ROOT)
    except ValueError:
        pass
    answer_url = f"https://github.com/PengChengDream/DailyStudy/blob/main/{answer_file_for_link.as_posix()}"
    question_sections = [
        f"# {hook}\n\n日期：{target_day.isoformat()}\n\n答案版：[{target_day.isoformat()}-answers.md]({answer_url})\n",
        render_standard_question(1, "智商题", iq_item, include_answers=False),
        render_standard_question(2, "经典 ML/DL", classic_item, include_answers=False),
        render_standard_question(3, "热门技术", hot_items[0], include_answers=False),
        render_standard_question(4, "热门技术", hot_items[1], include_answers=False),
        render_standard_question(5, "近 7 天新技术", new_tech_item, include_answers=False),
        render_coding_question(6, coding_item, coding_type, include_answers=False),
    ]
    answer_sections = [
        f"# {hook}\n\n日期：{target_day.isoformat()}\n",
        render_standard_question(1, "智商题", iq_item, include_answers=True),
        render_standard_question(2, "经典 ML/DL", classic_item, include_answers=True),
        render_standard_question(3, "热门技术", hot_items[0], include_answers=True),
        render_standard_question(4, "热门技术", hot_items[1], include_answers=True),
        render_standard_question(5, "近 7 天新技术", new_tech_item, include_answers=True),
        render_coding_question(6, coding_item, coding_type, include_answers=True),
    ]
    question_content = "\n\n".join(question_sections) + "\n"
    answer_content = "\n\n".join(answer_sections) + "\n"

    questions = [
        {"slot": 1, "type": "iq", **log_item(iq_item)},
        {"slot": 2, "type": "ml_dl", **log_item(classic_item)},
        {"slot": 3, "type": "hot_tech", **log_item(hot_items[0])},
        {"slot": 4, "type": "hot_tech", **log_item(hot_items[1])},
        {"slot": 5, "type": "new_tech", **log_item(new_tech_item)},
        {"slot": 6, "type": coding_type, **log_item(coding_item)},
    ]
    daily_path = daily_dir / f"{target_day.isoformat()}.md"
    answer_path = daily_dir / f"{target_day.isoformat()}-answers.md"
    try:
        daily_file = daily_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        daily_file = daily_path.as_posix()
    try:
        month_bank = month_dir.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        month_bank = month_dir.as_posix()
    log_row = {
        "date": target_day.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "daily_file": daily_file,
        "answer_file": answer_path.relative_to(PROJECT_ROOT).as_posix()
        if answer_path.is_relative_to(PROJECT_ROOT)
        else answer_path.as_posix(),
        "month_bank": month_bank,
        "iso_week": iso_week_key(target_day),
        "coding_rotation": coding_type,
        "questions": questions,
        "next_actions": infer_next_actions(month_dir, coding_type, new_tech_item),
    }
    return question_content, answer_content, log_row


def log_item(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source", {})
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "source_title": source.get("title") or item.get("source_title"),
        "source_url": source.get("url") or item.get("url"),
        "published_at": source.get("published_at") or item.get("published_at"),
        "zhihu_candidate": bool(item.get("zhihu_candidate")),
        "manual_review": bool(item.get("manual_review")),
    }


def infer_next_actions(month_dir: Path, coding_type: str, new_tech_item: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    try:
        month_label = month_dir.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        month_label = month_dir.as_posix()
    if new_tech_item.get("manual_review"):
        actions.append("补充真实的近 7 天新技术来源后再正式发布。")
    if coding_type == "ml":
        actions.append("明天按轮换应选择 LeetCode 题。")
    else:
        actions.append("明天按轮换应选择 ML 编程题。")
    actions.append(f"月度题库路径：{month_label}。")
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one daily AI interview Markdown file.")
    parser.add_argument("--date", default=None, help="Target date, YYYY-MM-DD. Defaults to Beijing today.")
    parser.add_argument("--bank-root", default="question_bank")
    parser.add_argument("--daily-dir", default="daily")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--strict-new-tech", action="store_true", help="Fail if no real recent source is found.")
    parser.add_argument("--offline-new-tech", action="store_true", help="Use a clearly marked placeholder for local smoke tests.")
    parser.add_argument("--readme-path", default=None, help="Optional path to overwrite with the daily content, e.g. README.md.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    target_day = parse_date(args.date)
    bank_root = project_path(args.bank_root)
    daily_dir = project_path(args.daily_dir)
    log_dir = project_path(args.log_dir)
    daily_path = daily_dir / f"{target_day.isoformat()}.md"
    answer_path = daily_dir / f"{target_day.isoformat()}-answers.md"
    log_path = log_dir / f"{target_day.isoformat()}.jsonl"
    if daily_path.exists() and not args.overwrite:
        raise FileExistsError(f"{daily_path} exists. Use --overwrite to regenerate it.")
    if answer_path.exists() and not args.overwrite:
        raise FileExistsError(f"{answer_path} exists. Use --overwrite to regenerate it.")
    if args.overwrite and log_path.exists():
        log_path.unlink()

    question_content, answer_content, log_row = build_daily(
        target_day=target_day,
        bank_root=bank_root,
        daily_dir=daily_dir,
        log_dir=log_dir,
        strict_new_tech=args.strict_new_tech,
        offline_new_tech=args.offline_new_tech,
    )
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    daily_path.write_text(question_content, encoding="utf-8")
    answer_path.write_text(answer_content, encoding="utf-8")
    if args.readme_path:
        readme_path = project_path(args.readme_path)
        readme_path.write_text(question_content, encoding="utf-8")
    append_jsonl(log_path, log_row)
    print(f"Generated {daily_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
