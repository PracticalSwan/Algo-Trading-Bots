# Exness MT5 Trading Bots

Automated MetaTrader 5 bots for Exness-focused forex grid trading plus one NAS100 grid strategy:

- 6 forex grid wrappers that share `forex_grid_engine.py`
- 1 conservative NAS100 grid bot

The README is intentionally short.
Use it as the front door, then jump into the focused docs for setup,
tuning details, and troubleshooting.

## Bot lineup

| Bot | Template | Symbol | Session (UTC) | Style |
|---|---|---|---|---|
| `eurusd_grid_bot.py` | `eurusd_grid_bot.py.template` | `EURUSDm` | 22:00-08:00 | Grid, Aggressive |
| `gbpusd_grid_bot.py` | `gbpusd_grid_bot.py.template` | `GBPUSDm` | 22:00-08:00 | Grid, Balanced |
| `usdjpy_grid_bot.py` | `usdjpy_grid_bot.py.template` | `USDJPYm` | 22:00-08:00 | Grid, Balanced |
| `audusd_grid_bot.py` | `audusd_grid_bot.py.template` | `AUDUSDm` | 22:00-08:00 | Grid, Conservative |
| `nzdusd_grid_bot.py` | `nzdusd_grid_bot.py.template` | `NZDUSDm` | 22:00-08:00 | Grid, Conservative |
| `usdcad_grid_bot.py` | `usdcad_grid_bot.py.template` | `USDCADm` | 22:00-08:00 | Grid, Balanced |
| `nas100_grid_bot.py` | `nas100_grid_bot.py.template` | `USTECm` | Market hours, Mon-Fri | Grid, Conservative |

## Quick start

1. Install and log into the MT5 desktop terminal.
2. Install Python dependencies:

```powershell
pip install MetaTrader5 pandas numpy
```

3. Copy a template to a local bot file:

```powershell
Copy-Item eurusd_grid_bot.py.template eurusd_grid_bot.py
```

4. Fill in `LOGIN`, `PASSWORD`, `SERVER`, and verify `SYMBOL` matches MT5 exactly.
5. Keep MT5 open, then run the bot:

```powershell
python eurusd_grid_bot.py
```

6. Watch the daily log:

```powershell
Get-Content logs\eurusd_grid_bot_YYYYMMDD.log -Wait -Tail 30
```

Forex grid wrappers will not run without `forex_grid_engine.py` in the same folder.

## What matters most

### Credential workflow

- `*_grid_bot.py.template` files are the tracked source of truth.
- Local `*_grid_bot.py` files contain credentials and are kept out of version control.
- When grid logic changes, update the `.template` file first, then sync the local bot file.
- `forex_grid_engine.py` is tracked directly.

### Shared safety model

All grid bots are tuned for parallel runtime on the same account and share the same account-level guard rails:

- `GLOBAL_MAX_ACCOUNT_POSITIONS = 16`
- `GLOBAL_POSITION_RESERVE_FOR_EXPANSION = 4`
- `GLOBAL_MAX_FLOATING_DRAWDOWN_USD = 8.50`
- `GLOBAL_MIN_FREE_MARGIN_USD = 10.00`
- `GLOBAL_MIN_MARGIN_LEVEL_PCT = 250.0`
- `GLOBAL_SOFT_EQUITY_STOP = 29.00`

New basket starts are throttled once the account reaches `16 - 4 = 12`
open positions, while active baskets can still expand until the hard cap of
`16`.

`DAILY_MAX_LOSS_USD` is now bot-scoped instead of account-equity-scoped. Each bot measures its own current UTC-day P/L from MT5 deal history plus its open basket P/L, so NAS100 losses no longer trip forex daily-loss stops and one forex bot does not consume another bot's daily-loss allowance.

### Current forex profile bands

| Profile | Bots | Lot multiplier | Max lot | Max levels |
|---|---|---|---|---|
| Aggressive | EURUSD | `1.20-1.22` | `0.04-0.05` | `6` |
| Balanced | GBPUSD, USDJPY, USDCAD | `1.08-1.14` | `0.03-0.04` | `5` |
| Conservative | AUDUSD, NZDUSD | `1.00` | `0.015-0.02` | `4` |

NAS100 sits outside those forex bands:

- `nas100_grid_bot.py` is the conservative, news-aware grid variant for `USTECm`.
- Current live tuning is `LOT_MULTIPLIER=1.00`, `MAX_LOT=0.02`, `MAX_LEVELS=4`, `GROWTH_LOT_EXPONENT=0.50`, `GRID_ATR_MULTIPLIER=1.00`, and `MIN_GRID_STEP_PRICE=18.0`.

## Docs map

- [MT5 setup guide](docs/mt5-setup.md) - Exness setup and first-run checklist.
- [Strategy and profiles](docs/strategy-and-profiles.md) - Strategy summary,
  session rationale, and live forex settings.
- [Operations and troubleshooting](docs/operations-and-troubleshooting.md) -
  Daily usage, customization, logs, and common failure modes.
- [CHANGELOG](CHANGELOG.md) - Versioned behavior and tuning history.

## Repo layout

```text
Exness_Bot/
|-- forex_grid_engine.py
|-- *_grid_bot.py.template
|-- *_grid_bot.py
|-- nas100_grid_bot.py.template
|-- nas100_grid_bot.py
|-- docs/
|-- logs/
|-- README.md
|-- CHANGELOG.md
|-- CLAUDE.md
```

## Risk warning

Trading forex and CFDs on margin is high risk.
Test on demo first, keep sizing conservative, and do not run these bots
without understanding the account-wide drawdown controls.
