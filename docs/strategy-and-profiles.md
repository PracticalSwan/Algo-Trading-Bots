# Strategy And Profiles

## Strategy summary

### Forex grid bots

The six forex bots are thin wrappers around `forex_grid_engine.py`.

Core behavior:

- Start with a BUY and SELL hedge.
- Add levels only when ATR-based spacing conditions are met.
- Pause new expansion when ADX suggests a strong one-way trend.
- Filter entries when spread is too large for current volatility.
- Close by exact MT5 ticket targeting.
- Flatten at the end of the Asia session.

### NAS100 conservative grid bot

`nas100_grid_bot.py` applies the same survival-first grid philosophy to `USTECm`, but it is now tuned as a conservative index grid for current Exness conditions:

- ATR-adaptive spacing
- wider minimum spacing for quieter ATR regimes
- ADX trend pause
- high-impact USD news blackout
- optional position flattening around blocked events
- growth-aware sizing and safety thresholds

Current NAS100 settings:

- `LOT_MULTIPLIER = 1.00`
- `MAX_LOT = 0.02`
- `MAX_LEVELS = 4`
- `GROWTH_LOT_EXPONENT = 0.50`
- `GRID_ATR_MULTIPLIER = 1.00`
- `MIN_GRID_STEP_PRICE = 18.0`

## Why the sessions differ

### Forex grid session: 22:00-08:00 UTC

The forex grid bots target the quieter Asia window because range-bound behavior is more useful for basket-style mean reversion than fast directional movement.

High-level placement:

| Pair group | Why it fits |
|---|---|
| AUDUSD, NZDUSD, USDJPY | Asia-Pacific participation is naturally stronger in this window. |
| EURUSD, GBPUSD | Europe and the US are quieter, which often reduces directional pressure. |
| USDCAD | North American catalysts are usually quieter during Asia hours. |

All forex baskets are flattened before the London open at 08:00 UTC.

### NAS100 grid availability: market hours, Mon-Fri

The NAS100 grid bot stays aligned to index market availability instead of the forex Asia window:

- index volatility is more usable when the underlying cash and futures participation is active
- high-impact USD events are explicitly blacked out
- optional pre-news flattening reduces event shock exposure

## Current forex profile ranges

| Profile | Typical use | Lot multiplier | Max lot | Max levels | Growth lot exponent |
|---|---|---|---|---|---|
| Aggressive | Faster recovery, higher pressure | `1.18-1.25` | `0.04-0.05` | `6` | `0.72-0.80` |
| Balanced | Middle ground for parallel runtime | `1.08-1.14` | `0.03-0.04` | `5` | `0.60-0.70` |
| Conservative | Lower pressure, fixed-lot style behavior | `1.00` | `0.015-0.02` | `4` | `0.45-0.55` |

## Current per-bot forex settings

| Bot | Profile | Lot multiplier | Max lot | Max levels | Base basket TP | Daily max loss | Min equity stop |
|---|---|---|---|---|---|---|---|
| EURUSD | Aggressive | `1.22` | `0.05` | `6` | `$1.45` | `$2.90` | `$30.00` |
| GBPUSD | Balanced | `1.12` | `0.035` | `5` | `$1.25` | `$2.30` | `$30.00` |
| USDJPY | Balanced | `1.10` | `0.035` | `5` | `$1.20` | `$2.20` | `$30.00` |
| AUDUSD | Conservative | `1.00` | `0.018` | `4` | `$0.78` | `$1.60` | `$30.50` |
| NZDUSD | Conservative | `1.00` | `0.016` | `4` | `$0.75` | `$1.50` | `$30.50` |
| USDCAD | Balanced | `1.08` | `0.030` | `5` | `$1.05` | `$2.00` | `$30.20` |

## Shared safety model

These controls are intentionally aligned across the grid bots so they can run in parallel on the same account:

- `GLOBAL_MAX_ACCOUNT_POSITIONS = 16`
- `GLOBAL_POSITION_RESERVE_FOR_EXPANSION = 4`
- `GLOBAL_MAX_FLOATING_DRAWDOWN_USD = 8.50`
- `GLOBAL_MIN_FREE_MARGIN_USD = 10.00`
- `GLOBAL_MIN_MARGIN_LEVEL_PCT = 250.0`
- `GLOBAL_SOFT_EQUITY_STOP = 29.00`

Split gating matters:

- New baskets are blocked once the account reaches 12 open positions.
- Existing baskets may still expand until the hard cap of 16.

## Growth adaptation

The bots support bounded growth controls so size and thresholds can scale with equity while still locking in part of the gains. Key controls include:

- `AUTO_GROWTH_ENABLED`
- `GROWTH_BASE_EQUITY`
- `GROWTH_MAX_FACTOR`
- `GROWTH_LOT_EXPONENT`
- `GROWTH_TP_EXPONENT`
- `GROWTH_RISK_EXPONENT`
- `GROWTH_EQUITY_LOCK_RATIO`

Keep those controls present when tuning wrappers so scaling behavior stays consistent across the repo.
