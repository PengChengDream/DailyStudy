from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - Python < 3.9 fallback is not expected.
    ZoneInfo = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
try:
    BEIJING_TZ = ZoneInfo("Asia/Shanghai") if ZoneInfo else timezone(timedelta(hours=8))
except Exception:
    BEIJING_TZ = timezone(timedelta(hours=8))


def today_beijing() -> date:
    return datetime.now(BEIJING_TZ).date()


def parse_date(value: str | None) -> date:
    if not value:
        return today_beijing()
    return date.fromisoformat(value)


def month_key(day: date) -> str:
    return day.strftime("%Y-%m")


def iso_week_key(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def stable_int(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def select_item(items: list[dict[str, Any]], used_ids: set[str], salt: str) -> dict[str, Any]:
    if not items:
        raise ValueError(f"No items available for {salt}")
    unused = [item for item in items if item.get("id") not in used_ids]
    pool = unused or items
    return pool[stable_int(salt) % len(pool)]


def select_items(
    items: list[dict[str, Any]],
    used_ids: set[str],
    count: int,
    salt: str,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    local_used = set(used_ids)
    for index in range(count):
        item = select_item(items, local_used, f"{salt}:{index}")
        selected.append(item)
        if item.get("id"):
            local_used.add(item["id"])
    return selected


def read_generation_logs(log_dir: Path) -> list[dict[str, Any]]:
    if not log_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(log_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"log_parse_error": str(path), "raw": line})
    return rows


def used_question_ids(log_dir: Path) -> set[str]:
    used: set[str] = set()
    for row in read_generation_logs(log_dir):
        for question in row.get("questions", []):
            qid = question.get("id")
            if qid:
                used.add(qid)
    return used


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def markdown_list(values: Iterable[str]) -> str:
    values = [value for value in values if value]
    return "、".join(values) if values else "无"


def code_line_count(code: str) -> int:
    return len([line for line in code.splitlines() if line.strip()])


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path
