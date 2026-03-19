# Lessons Learned

Purpose: Keep short, practical lessons from implementation work so future changes are safer and faster.

How to update:
- Add newest entries at the top.
- Keep each lesson concise and actionable.
- Focus on why the change mattered and what to repeat next time.

---

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
