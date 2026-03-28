# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Serena Workflow (Required)

When Serena tools are available, always run this sequence for memory preservation and context continuity:

1. Read the Serena skill: `C:/Users/LOQ/.agents/skills/serena-usage/SKILL.md`
2. Verify activation: call `mcp_oraios_serena_get_current_config`
3. If no active project, activate/select `Exness_Bot` first
4. Check onboarding: call `mcp_oraios_serena_check_onboarding_performed`
5. If onboarding is incomplete, run `mcp_oraios_serena_initial_instructions` then `mcp_oraios_serena_onboarding`
6. Persist key decisions/changes to project memory at the end of implementation
7. Update `lessons.md` with concise implementation lessons after completing code changes

## Commands

### Run a bot
```powershell
python eurusd_grid_bot.py
python gbpusd_grid_bot.py
python audusd_grid_bot.py
python nzdusd_grid_bot.py
python usdcad_grid_bot.py
python usdjpy_grid_bot.py
python nas100_grid_bot.py
```

Each bot runs indefinitely in a loop until stopped with `Ctrl+C`, which disconnects the script cleanly from MT5.

### Install dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`pandas` and `numpy` are required by the shared grid engine and NAS100 grid bot.

### Lightweight validation
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

### View live logs
```powershell
Get-Content logs\eurusd_grid_bot_YYYYMMDD.log -Wait -Tail 30
```

---

## Architecture

### Bot Types

**Forex Grid Bots** (6 files: `*_grid_bot.py` for forex pairs):
- Open BUY and SELL hedge orders, then expand grid levels with ATR-adaptive spacing
- Close entire basket when cumulative floating profit reaches `BASKET_TP_USD`
- Some profiles use multiplier-based sizing while conservative profiles use fixed-lot behavior
- Trade Asia session only: 22:00-08:00 UTC, weekdays only
- Pause new starts and expansions outside the Asia session while keeping active baskets managed

**NAS100 Grid Bot** (`nas100_grid_bot.py`):
- Conservative USTEC grid with ATR-adaptive step size, ADX trend filter, and high-impact USD news blackout
- Trades all available market hours on weekdays and now pauses around blackout periods instead of routine forced flattening

### Shared Risk Controls (all bots)

| Parameter | Purpose |
|-----------|---------|
| `DAILY_MAX_LOSS_USD` / `DAILY_MAX_LOSS_PERCENT` | Soft-stop threshold. Forex wrappers can share a combined forex-only UTC-day P/L cap; NAS100 uses its own bot scope |
| `MIN_EQUITY_STOP` | Emergency close-all and shutdown if equity drops below threshold |
| `COOLDOWN_AFTER_CLOSE` | Seconds to wait after basket close before opening new positions |
| `is_trading_allowed()` | Session guard - returns `False` on weekends or outside trading hours |
| `MAGIC` | Unique integer per bot - filters this bot's orders from others |

`GLOBAL_*` guard rails remain account-wide for parallel runtime. The current loss flow uses trim-to-core soft stops for `DAILY_MAX_LOSS_USD`, while full close-all remains reserved for hard safety events, basket TP, incomplete starts, and weekend market closure.

### Grid Bot Logic Flow

1. **Entry**: If no positions exist, open BUY + SELL at current price (grid start)
2. **Grid expansion**: Add new levels only after ATR-adaptive distance thresholds and spread/trend filters pass
3. **Lot sizing**: `FIXED_START_LOT x (LOT_MULTIPLIER ^ level_number)` with symbol-normalization and `MAX_LOT` cap
4. **Exit**: Close all positions when `total_profit >= BASKET_TP_USD`
5. **Safety**: Enforce account-wide parallel guards, equity stops, and session-aware start/expansion pauses

## File Structure

```text
Exness_Bot/
|-- *_grid_bot.py          # Grid bots with credentials (gitignored - local use only)
|-- *_grid_bot.py.template # Grid bot templates WITHOUT credentials (tracked in git)
|-- forex_grid_engine.py   # Shared forex grid execution/risk engine
|-- daily_loss_scope.py    # Shared daily-loss scope and trim-to-core helper logic
|-- nas100_grid_bot.py     # Conservative NAS100 grid bot with news blackout (gitignored)
|-- nas100_grid_bot.py.template # NAS100 grid bot template WITHOUT credentials (tracked)
|-- tests/                 # Lightweight regression tests
|-- .github/               # GitHub templates, workflows, and workspace skill files
|-- requirements.txt       # Runtime dependency manifest
|-- .gitignore             # Excludes grid bots with credentials from version control
|-- lessons.md             # Persistent lessons learned from implementation work
|-- logs/                  # Auto-created, daily rotating logs (gitignored)
|-- CONTRIBUTING.md        # Contributor workflow and local validation
|-- SECURITY.md            # Vulnerability reporting and secret-handling guidance
|-- CLAUDE.md              # This file
|-- README.md              # User documentation
```

### Template Files and Credential Management

**IMPORTANT**: The grid bots with credentials (`*_grid_bot.py`) are excluded from git via `.gitignore`. Only the template files (`*_grid_bot.py.template`) are tracked in version control.

When making changes to any grid bot:
1. **Edit the `.template.py` file first** (this is tracked in git)
2. **Then manually sync the change to the corresponding `*_grid_bot.py`** (local file with credentials)
3. Shared tracked files like `forex_grid_engine.py` can be edited directly

This design allows:
- Sharing bot configurations and code changes via git without exposing credentials
- Each user maintains their own local `*_grid_bot.py` files with their MT5 credentials
- Template files serve as the source of truth for bot configuration and logic

---

## Adding a New Grid Bot

**When adding a new grid bot, you must create BOTH a template file and update the local bot file:**

1. **Create the template file** (tracked in git):
   - Copy an existing `.template.py` file and rename it (e.g., `xauusd_grid_bot.py.template`)
   - Use placeholder credentials: `"LOGIN": YOUR_MT5_ACCOUNT_NUMBER`, `"PASSWORD": "YOUR_MT5_PASSWORD"`
   - Update: `SYMBOL`, `MAGIC` (unique), and tune all parameters for the new instrument
   - Update all log references to match the new instrument name

2. **Create the local bot file** (gitignored, for local use):
   - Copy the template file and remove the `.template` suffix
   - Replace placeholder credentials with actual MT5 credentials
   - Add the new bot filename to `.gitignore`

3. **Parameter tuning**:
   - **CONFIG block**: `SYMBOL`, `MAGIC` (unique), and tune `LOT_MULTIPLIER`, `MAX_LOT`, `MAX_LEVELS`, `BASE_BASKET_TP_USD`, `TP_PER_LEVEL_USD`, `DAILY_MAX_LOSS_USD`, `MIN_EQUITY_STOP`
   - **Adaptive controls**: tune `GRID_ATR_MULTIPLIER`, `MIN_GRID_STEP_PIPS`, `MAX_GRID_STEP_PIPS`, `MAX_SPREAD_PIPS`, `MAX_SPREAD_ATR_RATIO`, `TREND_PAUSE_ADX`
   - **Parallel account safety**: keep global limits aligned with other bots (`GLOBAL_*` keys) so all bots enforce the same account-wide safety gates
   - **Growth adaptation**: keep `AUTO_GROWTH_ENABLED` and `GROWTH_*` keys present so sizing and limits adapt as equity grows

Current profile mapping for forex bots:
- **Aggressive**: EURUSD
- **Balanced**: GBPUSD, USDJPY, USDCAD
- **Conservative**: AUDUSD, NZDUSD

---

## Template Sync Workflow

**CRITICAL**: When making changes to grid bot logic or configuration, ALWAYS follow this order:

1. **Edit the `.template.py` file first** - This is the source of truth tracked in git
2. **Apply the same changes to the local `*_grid_bot.py`** - This preserves your credentials
3. **Never edit the local `*_grid_bot.py` without updating the template** - Changes will be lost on git pull

**Files to sync**:
- `eurusd_grid_bot.py` <-> `eurusd_grid_bot.py.template`
- `gbpusd_grid_bot.py` <-> `gbpusd_grid_bot.py.template`
- `usdjpy_grid_bot.py` <-> `usdjpy_grid_bot.py.template`
- `audusd_grid_bot.py` <-> `audusd_grid_bot.py.template`
- `nzdusd_grid_bot.py` <-> `nzdusd_grid_bot.py.template`
- `usdcad_grid_bot.py` <-> `usdcad_grid_bot.py.template`
- `nas100_grid_bot.py` <-> `nas100_grid_bot.py.template`

**Exception**: `forex_grid_engine.py` is tracked directly (no template needed).

---

## Important Notes

- **Symbol names must match MT5 exactly**: Exness uses suffixed names like `EURUSDm`, `USTECm`
- **Session timing is deliberate**: Forex grids use the range-bound Asia session; NAS100 grid follows market hours and news blackouts
- **Filling mode**: Auto-detected at startup (`ORDER_FILLING_IOC` or `ORDER_FILLING_RETURN`)
- **Console output**: Cleared each loop iteration with `os.system('cls')` - real-time dashboard
- **MT5 API**: Uses `mt5.initialize()`, `mt5.positions_get()`, `mt5.order_send()`, `mt5.shutdown()`
