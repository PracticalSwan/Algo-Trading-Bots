# Exness MT5 Trading Bots

Automated MetaTrader 5 bots for Exness-focused grid trading, built around a shared forex grid engine plus one conservative NAS100 grid variant.

This repository is intentionally application-first rather than package-first. It is designed for running and maintaining MT5 bot scripts, not for publishing a Python library.

## Risk warning

Trading forex and CFDs on margin is high risk.

- Test on demo first.
- Keep sizing conservative.
- Do not run these bots without understanding the account-wide drawdown controls.
- Never commit live MT5 credentials or account-specific local bot files.

## Bot lineup

| Bot | Tracked template | Symbol | Session (UTC) | Style |
| --- | --- | --- | --- | --- |
| `eurusd_grid_bot.py` | `eurusd_grid_bot.py.template` | `EURUSDm` | 22:00-08:00 | Grid, Aggressive |
| `gbpusd_grid_bot.py` | `gbpusd_grid_bot.py.template` | `GBPUSDm` | 22:00-08:00 | Grid, Balanced |
| `usdjpy_grid_bot.py` | `usdjpy_grid_bot.py.template` | `USDJPYm` | 22:00-08:00 | Grid, Balanced |
| `audusd_grid_bot.py` | `audusd_grid_bot.py.template` | `AUDUSDm` | 22:00-08:00 | Grid, Conservative |
| `nzdusd_grid_bot.py` | `nzdusd_grid_bot.py.template` | `NZDUSDm` | 22:00-08:00 | Grid, Conservative |
| `usdcad_grid_bot.py` | `usdcad_grid_bot.py.template` | `USDCADm` | 22:00-08:00 | Grid, Balanced |
| `nas100_grid_bot.py` | `nas100_grid_bot.py.template` | `USTECm` | Market hours, Mon-Fri | Grid, Conservative |

## What the repo contains

- `forex_grid_engine.py`: shared execution, adaptive spacing, and safety logic for the six forex wrappers
- `*_grid_bot.py.template`: tracked bot templates with placeholder credentials
- local `*_grid_bot.py` files: credential-bearing runtime copies for your machine only
- `daily_loss_scope.py`: helper logic for daily loss scoping and trim-to-core behavior
- `tests/test_daily_loss_scope.py`: regression coverage for daily-loss helper behavior

## Quick start

1. Install MetaTrader 5 and log in with your Exness account.
2. Install Python dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Create a local bot file from a tracked template:

```powershell
Copy-Item usdjpy_grid_bot.py.template usdjpy_grid_bot.py
```

4. Fill in `LOGIN`, `PASSWORD`, and `SERVER`, then verify `SYMBOL` matches MT5 exactly.
5. Keep MT5 open and logged in, then run the bot:

```powershell
python usdjpy_grid_bot.py
```

6. Watch the runtime log:

```powershell
Get-Content logs\usdjpy_grid_bot_YYYYMMDD.log -Wait -Tail 30
```

For forex wrappers, keep `forex_grid_engine.py` in the same folder as the bot wrapper.

## Credential workflow

Tracked source of truth:
- `*_grid_bot.py.template`
- `nas100_grid_bot.py.template`
- shared tracked files such as `forex_grid_engine.py`

Local-only runtime files:
- `*_grid_bot.py`
- `nas100_grid_bot.py`

Rules:
- Edit the template file first when changing wrapper logic or config.
- Sync the same change into your local credential-bearing copy afterward.
- Do not commit live credentials, account IDs, or secret-bearing local bot files.

## Shared safety model

All grid bots are tuned for parallel runtime on the same account and share the same account-level guard rails:

- `GLOBAL_MAX_ACCOUNT_POSITIONS = 16`
- `GLOBAL_POSITION_RESERVE_FOR_EXPANSION = 4`
- `GLOBAL_MAX_FLOATING_DRAWDOWN_USD = 8.50`
- `GLOBAL_MIN_FREE_MARGIN_USD = 10.00`
- `GLOBAL_MIN_MARGIN_LEVEL_PCT = 250.0`
- `GLOBAL_SOFT_EQUITY_STOP = 29.00`

New basket starts are throttled once the account reaches `16 - 4 = 12` open positions, while active baskets may still expand until the hard cap of `16`.

The six forex wrappers share one combined forex-only UTC-day `DAILY_MAX_LOSS_USD = 3.00` budget. NAS100 keeps its own tighter `DAILY_MAX_LOSS_USD = 2.60` scope.

When that soft loss limit is hit, the bots now trim newer expansion legs back to the oldest hedge/core pair and freeze new starts or expansions until the next UTC day instead of flattening the whole basket.

Manual `Ctrl+C` stops the script loop and disconnects from MT5. It is not documented as a force-close shortcut for all positions.

## Current forex profile ranges

| Profile | Bots | Lot multiplier | Max lot | Max levels |
| --- | --- | --- | --- | --- |
| Aggressive | EURUSD | `1.20-1.22` | `0.04-0.05` | `6` |
| Balanced | GBPUSD, USDJPY, USDCAD | `1.08-1.14` | `0.03-0.04` | `5` |
| Conservative | AUDUSD, NZDUSD | `1.00` | `0.015-0.02` | `4` |

NAS100 sits outside those forex bands with conservative `USTECm` tuning:

- `LOT_MULTIPLIER = 1.00`
- `MAX_LOT = 0.02`
- `MAX_LEVELS = 4`
- `GROWTH_LOT_EXPONENT = 0.50`
- `GRID_ATR_MULTIPLIER = 1.00`
- `MIN_GRID_STEP_PRICE = 18.0`

## Development and verification

This repo includes a lightweight Windows GitHub Actions workflow that checks syntax/compile health and runs `tests/test_daily_loss_scope.py`.

You can run the same validation locally:

```powershell
@'
import py_compile

files = [
    "daily_loss_scope.py",
    "forex_grid_engine.py",
    "eurusd_grid_bot.py.template",
    "gbpusd_grid_bot.py.template",
    "usdjpy_grid_bot.py.template",
    "audusd_grid_bot.py.template",
    "nzdusd_grid_bot.py.template",
    "usdcad_grid_bot.py.template",
    "nas100_grid_bot.py.template",
    "tests/test_daily_loss_scope.py",
]

for path in files:
    py_compile.compile(path, doraise=True)

print(f"Compiled {len(files)} files successfully")
'@ | python -

python -m unittest tests.test_daily_loss_scope -v
```

## Docs map

- [MT5 setup guide](docs/mt5-setup.md)
- [Strategy and profiles](docs/strategy-and-profiles.md)
- [Operations and troubleshooting](docs/operations-and-troubleshooting.md)
- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE)

## Repo layout

```text
Exness_Bot/
|-- forex_grid_engine.py
|-- daily_loss_scope.py
|-- *_grid_bot.py.template
|-- nas100_grid_bot.py.template
|-- docs/
|-- tests/
|-- .github/
|-- requirements.txt
|-- README.md
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- LICENSE
```
