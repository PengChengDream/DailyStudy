# DailyStudy AI Agent Guide

## Objective

This repository publishes one daily AI interview practice set to GitHub. The homepage `README.md` must always mirror the current day's question-only file. The answer file is stored separately.

Daily outputs:

- `history/YYYY-MM-DD.md`: question-only version, copied to `README.md`.
- `history/YYYY-MM-DD-answers.md`: questions plus reference answers.
- `logs/YYYY-MM-DD.jsonl`: machine-readable generation log.
- `weekly/YYYY-WW-zhihu-draft.md`: weekly hand-picked Zhihu draft candidates.

## Daily Schedule

The daily automation should run at 08:00 Beijing time.

GitHub Actions uses UTC, so 08:00 Asia/Shanghai is:

```yaml
cron: "0 0 * * *"
```

The normal daily command is:

```bash
python scripts/build_monthly_bank.py --month "$YYYY_MM" --fetch-dynamic
python scripts/generate_daily.py --date "$YYYY_MM_DD" --daily-dir history --strict-new-tech --overwrite --readme-path README.md
python scripts/generate_weekly_zhihu.py --date "$YYYY_MM_DD" --if-sunday
python scripts/validate_plan.py --start-date "$YYYY_MM_DD" --days 1
```

After generation, commit and push:

```bash
git add README.md history weekly logs question_bank
git commit -m "chore: daily AI questions $YYYY_MM_DD"
git push
```

If this is a fresh local checkout without remote configuration:

```bash
git remote add origin https://github.com/PengChengDream/DailyStudy.git
git branch -M main
git push -u origin main
```

Only run `git init` manually when the directory is not already a git repository.

## What AI Should Do

Use AI assistance for content quality, not for mechanical file generation.

AI-assisted tasks:

- Extract one "recent technology" interview question from public Chinese AI media, prioritizing 量子位 and 机器之心, within the last 7 days.
- Rewrite public big-tech interview experiences and discussions into original, non-infringing interview questions.
- Generate concise reference answers, follow-up questions, and knowledge points.
- Judge whether a question is duplicated, stale, too easy, too broad, or suitable for weekly Zhihu selection.
- During monthly refresh, expand `question_bank/YYYY-MM/`, classify by topic, remove duplicates, and keep difficulty balanced.

Rule-based tasks:

- Rotate LeetCode and ML coding questions.
- Select questions from local JSON banks.
- Generate Markdown files.
- Write JSONL logs.
- Update `README.md`.
- Generate weekly draft files.

## Log-Driven Workflow

Before changing a question bank, read recent logs:

```bash
python - <<'PY'
from pathlib import Path
import json
for path in sorted(Path("logs").glob("*.jsonl"))[-14:]:
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        print(row["date"], row["coding_rotation"], [q["id"] for q in row["questions"]])
PY
```

Use the logs to decide:

- Which topics have appeared too often.
- Which banks are running low on unused questions.
- Whether LeetCode/Deep-ML rotation is intact.
- Which questions deserve `zhihu_candidate: true`.
- Whether the next monthly refresh should emphasize ML/DL basics, LLM/RAG/Agent, AI infra, multimodal, recommender systems, or coding.

## Recent Technology Question Rules

Preferred sources:

- 量子位: `https://www.qbitai.com/`
- 机器之心: `https://www.jiqizhixin.com/articles`

The recent technology item must:

- Be published within 7 days of the target date.
- Include title, URL, and `published_at`.
- Be rewritten as an interview question, not copied as a news paragraph.
- Include `points`, `hint`, `answer`, and `zhihu_candidate`.
- Prefer technology judgment questions over simple news recall.

Allowed manual format in `question_bank/YYYY-MM/new_tech_manual.json`:

```json
{
  "id": "new-tech-YYYY-MM-DD-short-id",
  "type": "new_tech",
  "title": "article title",
  "question": "rewritten interview question",
  "points": ["技术本质", "落地约束", "风险边界"],
  "hint": "short reasoning hint",
  "answer": "concise reference answer",
  "source": {
    "title": "source title",
    "url": "https://...",
    "published_at": "YYYY-MM-DD"
  },
  "zhihu_candidate": true
}
```

## Interview Bank Update Rules

Use public big-company interview experiences only as topic signals. Do not copy original posts, long passages, or platform problem statements.

Good source categories:

- Public Nowcoder interview experiences for ByteDance, Alibaba, Tencent, Baidu, Kuaishou, Xiaohongshu.
- Public overseas MLE/AI engineer interview discussions.
- GitHub interview question repos.
- Official company blogs and technical reports.

For each new question, write original content:

- `title`
- `question`
- `points`
- `hint`
- `answer`
- `source.title`
- `source.url`
- `zhihu_candidate`

Keep answers concise and interview-focused.

## Coding Question Rules

LeetCode:

- Store only problem number, title, difficulty, tags, URL, self-written summary, hint, and answer.
- The URL must be the exact problem page: `https://leetcode.com/problems/.../`.
- Do not copy full LeetCode problem statements.

Deep-ML:

- Prefer actual Deep-ML problem pages.
- The URL must be the exact problem page: `https://www.deep-ml.com/problems/<id>`.
- Keep reference solutions under 30 non-empty lines.

Validation enforces these link rules.

## Duplicate And Quality Checks

Before adding a question:

- Search existing monthly and base banks for similar titles and points.
- Avoid repeating the same concept more than twice in a week.
- Prefer questions with a concrete interview angle.
- Mark `zhihu_candidate: true` only if the question can spark discussion and the answer teaches a reusable reasoning pattern.

## Copyright Boundaries

Do not copy:

- LeetCode full problem statements.
- Deep-ML full statements if not necessary.
- Full interview experience posts.
- Long excerpts from news articles, books, or blogs.

Allowed:

- Short titles and links.
- Self-written summaries.
- Original rewritten questions.
- Concise commentary and reference answers.

## Required Validation

Before committing generated content, run:

```bash
python -m py_compile scripts/common.py scripts/generate_daily.py scripts/build_monthly_bank.py scripts/generate_weekly_zhihu.py scripts/validate_plan.py
python scripts/validate_plan.py --start-date "$YYYY_MM_DD" --days 1
```

For larger bank updates, run:

```bash
python scripts/validate_plan.py --start-date "$YYYY_MM_DD" --days 7
```
