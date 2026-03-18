# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---
## [Unreleased]

### Removed
- Removed `nas100_trend_bot.py` from the active repository bot lineup.

### Changed
- Updated repo documentation, workflow guidance, and ignore rules to remove current-state references to the deleted NAS100 trend bot while preserving historical changelog entries.
- Retuned `nas100_grid_bot.py` and `nas100_grid_bot.py.template` from aggressive to conservative for current Exness `USTECm` conditions by setting `LOT_MULTIPLIER=1.00`, `MAX_LOT=0.02`, `MAX_LEVELS=4`, `GROWTH_LOT_EXPONENT=0.50`, `GRID_ATR_MULTIPLIER=1.00`, and `MIN_GRID_STEP_PRICE=18.0`.
- Updated current-state docs and workflow guidance to reflect NAS100 as the conservative, news-aware `USTECm` grid variant.


## [1.0.8] — 2026-03-17

### Added
- Added `nas100_grid_bot.py.template` template file without credentials for version control.
- Added diagnostic logging for news filtering: next event details and position status during blackout.

### Changed
- Enhanced news blackout logging to clarify why positions are or aren't closed during news events.

## [1.0.7] — 2026-03-17

### Changed
- Raised shared parallel hard cap from `GLOBAL_MAX_ACCOUNT_POSITIONS=12` to `16` across all forex grid wrappers and `nas100_grid_bot.py`.
- Added `GLOBAL_POSITION_RESERVE_FOR_EXPANSION=4` to grid bots, with split gating logic so new basket starts are throttled earlier while active baskets can still expand until the hard cap.
- Updated `forex_grid_engine.py` and `nas100_grid_bot.py` logging/dashboard output to show both global hard cap and start-cap reserve behavior.
- Updated `nas100_trend_bot.py` to respect an account-wide global position cap before opening new trend entries, improving cross-bot coordination during parallel runtime.

### Added
- Added `lessons.md` as a persistent implementation-learning log for this repository.
- Added an explicit `CLAUDE.md` instruction to update `lessons.md` after implementation work.

## [1.0.6] — 2026-03-13

### Fixed
- Fixed MT5 account info compatibility crash in `nas100_grid_bot.py` and `forex_grid_engine.py` by supporting both `free_margin` and `margin_free` account fields.
- Added safe free-margin guards that skip the cycle (with log message) if neither field is present, preventing runtime `AttributeError` and protecting all forex wrapper bots plus NAS100 grid.

## [1.0.5] — 2026-03-13

### Added
- Added workspace skill: `.github/skills/exness-grid-bot-workflow/SKILL.md` for repeatable grid-bot creation/tuning workflow (Exness MT5 integration, market-condition research, parallel safety checks, growth controls, and documentation/memory steps).

### Changed
- Retuned all forex grid bots with session-aware profile placement for parallel runtime:
	- Aggressive: EURUSD
	- Balanced: GBPUSD, USDJPY, USDCAD
	- Conservative: AUDUSD, NZDUSD
- Tightened shared parallel safety limits in forex wrappers (`GLOBAL_MAX_ACCOUNT_POSITIONS`, floating drawdown cap, free-margin floor, margin-level floor, and soft-equity stop).
- Retuned `nas100_grid_bot.py` aggressive settings for lower parallel account pressure (smaller lot cap/levels, tighter global safety thresholds, adjusted ATR and ADX gates).
- Added explicit Serena workflow section to repository `CLAUDE.md` requiring activation/config checks and onboarding checks before Serena operations.
- Updated README profile tables and rationale to reflect new market-condition-based settings and current live config values.

## [1.0.4] — 2026-03-13

### Added
- Added account-growth adaptation logic across all bots so sizing and limits adjust as equity increases, with capped scaling and equity-lock safeguards.

### Changed
- Updated `forex_grid_engine.py` to scale start/max lot, basket TP model, daily loss threshold, and global safety thresholds from equity growth factor.
- Updated all six forex grid wrapper configs with explicit growth-control parameters (`AUTO_GROWTH_ENABLED`, `GROWTH_*`).
- Updated `nas100_grid_bot.py` to apply the same growth-adaptive sizing and risk-threshold scaling.
- Updated `nas100_trend_bot.py` with growth-adaptive lot sizing, dynamic trade/position limits, and growth-based equity stop floor.
- Updated README to document growth adaptation parameters and behavior.

## [1.0.3] — 2026-03-13

### Added
- Added `forex_grid_engine.py` as a shared execution engine for all six forex grid bots.

### Changed
- Overhauled `eurusd_grid_bot.py`, `gbpusd_grid_bot.py`, `usdjpy_grid_bot.py`, `audusd_grid_bot.py`, `nzdusd_grid_bot.py`, and `usdcad_grid_bot.py` to use real-market adaptive logic (ATR-based step sizing, ADX trend pause, spread-vs-volatility filtering, dynamic basket TP scaling).
- Tuned all six forex grid profiles for a 50 USD account context with relative profile behavior preserved: aggressive (EURUSD/GBPUSD), balanced (USDJPY), conservative (AUDUSD/NZDUSD/USDCAD).
- Added account-wide parallel safety controls in forex bots (global open-position cap, global floating drawdown cap, free-margin guard, and margin-level guard).
- Tightened `nas100_grid_bot.py` for parallel operation with lower exposure limits and account-wide safety gates aligned to multi-bot runtime.
- Updated README to document the new shared engine architecture, profile settings, and parallel safety parameters.

## [1.0.2] — 2026-03-13

### Added
- Added `nas100_grid_bot.py` — an aggressive NAS100 (USTECm) grid bot designed for all available market hours (Mon–Fri) with high-impact USD news blackout handling.
- Added ForexFactory XML-based high-impact news filter (`ff_calendar_thisweek.xml`) with configurable before/after blackout windows and optional pre-news position flattening.
- Added ATR-adaptive grid spacing, ADX trend-strength expansion pause, and spread-vs-ATR guard to make grid behavior more aligned with real intraday index volatility conditions.

### Changed
- Updated README with new NAS100 aggressive grid bot usage, configuration parameters, and MT5/news integration references.

## [1.0.1] — 2026-03-13

### Fixed
- Fixed `close_all_positions()` across all grid bots so each close request is bound to the exact MT5 position ticket (`position=pos.ticket`). This resolves Exness hedging-account cases where opposite orders were sent but positions stayed open.
- Added stronger close-failure logging (`retcode` + broker comment) so rejected closes are visible immediately in logs.
- Added the same ticket-bound close flow to `nas100_trend_bot.py` for emergency-stop and `Ctrl+C` shutdown handling.
- Hardened all bots to treat trades as successful only on `TRADE_RETCODE_DONE` / `TRADE_RETCODE_DONE_PARTIAL` instead of assuming non-null `order_send()` results mean filled orders.
- Hardened all bots to select `type_filling` from symbol-supported flags (`SYMBOL_FILLING_MODE`) with `IOC` -> `FOK` -> `RETURN` fallback logic, reducing broker-specific fill rejections.
- Added symbol/tick guards before order placement and grid maintenance calculations to prevent runtime crashes and silent bad execution states when market data is temporarily unavailable.

## [1.0.0] — 2026-03-12

### Added
- `eurusd_grid_bot.py` — Grid bot for EURUSD, Asia session (22:00–08:00 UTC). Martingale lot multiplier (×1.15), 8 levels, basket TP $2.80.
- `gbpusd_grid_bot.py` — Grid bot for GBPUSD, Asia session. Martingale lot multiplier (×1.2), 8 levels, basket TP $3.00.
- `audusd_grid_bot.py` — Grid bot for AUDUSD, Asia session. Fixed lot, 5 levels, basket TP $1.80.
- `nzdusd_grid_bot.py` — Grid bot for NZDUSD, Asia session. Fixed lot, 5 levels, basket TP $1.80.
- `usdcad_grid_bot.py` — Grid bot for USDCAD, Asia session. Fixed lot, 5 levels, basket TP $2.00.
- `usdjpy_grid_bot.py` — Grid bot for USDJPY, Asia session. Martingale lot multiplier (×1.1), 7 levels, basket TP $2.50.
- `nas100_trend_bot.py` — Trend-following bot for NAS100 (USTECm). M15 timeframe, EMA/RSI/ADX entry, ATR trailing stop, breakeven logic. Trades 08:00–17:00 UTC.
- `logs/` directory — Auto-created at runtime; daily rotating log files per bot.
- Shared risk controls across all bots: daily max loss, minimum equity stop, cooldown after basket close, weekday-only trading guard.
