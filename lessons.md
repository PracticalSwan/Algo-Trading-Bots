# Lessons Learned

Purpose: Keep short, practical lessons from implementation work so future changes are safer and faster.

How to update:
- Add newest entries at the top.
- Keep each lesson concise and actionable.
- Focus on why the change mattered and what to repeat next time.

---

## 2026-03-17 (Template & Credential Security Implementation)

- Implemented template-based credential management: grid bots with credentials (`*_grid_bot.py`) are now gitignored, while template files (`*.template.py`) are tracked in version control.
- Created `.gitignore` to protect MT5 credentials from accidental commits.
- When making bot changes, always edit the `.template.py` file first, then manually sync to the local `*_grid_bot.py` (which has actual credentials).
- This pattern allows sharing bot configurations and code via git without exposing sensitive MT5 login credentials.
- The trend bot (`nas100_trend_bot.py`) and forex grid engine (`forex_grid_engine.py`) remain tracked directly as they don't contain hardcoded credentials.

## 2026-03-17 (Parallel Capacity Improvements)

- A single global position cap can unintentionally stall multi-bot grids when baseline hedge starts consume all slots.
- Split gating works better than a single hard block: throttle new starts earlier and keep a small reserve for active basket expansion.
- Keep one hard cap in place for survival, then tune throughput with a reserve value instead of removing the cap entirely.
- Cross-bot coordination should include non-grid strategies too, so trend entries do not silently bypass account-wide capacity limits.
