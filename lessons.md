# Lessons Learned

Purpose: Keep short, practical lessons from implementation work so future changes are safer and faster.

How to update:
- Add newest entries at the top.
- Keep each lesson concise and actionable.
- Focus on why the change mattered and what to repeat next time.

---

## 2026-03-28 (CI Test Package Shadowing)

- `python -m unittest tests.test_daily_loss_scope` is brittle on shared runners because a different top-level `tests` package can be resolved before the repo's test directory if `tests/` is not an explicit package.
- The safer pattern here is to add `tests/__init__.py` and run `python -m unittest discover -s tests -p "test_*.py"` in CI and docs so validation does not depend on ambiguous package resolution.

## 2026-03-28 (GitHub Repo Kit And Docs Hygiene)

- If a repository expects tracked GitHub workflows, issue templates, or workspace skills, `.gitignore` must not blanket-ignore `.github/`; otherwise the repo can look complete locally while silently blocking the files that make the public project usable.
- For script-first repos, a practical public-ready setup is usually better than package-style ceremony: add license, contributor/security docs, issue/PR templates, dependency manifest, and honest lightweight CI, then update README and operations docs so the new files are discoverable.

## 2026-03-19 (Shared Forex Loss And Soft Stops)

- In a high-ADX, risk-off regime, full basket flattening on soft loss stops tends to realize the worst part of the move. Trimming newer expansion legs back to the oldest hedge pair preserves more recovery potential while still cutting pressure.
- If multiple forex bots share one account and are meant to behave like one cluster, give them one shared forex-only daily-loss scope instead of separate budgets; otherwise they can all lose together while each still thinks it has room left.

## 2026-03-19 (Bot-Scoped Daily Loss)

- When multiple MT5 bots share one account, daily-loss checks should not be derived from total account equity if the limit is meant to be bot-specific; that couples unrelated bots and makes one strategy consume another's daily-loss budget.
- The safer pattern is to compute current UTC-day bot P/L from MT5 deal history plus open-position P/L filtered by `SYMBOL` and `MAGIC`, while leaving `GLOBAL_*` protections account-wide.

## 2026-03-18 (NAS100 Conservative Retune)

- For Exness `USTECm`, a conservative retune should usually reduce both level growth and expansion frequency together; the March 17-18 logs showed recurring spreads around `1.92-2.16` while M5 ATR compressed into roughly `7-10`, so lower multipliers alone would still leave the grid too eager.
- When a live bot profile changes, sync the template file, local credentialed copy, startup labels, README/docs, changelog, lessons, and project memory in the same pass so current-state references do not drift.

## 2026-03-17 (NAS100 Trend Removal Cleanup)

- When a bot is removed from the repo, clean up every current-state reference together: `README.md`, `docs/`, `CLAUDE.md`, workspace skills, ignore rules, and project memory.
- Keep changelog history intact; add a new removal note instead of rewriting older release entries that documented the bot when it still existed.

## 2026-03-17 (Template & Credential Security Implementation)

- Implemented template-based credential management: grid bots with credentials (`*_grid_bot.py`) are now gitignored, while template files (`*.template.py`) are tracked in version control.
- Created `.gitignore` to protect MT5 credentials from accidental commits.
- When making bot changes, always edit the `.template.py` file first, then manually sync to the local `*_grid_bot.py` (which has actual credentials).
- This pattern allows sharing bot configurations and code via git without exposing sensitive MT5 login credentials.
- The template pattern applies to local bot wrappers, while shared tracked files like `forex_grid_engine.py` remain directly versioned.

## 2026-03-17 (Parallel Capacity Improvements)

- A single global position cap can unintentionally stall multi-bot grids when baseline hedge starts consume all slots.
- Split gating works better than a single hard block: throttle new starts earlier and keep a small reserve for active basket expansion.
- Keep one hard cap in place for survival, then tune throughput with a reserve value instead of removing the cap entirely.
- Cross-bot coordination should account for any future non-grid strategies so they do not silently bypass shared account-wide capacity limits.
