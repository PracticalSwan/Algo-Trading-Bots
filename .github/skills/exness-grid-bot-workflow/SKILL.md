---
name: exness-grid-bot-workflow
description: Use when creating, tuning, or reviewing Exness MT5 grid bots in this repository, especially for parallel multi-bot operation with account safety, market-session-aware profile mapping, adaptive growth controls, and required memory/documentation updates.
---

# Exness Grid Bot Workflow

## Overview

Repository-specific playbook for building and tuning Exness MT5 grid bots with a survival-first approach for small accounts.

Primary goal: improve consistency of outcomes by combining session-aware profile selection, strict execution safety, and account-level drawdown protection.

## When to Use

- Adding a new forex grid bot wrapper.
- Retuning existing grid profiles (Aggressive, Balanced, Conservative).
- Running multiple bots in parallel on one account.
- Adding Exness/MT5 execution safety controls.
- Updating growth-adaptive sizing/risk parameters.

Do not use this for non-grid strategies.

## Serena-First Context Workflow

1. Read `C:/Users/LOQ/.agents/skills/serena-usage/SKILL.md`.
2. Run `mcp_oraios_serena_get_current_config`.
3. If no active project, activate/select `Exness_Bot`.
4. Run `mcp_oraios_serena_check_onboarding_performed`.
5. If onboarding is incomplete, run `mcp_oraios_serena_initial_instructions` then `mcp_oraios_serena_onboarding`.
6. Record key tuning decisions and risk changes to repository memory before finishing.

## Market-Condition Research Rules

Use at least one reliable source before major retuning.

Current working assumptions used in this repository:

- Sydney/Tokyo session typically drives higher activity in AUD, NZD, and JPY-linked pairs.
- EUR and GBP pairs are generally more active during London/NY overlaps; Asia can be quieter but off-session spreads may widen.
- USDCAD is usually most event-active during North American hours; Asia tends to be quieter.

If source fetch fails due anti-bot blocks, proceed with these assumptions and bias toward safer settings.

## Profile Bands for This Repository

Use these as tuning ranges, then adjust per symbol behavior.

- Aggressive:
  - `LOT_MULTIPLIER`: 1.18-1.25
  - `MAX_LOT`: 0.04-0.05
  - `MAX_LEVELS`: 6
  - `GROWTH_LOT_EXPONENT`: 0.72-0.80
- Balanced:
  - `LOT_MULTIPLIER`: 1.08-1.14
  - `MAX_LOT`: 0.03-0.04
  - `MAX_LEVELS`: 5
  - `GROWTH_LOT_EXPONENT`: 0.60-0.70
- Conservative:
  - `LOT_MULTIPLIER`: 1.00
  - `MAX_LOT`: 0.015-0.02
  - `MAX_LEVELS`: 4
  - `GROWTH_LOT_EXPONENT`: 0.45-0.55

## Required Safety Controls

Every grid bot must keep these behaviors:

- Ticket-bound close requests (`position=pos.ticket`).
- Symbol-aware filling mode (`IOC -> FOK -> RETURN`).
- Trade success validation on `TRADE_RETCODE_DONE` and `TRADE_RETCODE_DONE_PARTIAL`.
- Parallel account gates:
  - `GLOBAL_MAX_ACCOUNT_POSITIONS`
  - `GLOBAL_MAX_FLOATING_DRAWDOWN_USD`
  - `GLOBAL_MIN_FREE_MARGIN_USD`
  - `GLOBAL_MIN_MARGIN_LEVEL_PCT`
  - `GLOBAL_SOFT_EQUITY_STOP`
- Growth adaptation keys:
  - `AUTO_GROWTH_ENABLED`
  - `GROWTH_BASE_EQUITY`
  - `GROWTH_MAX_FACTOR`
  - `GROWTH_LOT_EXPONENT`
  - `GROWTH_TP_EXPONENT`
  - `GROWTH_RISK_EXPONENT`
  - `GROWTH_EQUITY_LOCK_RATIO`

## Implementation Checklist

1. Select target symbol and profile by session behavior.
2. Tune wrapper config values and keep global safety keys aligned across bots.
3. Verify MT5 symbol formatting (Exness suffixes like `EURUSDm`, `USTECm`).
4. Compile all bots:

```powershell
python -m py_compile forex_grid_engine.py eurusd_grid_bot.py gbpusd_grid_bot.py usdjpy_grid_bot.py audusd_grid_bot.py nzdusd_grid_bot.py usdcad_grid_bot.py nas100_grid_bot.py
```

5. Update `README.md` and `CHANGELOG.md` when settings/behavior change.
6. Update repository memory with what changed and why.

## Common Mistakes

- Using different global safety thresholds across wrappers when bots run in parallel.
- Treating quiet-session pairs as always low-risk without spread checks.
- Raising lot growth too fast (`GROWTH_LOT_EXPONENT` too high) on small equity.
- Retuning configs without updating docs and memory.
