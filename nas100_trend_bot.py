import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timezone
import sys
import os

# ====================== WINDOWS CONSOLE FIX ======================
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ========================= CONFIG =========================
LOGIN = 433310708
PASSWORD = "Stampy@199"
SERVER = "Exness-MT5Trial7"
SYMBOL = "USTECm"                    # Official Exness symbol for NAS100
TIMEFRAME = mt5.TIMEFRAME_M15
FIXED_LOT = 0.01
DAILY_MAX_LOSS_PERCENT = 10.0
MAX_DAILY_TRADES = 8
MAX_TOTAL_POSITIONS = 2
GLOBAL_MAX_ACCOUNT_POSITIONS = 16
MAGIC = 20250317
MIN_EQUITY_STOP = 30.0
MAX_SPREAD_POINTS = 300
ADX_THRESHOLD = 28
RSI_BUY = 52
RSI_SELL = 48
TRAILING_ATR_MULTIPLIER = 1.5
BREAKEVEN_ATR = 1.0
TRADING_START_HOUR_UTC = 8
TRADING_END_HOUR_UTC = 17

AUTO_GROWTH_ENABLED = True
GROWTH_BASE_EQUITY = 50.0
GROWTH_MAX_FACTOR = 3.0
GROWTH_LOT_EXPONENT = 0.65
GROWTH_TRADES_EXPONENT = 0.30
GROWTH_POSITIONS_EXPONENT = 0.35
GROWTH_EQUITY_LOCK_RATIO = 0.35
MAX_DYNAMIC_LOT = 0.05

# ====================== LOGGING SETUP ======================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_filename = os.path.join(LOG_DIR, f"nas100_trend_bot_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log")

logger = logging.getLogger("NAS100_TrendBot")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

# Tracks last logged reason to prevent spam on repeated loop iterations
_last_skip_reason = None

def write_log(message, level="info"):
    getattr(logger, level, logger.info)(message)

def log_skip_once(reason):
    """Only log a skip reason once until it changes — prevents spam from cls loop."""
    global _last_skip_reason
    if reason != _last_skip_reason:
        _last_skip_reason = reason
        logger.info(f"SKIP: {reason}")

def log_trade(action, details):
    logger.info(f"TRADE {action} | {details}")

def log_error(message):
    logger.error(message)

SUCCESS_RETCODES = {mt5.TRADE_RETCODE_DONE}
if hasattr(mt5, "TRADE_RETCODE_DONE_PARTIAL"):
    SUCCESS_RETCODES.add(mt5.TRADE_RETCODE_DONE_PARTIAL)

def is_trade_success(result):
    return bool(result and result.retcode in SUCCESS_RETCODES)

def pick_filling_mode(sym_info):
    flags = sym_info.filling_mode if sym_info else 0
    if flags & 2:  # SYMBOL_FILLING_IOC
        return mt5.ORDER_FILLING_IOC
    if flags & 1:  # SYMBOL_FILLING_FOK
        return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN

def lot_digits(step):
    step_str = f"{step:.8f}".rstrip("0")
    if "." not in step_str:
        return 0
    return len(step_str.split(".")[1])

def normalize_lot(raw_lot, sym_info):
    step = sym_info.volume_step if sym_info and sym_info.volume_step > 0 else 0.01
    min_lot = sym_info.volume_min if sym_info else 0.01
    max_lot = sym_info.volume_max if sym_info else raw_lot
    lot = max(min_lot, min(max_lot, raw_lot))
    lot = round(lot / step) * step
    lot = max(min_lot, min(max_lot, lot))
    return round(lot, lot_digits(step))

def growth_factor_from_equity(equity):
    if not AUTO_GROWTH_ENABLED:
        return 1.0
    raw_factor = max(1.0, equity / max(1.0, GROWTH_BASE_EQUITY))
    return min(raw_factor, GROWTH_MAX_FACTOR)

def close_all_positions():
    positions = [p for p in (mt5.positions_get() or ()) if p.magic == MAGIC]
    if not positions:
        return

    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            log_error(f"CLOSE FAILED #{pos.ticket} | No tick data for {pos.symbol}")
            continue

        sym_info = mt5.symbol_info(pos.symbol)
        filling_mode = pick_filling_mode(sym_info)
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": close_price,
            "deviation": 20,
            "magic": MAGIC,
            "comment": "Trend_Close_All",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        result = mt5.order_send(request)
        side = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
        retcode = result.retcode if result else "None"
        comment = result.comment if result else "No result"

        if is_trade_success(result):
            logger.info(f"CLOSE {side} #{pos.ticket} {pos.symbol} | Vol={pos.volume} P/L=${pos.profit:.2f} | retcode={retcode}")
        else:
            log_error(f"CLOSE FAILED {side} #{pos.ticket} {pos.symbol} | Vol={pos.volume} P/L=${pos.profit:.2f} | retcode={retcode} | {comment}")

# ====================== INDICATORS ======================
def get_data(symbol, timeframe, bars=300):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) < 100:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_adx(df, period=14):
    df = df.copy()
    plus_dm = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                       np.maximum(df['high'] - df['high'].shift(1), 0), 0)
    minus_dm = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                        np.maximum(df['low'].shift(1) - df['low'], 0), 0)
    tr = np.maximum.reduce([df['high'] - df['low'],
                            np.abs(df['high'] - df['close'].shift()),
                            np.abs(df['low'] - df['close'].shift())])
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).sum() / pd.Series(tr).rolling(period).sum())
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).sum() / pd.Series(tr).rolling(period).sum())
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return adx

# ====================== POSITION MANAGEMENT ======================
def apply_breakeven_and_trailing():
    positions = mt5.positions_get()
    if positions is None:
        return
    for pos in positions:
        if pos.magic != MAGIC:
            continue
        symbol = pos.symbol
        df = get_data(symbol, TIMEFRAME, 50)
        if df is None or len(df) < 14:
            continue
        atr = calculate_atr(df).iloc[-1]
        profit_atr = (pos.price_current - pos.price_open) / atr if pos.type == mt5.ORDER_TYPE_BUY else (pos.price_open - pos.price_current) / atr

        if pos.type == mt5.ORDER_TYPE_BUY:
            if profit_atr > BREAKEVEN_ATR and pos.sl < pos.price_open + 0.01:
                result = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": symbol, "sl": pos.price_open + 0.01, "tp": pos.tp, "position": pos.ticket})
                logger.info(f"BREAKEVEN BUY #{pos.ticket} | SL moved to {pos.price_open + 0.01:.2f} | result={result.retcode if result else 'None'}")
            new_sl = pos.price_current - TRAILING_ATR_MULTIPLIER * atr
            if new_sl > pos.sl + 0.01:
                result = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": symbol, "sl": new_sl, "tp": pos.tp, "position": pos.ticket})
                logger.info(f"TRAILING BUY #{pos.ticket} | SL trailed to {new_sl:.2f} | result={result.retcode if result else 'None'}")

        elif pos.type == mt5.ORDER_TYPE_SELL:
            if profit_atr > BREAKEVEN_ATR and pos.sl > pos.price_open - 0.01:
                result = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": symbol, "sl": pos.price_open - 0.01, "tp": pos.tp, "position": pos.ticket})
                logger.info(f"BREAKEVEN SELL #{pos.ticket} | SL moved to {pos.price_open - 0.01:.2f} | result={result.retcode if result else 'None'}")
            new_sl = pos.price_current + TRAILING_ATR_MULTIPLIER * atr
            if new_sl < pos.sl - 0.01 or pos.sl == 0:
                result = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": symbol, "sl": new_sl, "tp": pos.tp, "position": pos.ticket})
                logger.info(f"TRAILING SELL #{pos.ticket} | SL trailed to {new_sl:.2f} | result={result.retcode if result else 'None'}")

# ====================== FILTERS ======================
def is_trading_allowed():
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False
    hour = now.hour
    if not (TRADING_START_HOUR_UTC <= hour < TRADING_END_HOUR_UTC):
        return False
    if 12 <= hour <= 13 or 14 <= hour <= 15:   # Skip major US news windows
        return False
    return True

# ====================== MAIN ======================
def main():
    if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
        print("ERROR: MT5 initialize failed!")
        log_error("MT5 initialize failed!")
        return

    if not mt5.symbol_select(SYMBOL, True):
        print(f"ERROR: Symbol {SYMBOL} not found!")
        log_error(f"Symbol {SYMBOL} not found!")
        mt5.shutdown()
        return

    startup_symbol_info = mt5.symbol_info(SYMBOL)
    if startup_symbol_info is None:
        print(f"ERROR: symbol_info({SYMBOL}) returned None")
        log_error(f"symbol_info({SYMBOL}) returned None")
        mt5.shutdown()
        return

    filling_mode = pick_filling_mode(startup_symbol_info)

    write_log("=== NAS100 TREND BOT v1.1 (London-NY + News Filter) STARTED ===")
    print("NAS100 Trend Bot v1.1 RUNNING - Optimized for Profits")

    daily_start_equity = None
    current_day = None
    daily_trades = 0
    peak_equity = GROWTH_BASE_EQUITY

    try:
        while True:
            account = mt5.account_info()
            if not account:
                log_skip_once("No account info from MT5")
                time.sleep(60)
                continue

            balance = account.balance
            equity = account.equity
            now = datetime.now(timezone.utc)
            today = now.date()
            peak_equity = max(peak_equity, equity)

            growth_factor = growth_factor_from_equity(equity)
            dynamic_max_daily_trades = min(
                14,
                max(MAX_DAILY_TRADES, int(round(MAX_DAILY_TRADES * (growth_factor ** GROWTH_TRADES_EXPONENT)))),
            )
            dynamic_max_total_positions = min(
                4,
                max(MAX_TOTAL_POSITIONS, int(round(MAX_TOTAL_POSITIONS * (growth_factor ** GROWTH_POSITIONS_EXPONENT)))),
            )
            dynamic_min_equity_stop = max(
                MIN_EQUITY_STOP,
                MIN_EQUITY_STOP + max(0.0, peak_equity - GROWTH_BASE_EQUITY) * GROWTH_EQUITY_LOCK_RATIO,
            )

            if current_day != today or daily_start_equity is None:
                daily_start_equity = equity
                current_day = today
                daily_trades = 0
                write_log(f"New trading day started. Daily equity baseline: ${daily_start_equity:.2f}")

            all_positions = mt5.positions_get() or ()
            my_positions = [p for p in all_positions if p.magic == MAGIC]
            global_open_count = len(all_positions)
            floating_pnl = sum(p.profit for p in my_positions)
            open_count = len(my_positions)
            day_pnl = round(equity - daily_start_equity - floating_pnl, 2)

            daily_loss = round((daily_start_equity - equity) / daily_start_equity * 100, 1) if daily_start_equity else 0.0

            # === DASHBOARD ===
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 80)
            print(f"   NAS100 TREND BOT v1.1 | London-NY Session | Profit Optimized")
            print(f"   Balance        : ${balance:.2f} USD")
            print(f"   Growth Factor  : x{growth_factor:.2f} | Peak Equity: ${peak_equity:.2f}")
            print(f"   Taken Today    : {daily_trades}/{dynamic_max_daily_trades}")
            print(f"   Daily P/L      : ${day_pnl:+.2f}")
            print(f"   Open Positions : {open_count}/{dynamic_max_total_positions}")
            print(f"   Global Pos     : {global_open_count}/{GLOBAL_MAX_ACCOUNT_POSITIONS}")
            print(f"   Time           : {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print("=" * 80)

            blocked_by_risk = False
            if daily_loss > DAILY_MAX_LOSS_PERCENT:
                print(f"ALERT DAILY MAX LOSS REACHED ({daily_loss}%) - No new trades today!")
                log_skip_once(f"Daily max loss reached ({daily_loss}%)")
                blocked_by_risk = True
            elif equity < dynamic_min_equity_stop:
                print(f"CRITICAL: Equity below ${dynamic_min_equity_stop:.2f} - Stopping bot!")
                log_error(f"Equity below ${dynamic_min_equity_stop:.2f} - Stopping bot!")
                close_all_positions()
                break
            if daily_trades >= dynamic_max_daily_trades:
                print("DAILY TRADE LIMIT REACHED - No more trades today!")
                log_skip_once(f"Daily trade limit reached ({daily_trades}/{dynamic_max_daily_trades})")
                blocked_by_risk = True

            apply_breakeven_and_trailing()

            if blocked_by_risk:
                time.sleep(60)
                continue

            if not is_trading_allowed():
                now_hour = now.hour
                if now.weekday() >= 5:
                    reason = "Weekend - market closed"
                elif 12 <= now_hour <= 13 or 14 <= now_hour <= 15:
                    reason = f"News window (hour={now_hour})"
                else:
                    reason = f"Outside trading hours ({TRADING_START_HOUR_UTC}-{TRADING_END_HOUR_UTC} UTC, current={now_hour})"
                print(f"  {reason} - waiting...")
                log_skip_once(reason)
                time.sleep(60)
                continue

            if open_count >= dynamic_max_total_positions:
                print(f"MAX TOTAL POSITIONS ({dynamic_max_total_positions}) REACHED - waiting...")
                log_skip_once(f"Max positions reached ({open_count}/{dynamic_max_total_positions})")
                time.sleep(60)
                continue

            if global_open_count >= GLOBAL_MAX_ACCOUNT_POSITIONS:
                print(f"GLOBAL POSITION CAP ({global_open_count}/{GLOBAL_MAX_ACCOUNT_POSITIONS}) REACHED - waiting...")
                log_skip_once(f"Global position cap reached ({global_open_count}/{GLOBAL_MAX_ACCOUNT_POSITIONS})")
                time.sleep(60)
                continue

            # === SYMBOL CHECKING ===
            if not mt5.symbol_select(SYMBOL, True):
                log_skip_once(f"Symbol {SYMBOL} not available")
                continue

            df = get_data(SYMBOL, TIMEFRAME, 300)
            if df is None:
                log_skip_once("Insufficient market data from MT5")
                continue

            df['ema9'] = calculate_ema(df['close'], 9)
            df['ema21'] = calculate_ema(df['close'], 21)
            df['rsi'] = calculate_rsi(df['close'])
            df['atr'] = calculate_atr(df)
            df['adx'] = calculate_adx(df)
            df = df.dropna()

            if len(df) < 2:
                log_skip_once("Not enough indicator data after dropna")
                continue

            last = df.iloc[-1]
            prev = df.iloc[-2]

            if pd.isna(last.get('adx')) or pd.isna(last.get('atr')) or last['atr'] < 5:
                log_skip_once(f"Invalid indicators: ADX={last.get('adx')}, ATR={last.get('atr')}")
                continue

            symbol_positions = [p for p in (mt5.positions_get(symbol=SYMBOL) or ()) if p.magic == MAGIC]
            if len(symbol_positions) >= 1:
                log_skip_once(f"Already have {len(symbol_positions)} position(s) open for {SYMBOL}")
                continue

            tick = mt5.symbol_info_tick(SYMBOL)
            symbol_info = mt5.symbol_info(SYMBOL)
            if tick is None or symbol_info is None:
                log_skip_once(f"No tick/symbol info for {SYMBOL}")
                time.sleep(60)
                continue
            if symbol_info.point <= 0:
                log_skip_once(f"Invalid point size for {SYMBOL}: {symbol_info.point}")
                time.sleep(60)
                continue
            spread = (tick.ask - tick.bid) / symbol_info.point
            if spread > MAX_SPREAD_POINTS:
                log_skip_once(f"Spread too wide: {spread:.0f} > {MAX_SPREAD_POINTS} points")
                continue

            adaptive_lot = normalize_lot(min(FIXED_LOT * (growth_factor ** GROWTH_LOT_EXPONENT), MAX_DYNAMIC_LOT), symbol_info)
            if adaptive_lot < symbol_info.volume_min or adaptive_lot > symbol_info.volume_max:
                log_skip_once(f"Lot {adaptive_lot} outside allowed range [{symbol_info.volume_min}, {symbol_info.volume_max}]")
                continue

            # Compare the previous *completed* bar against an average of completed bars.
            # Using last['tick_volume'] is wrong because the current bar is still forming
            # and its partial count is always below the average of finished bars.
            avg_volume = df['tick_volume'].iloc[:-1].rolling(20).mean().iloc[-1]
            if prev['tick_volume'] < 1.2 * avg_volume:
                log_skip_once(f"Low volume: {int(prev['tick_volume'])} < {int(1.2 * avg_volume)} (1.2x avg)")
                time.sleep(60)
                continue

            if daily_trades >= dynamic_max_daily_trades:
                log_skip_once(f"Daily trade limit reached ({daily_trades}/{dynamic_max_daily_trades})")
                continue

            # Log current indicator snapshot for context
            logger.debug(f"INDICATORS | EMA9={last['ema9']:.2f} EMA21={last['ema21']:.2f} RSI={last['rsi']:.1f} ADX={last['adx']:.1f} ATR={last['atr']:.1f} Spread={spread:.0f}")

            # ENTRY CONDITIONS
            ema_cross_up = prev['ema9'] < prev['ema21'] and last['ema9'] > last['ema21']
            ema_cross_down = prev['ema9'] > prev['ema21'] and last['ema9'] < last['ema21']

            if ema_cross_up and last['rsi'] > RSI_BUY and last['adx'] > ADX_THRESHOLD:
                sl = last['close'] - 1.5 * last['atr']
                tp = last['close'] + 4.5 * last['atr']
                request = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": adaptive_lot,
                           "type": mt5.ORDER_TYPE_BUY, "price": tick.ask,
                           "sl": sl, "tp": tp, "deviation": 20, "magic": MAGIC,
                           "comment": "NAS100_TrendBot", "type_time": mt5.ORDER_TIME_GTC,
                           "type_filling": filling_mode}
                result = mt5.order_send(request)
                if is_trade_success(result):
                    log_trade("BUY", f"NAS100 @ {tick.ask:.2f} | SL={sl:.2f} TP={tp:.2f} | Lot={adaptive_lot} | growth=x{growth_factor:.2f}")
                    print(f"TRADE BUY NAS100 | Lot {adaptive_lot}")
                    daily_trades += 1
                else:
                    comment = result.comment if result else "No result"
                    retcode = result.retcode if result else "N/A"
                    log_error(f"BUY FAILED | retcode={retcode} | {comment}")

            elif ema_cross_down and last['rsi'] < RSI_SELL and last['adx'] > ADX_THRESHOLD:
                sl = last['close'] + 1.5 * last['atr']
                tp = last['close'] - 4.5 * last['atr']
                request = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": adaptive_lot,
                           "type": mt5.ORDER_TYPE_SELL, "price": tick.bid,
                           "sl": sl, "tp": tp, "deviation": 20, "magic": MAGIC,
                           "comment": "NAS100_TrendBot", "type_time": mt5.ORDER_TIME_GTC,
                           "type_filling": filling_mode}
                result = mt5.order_send(request)
                if is_trade_success(result):
                    log_trade("SELL", f"NAS100 @ {tick.bid:.2f} | SL={sl:.2f} TP={tp:.2f} | Lot={adaptive_lot} | growth=x{growth_factor:.2f}")
                    print(f"TRADE SELL NAS100 | Lot {adaptive_lot}")
                    daily_trades += 1
                else:
                    comment = result.comment if result else "No result"
                    retcode = result.retcode if result else "N/A"
                    log_error(f"SELL FAILED | retcode={retcode} | {comment}")
            else:
                # Log why no entry was taken (only on state change)
                reasons = []
                if not ema_cross_up and not ema_cross_down:
                    reasons.append("No EMA crossover")
                elif ema_cross_up:
                    if last['rsi'] <= RSI_BUY:
                        reasons.append(f"RSI too low for BUY: {last['rsi']:.1f} <= {RSI_BUY}")
                    if last['adx'] <= ADX_THRESHOLD:
                        reasons.append(f"ADX too low: {last['adx']:.1f} <= {ADX_THRESHOLD}")
                elif ema_cross_down:
                    if last['rsi'] >= RSI_SELL:
                        reasons.append(f"RSI too high for SELL: {last['rsi']:.1f} >= {RSI_SELL}")
                    if last['adx'] <= ADX_THRESHOLD:
                        reasons.append(f"ADX too low: {last['adx']:.1f} <= {ADX_THRESHOLD}")
                log_skip_once(f"No entry signal: {'; '.join(reasons)}")

            print("\nWaiting for next check (60 seconds)...")
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected - closing all bot positions")
        close_all_positions()
        write_log("Bot stopped by user")
        print("\nBot stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()