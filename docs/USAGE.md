# DailyStudy 自动题库说明

## 每日发布

- GitHub Actions 每天北京时间 08:00 运行 `.github/workflows/daily-ai-questions.yml`。
- 生成 `history/YYYY-MM-DD.md` 题目+答案版，并用同一份内容覆盖根目录 `README.md`，所以仓库首页会直接显示当天完整内容。
- 同时写入 `logs/YYYY-MM-DD.jsonl`，记录题目 id、来源、轮换状态和下一步建议。

## 月度题库

- 每月题库位于 `question_bank/YYYY-MM/`。
- 每月 1 日北京时间 09:00 运行 `.github/workflows/monthly-question-bank.yml`，创建或刷新当月题库候选来源。
- 自动刷新只保存来源链接和候选信息；真正入库的题目仍应改写后写入 JSON，避免复制面经原文或平台题面。
- 当前每日题目不再包含趣味短文。普通问题不显示提示和来源；编程题保留对应题目的 LeetCode 或 Deep-ML problem 链接。`README.md` 与 `history/YYYY-MM-DD.md` 内容一致，均包含答案。

## 本地命令

```powershell
python scripts/build_monthly_bank.py --month 2026-05 --overwrite
python scripts/generate_daily.py --date 2026-05-29 --daily-dir history --offline-new-tech --overwrite --readme-path README.md
python scripts/validate_plan.py --start-date 2026-05-29 --days 7
```

正式发布建议不要使用 `--offline-new-tech`。GitHub Actions 使用 `--strict-new-tech`，会优先从量子位、机器之心等中文 AI 科技媒体抓取近 7 天热点；如果抓不到公开网页源，也没有手动维护的新技术来源，会失败而不是发布占位内容。

## 推送到 GitHub

如果本地目录还没有绑定远程仓库：

```powershell
git init
git remote add origin https://github.com/PengChengDream/DailyStudy.git
git add .
git commit -m "init daily AI interview question generator"
git branch -M main
git push -u origin main
```

推送后在仓库 Settings -> Actions -> General 确认 workflow 有写入权限，或者使用仓库默认的 `GITHUB_TOKEN` contents write 权限。

后续 AI 辅助更新题库和内容质量控制的规则见根目录 `AGENT.md`。
