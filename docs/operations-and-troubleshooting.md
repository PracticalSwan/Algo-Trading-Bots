# Operations And Troubleshooting

## Daily operations

### Run a bot

```powershell
python eurusd_grid_bot.py
python nas100_grid_bot.py
```

Bots run continuously until interrupted. `Ctrl+C` is intended to shut them down safely.

### Run multiple bots

Open separate terminals for each bot you want to run:

```powershell
python eurusd_grid_bot.py
python gbpusd_grid_bot.py
python usdjpy_grid_bot.py
```

Parallel runtime safety depends on the shared `GLOBAL_*` guard rails staying aligned across bots.

### Watch logs

Each bot writes a daily log file under `logs/`.

```powershell
Get-Content logs\eurusd_grid_bot_YYYYMMDD.log -Wait -Tail 30
```

The `logs/` folder is created automatically if it does not exist.

## Repo file roles

| Path pattern | Purpose |
|---|---|
| `*_grid_bot.py.template` | Tracked templates without credentials |
| `*_grid_bot.py` | Local grid bot files with credentials |
| `forex_grid_engine.py` | Shared execution and risk engine for all forex grid wrappers |
| `nas100_grid_bot.py.template` | Tracked NAS100 grid template |
| `logs/` | Daily runtime logs |

## Template workflow

When changing a grid bot:

1. Edit the `.template` file first.
2. Sync the same logic into the local `*_grid_bot.py`.
3. Do not treat the local credential-bearing file as the source of truth.

## Common parameters

### Shared parameters

| Parameter | Meaning |
|---|---|
| `LOGIN`, `PASSWORD`, `SERVER` | MT5 credentials and broker server |
| `SYMBOL` | Instrument name exactly as shown in MT5 |
| `MAGIC` | Unique identifier for that bot's orders |
| `FIXED_START_LOT` | First order lot size |
| `DAILY_MAX_LOSS_USD` | Bot-scoped daily stop threshold based on that bot's current UTC-day realized P/L plus open basket P/L |
| `MIN_EQUITY_STOP` | Emergency equity floor |
| `CHECK_INTERVAL` | Loop delay in seconds |
| `COOLDOWN_AFTER_CLOSE` | Cooldown after basket close |

`GLOBAL_*` parameters still protect the whole account. `DAILY_MAX_LOSS_USD` now applies only to the bot identified by the current `SYMBOL` and `MAGIC`.

### Grid-specific parameters

| Parameter group | Meaning |
|---|---|
| `LOT_MULTIPLIER`, `MAX_LOT`, `MAX_LEVELS` | Core exposure profile |
| `BASE_BASKET_TP_USD`, `TP_PER_LEVEL_USD` | Basket profit model |
| `GRID_ATR_MULTIPLIER`, `MIN_GRID_STEP_PIPS`, `MAX_GRID_STEP_PIPS` | Adaptive grid spacing |
| `TREND_PAUSE_ADX` | Trend-strength guard for expansion |
| `MAX_SPREAD_PIPS`, `MAX_SPREAD_ATR_RATIO` | Entry quality filters |
| `GLOBAL_*` safety keys | Account-wide parallel runtime protection |
| `AUTO_GROWTH_ENABLED`, `GROWTH_*` | Equity-based scaling controls |

### NAS100 grid extras

| Parameter group | Meaning |
|---|---|
| `MIN_GRID_STEP_PRICE`, `MAX_GRID_STEP_PRICE` | Grid spacing bounds in index price units |
| `NEWS_COUNTRIES`, `NEWS_IMPACTS` | Event filter scope |
| `NEWS_BLOCK_BEFORE_MIN`, `NEWS_BLOCK_AFTER_MIN` | Event blackout window |
| `CLOSE_BEFORE_NEWS` | Flatten positions around blocked events |

## Environment variables for credentials

If you do not want credentials hardcoded in a local bot file, load them from the shell:

```python
import os

LOGIN = int(os.environ["MT5_LOGIN"])
PASSWORD = os.environ["MT5_PASSWORD"]
SERVER = os.environ["MT5_SERVER"]
```

```powershell
$env:MT5_LOGIN = "123456789"
$env:MT5_PASSWORD = "YourPassword"
$env:MT5_SERVER = "Exness-MT5Real8"
python eurusd_grid_bot.py
```

## Adding a new grid bot

1. Copy an existing template such as `eurusd_grid_bot.py.template`.
2. Rename it for the new symbol, for example `xauusd_grid_bot.py.template`.
3. Update `SYMBOL`, `MAGIC`, log naming, and tuning values.
4. Add the local `xauusd_grid_bot.py` to `.gitignore`.
5. Create the local runtime file by copying the template and inserting credentials.
6. Keep the shared `GLOBAL_*` safety keys aligned with the rest of the repo.

## MT5 integration notes

- Closing positions should bind to the exact MT5 ticket with `position=pos.ticket`.
- Filling mode should follow the symbol-supported options such as `IOC`, `FOK`, or `RETURN`.
- `positions_get` should be used to verify close behavior and scope orders correctly.
- The news blackout flow expects the ForexFactory weekly XML structure used by this repo.

## Troubleshooting

### `ImportError: No module named 'forex_grid_engine'`

Cause:

- The shared forex engine is missing from the same directory.

Fix:

- Keep `forex_grid_engine.py` beside the forex grid wrapper files.

### `ModuleNotFoundError: No module named 'MetaTrader5'`

Cause:

- Python dependencies are not installed in the environment you are using.

Fix:

```powershell
pip install MetaTrader5 pandas numpy
```

### MT5 initialization fails

Typical causes:

- MT5 is closed
- MT5 is open but not logged in
- `LOGIN`, `PASSWORD`, or `SERVER` is incorrect

Fix:

1. Open MT5 and log in.
2. Re-check the server string in MT5.
3. Confirm the bot config matches exactly.

### Symbol not found or trades are rejected

Typical causes:

- The symbol name is wrong.
- The symbol is hidden in Market Watch.
- The instrument is not tradable for that account.

Fix:

1. Use `Show All` in Market Watch.
2. Copy the symbol name exactly, including the `m` suffix when present.
3. Check the symbol specification in MT5.

### Bot is inside trading hours but still not opening trades

Typical causes:

- Daily loss stop reached
- Equity stop reached
- Spread filter blocking entry
- ADX trend filter blocking entry
- Global position cap reached

Fix:

- Read the live log first. The reason is usually written there explicitly.
