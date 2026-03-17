# MT5 Setup Guide

This project assumes the Exness MT5 desktop terminal is installed, logged in, and left running while the bot is active.

## Exness-specific notes

- Exness symbols usually include an `m` suffix such as `EURUSDm` or `USTECm`.
- The server string must match MT5 exactly.
- Common server name patterns include `Exness-MT5Trial8`, `Exness-MT5Real8`, and `Exness-MT5Cent8`.

Check the exact server name in MT5 under `Tools -> Options -> Server`.

## 1. Install MetaTrader 5

1. Download MT5 from your broker or from MetaQuotes.
2. Install it and log in with your Exness account.
3. Confirm the symbols you want to trade are visible in Market Watch.

## 2. Enable automated trading

1. Open `Tools -> Options`.
2. Go to the `Expert Advisors` tab.
3. Enable:
   - `Allow automated trading`
   - `Allow DLL imports`
4. Save the changes.

## 3. Verify symbols and permissions

1. Open Market Watch with `Ctrl+M`.
2. Right-click and use `Show All` if needed.
3. Open `Specification` for the symbol and confirm trading is enabled.
4. Copy the symbol name exactly into the bot config.

Examples:

- `EURUSDm`
- `GBPUSDm`
- `USTECm`

## 4. Install Python dependencies

```powershell
pip install MetaTrader5 pandas numpy
```

## 5. Verify Python can reach MT5

Use this quick check before running a bot:

```python
import MetaTrader5 as mt5

if mt5.initialize():
    info = mt5.account_info()
    print(f"Connected to: {info.server}")
    print(f"Account: {info.login}")
    mt5.shutdown()
else:
    print("Connection failed - make sure MT5 is open and logged in")
```

## 6. Create your first local bot file

Copy a tracked template and remove the `.template` suffix:

```powershell
Copy-Item eurusd_grid_bot.py.template eurusd_grid_bot.py
```

Then fill in the config block with your credentials:

```python
LOGIN = YOUR_MT5_ACCOUNT_NUMBER
PASSWORD = "YOUR_MT5_PASSWORD"
SERVER = "Exness-MT5Trial8"
SYMBOL = "EURUSDm"
```

Important:

- Local `*_grid_bot.py` files are for your machine only.
- The tracked templates are the repo source of truth.
- If you later change grid logic, edit the template first and sync the local file after that.

## 7. Run the bot

```powershell
python eurusd_grid_bot.py
```

If you are using a forex grid wrapper, keep `forex_grid_engine.py` in the same directory.

## First-run checklist

- MT5 is open and logged in.
- The server string is exact.
- The symbol name is exact.
- Algorithmic trading is enabled in MT5.
- Python dependencies are installed.
- You are starting on a demo account first.
