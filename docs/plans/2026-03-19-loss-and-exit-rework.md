# Loss And Exit Rework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Retune daily-loss limits for March 2026 market conditions, combine forex bots under one shared forex-only daily-loss cap, and replace destructive soft-stop full-flatten behavior with trim-to-core plus freeze logic.

**Architecture:** Keep hard account protections (`GLOBAL_*`, `EQUITY_STOP`, `BASKET_TP`, incomplete starts) intact, but move soft loss handling to a smaller helper-driven flow. The shared forex engine will compute one combined forex daily P/L scope across all forex bots, while NAS100 keeps its own scope. On soft-stop events, bots trim expansion legs back to the oldest hedge pair and disable new starts/expansions until the next UTC day instead of flattening everything.

**Tech Stack:** Python 3, MetaTrader5, unittest, repository templates + local credentialed bot files

---

### Task 1: Add failing helper tests for grouped forex loss and trim-to-core logic

**Files:**
- Modify: `tests/test_daily_loss_scope.py`

**Step 1: Write the failing test**

Add tests for:
- Combined forex P/L over multiple `SYMBOL` + `MAGIC` pairs
- Selecting expansion legs to close while keeping the oldest BUY and SELL positions

**Step 2: Run test to verify it fails**

Run: `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
Expected: FAIL because grouped scope and trim helpers do not exist yet.

**Step 3: Write minimal implementation**

Implement grouped scope matching and trim helpers in `daily_loss_scope.py`.

**Step 4: Run test to verify it passes**

Run: `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
Expected: PASS

### Task 2: Rework forex engine soft-stop behavior and combined forex loss cap

**Files:**
- Modify: `forex_grid_engine.py`
- Modify: `eurusd_grid_bot.py.template`
- Modify: `gbpusd_grid_bot.py.template`
- Modify: `usdjpy_grid_bot.py.template`
- Modify: `audusd_grid_bot.py.template`
- Modify: `nzdusd_grid_bot.py.template`
- Modify: `usdcad_grid_bot.py.template`
- Modify: `eurusd_grid_bot.py`
- Modify: `gbpusd_grid_bot.py`
- Modify: `usdjpy_grid_bot.py`
- Modify: `audusd_grid_bot.py`
- Modify: `nzdusd_grid_bot.py`
- Modify: `usdcad_grid_bot.py`

**Step 1: Write the failing test**

Add source-based assertions that:
- Forex uses a shared combined forex daily-loss scope
- Forex no longer closes all positions on daily-loss or session-end
- Forex enters a freeze/lock state until next UTC day after soft-stop trim

**Step 2: Run test to verify it fails**

Run: `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
Expected: FAIL because engine still uses the old soft-stop flow.

**Step 3: Write minimal implementation**

Implement:
- shared forex group scope
- shared forex `DAILY_MAX_LOSS_USD`
- trim-to-core function call on daily-loss
- freeze-until-next-day behavior
- no session-end flattening outside Asia hours

**Step 4: Run test to verify it passes**

Run: `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
Expected: PASS

### Task 3: Rework NAS100 manual stop and soft-stop behavior

**Files:**
- Modify: `nas100_grid_bot.py.template`
- Modify: `nas100_grid_bot.py`
- Modify: `tests/test_daily_loss_scope.py`

**Step 1: Write the failing test**

Add assertions that:
- `KeyboardInterrupt` no longer calls `close_all_positions(reason="MANUAL_STOP")`
- NAS100 trims to core on daily-loss instead of flattening
- NAS100 pauses during news blackout rather than force-closing positions

**Step 2: Run test to verify it fails**

Run: `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
Expected: FAIL because NAS100 still uses the old close-all flow.

**Step 3: Write minimal implementation**

Implement:
- manual stop as disconnect-only
- smaller NAS100 daily-loss cap
- trim-to-core plus freeze logic
- news blackout as no-new-risk pause, not forced flatten

**Step 4: Run test to verify it passes**

Run: `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
Expected: PASS

### Task 4: Update docs and validate runtime syntax

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/operations-and-troubleshooting.md`
- Modify: `docs/strategy-and-profiles.md`
- Modify: `CLAUDE.md`
- Modify: `lessons.md`

**Step 1: Update docs**

Document:
- combined forex daily-loss cap
- tighter NAS100 daily-loss cap
- trim-to-core behavior
- no manual flatten on stop
- session/news pause behavior

**Step 2: Run verification**

Run:
- `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m unittest tests.test_daily_loss_scope`
- `C:\Users\LOQ\AppData\Local\Python\bin\python.exe -m py_compile daily_loss_scope.py forex_grid_engine.py eurusd_grid_bot.py gbpusd_grid_bot.py usdjpy_grid_bot.py audusd_grid_bot.py nzdusd_grid_bot.py usdcad_grid_bot.py nas100_grid_bot.py nas100_grid_bot.py.template`

Expected:
- Tests PASS
- `py_compile` exits with code 0
