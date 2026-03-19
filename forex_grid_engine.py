import MetaTrader5 as mt5
import time
import logging
from datetime import datetime, timezone
import os

import pandas as pd
import numpy as np

from daily_loss_scope import FOREX_GROUP_MEMBERS, daily_loss_from_pnl, fetch_scoped_daily_pnl, select_trim_positions

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


def get_data(symbol, timeframe, bars):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) < 40:
        return None
    return pd.DataFrame(rates)


def calculate_atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_adx(df, period=14):
    plus_dm = np.where(
        (df["high"] - df["high"].shift(1)) > (df["low"].shift(1) - df["low"]),
        np.maximum(df["high"] - df["high"].shift(1), 0),
        0,
    )
    minus_dm = np.where(
        (df["low"].shift(1) - df["low"]) > (df["high"] - df["high"].shift(1)),
        np.maximum(df["low"].shift(1) - df["low"], 0),
        0,
    )
    tr = np.maximum.reduce(
        [
            df["high"] - df["low"],
            np.abs(df["high"] - df["close"].shift()),
            np.abs(df["low"] - df["close"].shift()),
        ]
    )
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).sum() / pd.Series(tr).rolling(period).sum())
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).sum() / pd.Series(tr).rolling(period).sum())
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    return dx.rolling(period).mean()


def dynamic_basket_tp(base_tp, step_tp, position_count):
    levels = max(1, position_count // 2)
    return base_tp + max(0, levels - 1) * step_tp


def run_forex_grid_bot(config):
    login = config["LOGIN"]
    password = config["PASSWORD"]
    server = config["SERVER"]
    symbol = config["SYMBOL"]
    magic = config["MAGIC"]

    fixed_start_lot = config["FIXED_START_LOT"]
    lot_multiplier = config["LOT_MULTIPLIER"]
    max_lot = config["MAX_LOT"]
    max_levels = config["MAX_LEVELS"]

    base_basket_tp_usd = config["BASE_BASKET_TP_USD"]
    tp_per_level_usd = config["TP_PER_LEVEL_USD"]
    daily_max_loss_usd = config["DAILY_MAX_LOSS_USD"]
    min_equity_stop = config["MIN_EQUITY_STOP"]
    check_interval = config["CHECK_INTERVAL"]
    cooldown_after_close = config["COOLDOWN_AFTER_CLOSE"]

    atr_timeframe = config["ATR_TIMEFRAME"]
    atr_period = config["ATR_PERIOD"]
    atr_bars = config["ATR_BARS"]
    grid_atr_multiplier = config["GRID_ATR_MULTIPLIER"]
    min_grid_step_pips = config["MIN_GRID_STEP_PIPS"]
    max_grid_step_pips = config["MAX_GRID_STEP_PIPS"]

    max_spread_pips = config["MAX_SPREAD_PIPS"]
    max_spread_atr_ratio = config["MAX_SPREAD_ATR_RATIO"]

    trend_timeframe = config["TREND_TIMEFRAME"]
    trend_bars = config["TREND_BARS"]
    trend_pause_adx = config["TREND_PAUSE_ADX"]

    global_max_account_positions = config["GLOBAL_MAX_ACCOUNT_POSITIONS"]
    global_max_floating_dd = config["GLOBAL_MAX_FLOATING_DRAWDOWN_USD"]
    global_min_free_margin = config["GLOBAL_MIN_FREE_MARGIN_USD"]
    global_min_margin_level = config["GLOBAL_MIN_MARGIN_LEVEL_PCT"]
    global_soft_equity_stop = config["GLOBAL_SOFT_EQUITY_STOP"]
    global_cooldown_after_safety = config["GLOBAL_COOLDOWN_AFTER_SAFETY"]
    global_position_reserve_for_expansion = max(0, int(config.get("GLOBAL_POSITION_RESERVE_FOR_EXPANSION", 0)))
    if global_position_reserve_for_expansion >= global_max_account_positions:
        global_position_reserve_for_expansion = max(0, global_max_account_positions - 1)
    global_start_entry_cap = max(1, global_max_account_positions - global_position_reserve_for_expansion)

    auto_growth_enabled = config.get("AUTO_GROWTH_ENABLED", True)
    growth_base_equity = max(1.0, float(config.get("GROWTH_BASE_EQUITY", 50.0)))
    growth_max_factor = max(1.0, float(config.get("GROWTH_MAX_FACTOR", 3.0)))
    growth_lot_exponent = float(config.get("GROWTH_LOT_EXPONENT", 0.70))
    growth_tp_exponent = float(config.get("GROWTH_TP_EXPONENT", 0.85))
    growth_risk_exponent = float(config.get("GROWTH_RISK_EXPONENT", 0.60))
    growth_equity_lock_ratio = min(1.0, max(0.0, float(config.get("GROWTH_EQUITY_LOCK_RATIO", 0.35))))

    bot_title = config["BOT_TITLE"]
    log_prefix = config["LOG_PREFIX"]
    logger_name = config["LOGGER_NAME"]
    start_buy_comment = config["START_BUY_COMMENT"]
    start_sell_comment = config["START_SELL_COMMENT"]
    grid_buy_comment = config["GRID_BUY_COMMENT"]
    grid_sell_comment = config["GRID_SELL_COMMENT"]
    price_digits = config["PRICE_DIGITS"]
    daily_loss_scope = config.get("DAILY_LOSS_SCOPE", "BOT")
    daily_loss_scope_members = FOREX_GROUP_MEMBERS if daily_loss_scope == "FOREX_GROUP" else None
    daily_loss_scope_label = "Forex group" if daily_loss_scope_members is not None else "Bot"

    def is_weekend(now):
        return now.weekday() >= 5

    def is_entry_session_open(now):
        hour = now.hour
        return 22 <= hour or hour < 8

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"{log_prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log")

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    last_skip_reason = None
    filling_mode = mt5.ORDER_FILLING_RETURN

    def write_log(message, level="info"):
        getattr(logger, level, logger.info)(message)

    def log_skip_once(reason):
        nonlocal last_skip_reason
        if reason != last_skip_reason:
            last_skip_reason = reason
            logger.info(f"SKIP: {reason}")

    def log_trade(action, details):
        logger.info(f"TRADE {action} | {details}")

    def log_error(message):
        logger.error(message)

    def send_market_order(order_type, volume, price, comment):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 25,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        return mt5.order_send(request)

    def growth_factor_from_equity(equity):
        if not auto_growth_enabled:
            return 1.0
        raw_factor = max(1.0, equity / growth_base_equity)
        return min(raw_factor, growth_max_factor)

    def get_account_free_margin(account):
        # MT5 account_info fields can vary by bridge/version (`free_margin` vs `margin_free`).
        free_margin = getattr(account, "free_margin", None)
        if free_margin is None:
            free_margin = getattr(account, "margin_free", None)
        return float(free_margin) if free_margin is not None else None

    def close_positions(positions, reason=""):
        closed = 0
        for pos in positions:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                log_error(f"CLOSE FAILED #{pos.ticket} | No tick data for {symbol}")
                continue

            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": close_price,
                "deviation": 25,
                "magic": magic,
                "comment": "Close_All" if not reason else f"Close_{reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
            result = mt5.order_send(request)
            side = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
            retcode = result.retcode if result else "None"
            comment = result.comment if result else "No result"

            if is_trade_success(result):
                closed += 1
                logger.info(
                    f"CLOSE {side} #{pos.ticket} | Vol={pos.volume} P/L=${pos.profit:.2f} | retcode={retcode} | reason={reason}"
                )
            else:
                log_error(
                    f"CLOSE FAILED {side} #{pos.ticket} | Vol={pos.volume} P/L=${pos.profit:.2f} | retcode={retcode} | {comment}"
                )

        return closed

    def close_all_positions(reason=""):
        positions = [p for p in (mt5.positions_get(symbol=symbol) or ()) if p.magic == magic]
        if not positions:
            return 0
        return close_positions(positions, reason=reason)

    def trim_positions_to_core(reason=""):
        positions = [p for p in (mt5.positions_get(symbol=symbol) or ()) if p.magic == magic]
        trim_positions = select_trim_positions(positions)
        if not trim_positions:
            return 0
        # Trim newest expansion legs first and keep the oldest hedge pair alive for recovery.
        return close_positions(trim_positions, reason=reason)

    if not mt5.initialize(login=login, password=password, server=server):
        log_error("MT5 initialize failed!")
        return

    if not mt5.symbol_select(symbol, True):
        log_error(f"Symbol {symbol} not found!")
        mt5.shutdown()
        return

    sym_info = mt5.symbol_info(symbol)
    if sym_info is None:
        log_error(f"symbol_info({symbol}) returned None")
        mt5.shutdown()
        return

    filling_mode = pick_filling_mode(sym_info)

    write_log(f"=== {bot_title} STARTED ===")
    print(f"{bot_title} RUNNING")

    last_close_time = 0.0
    peak_equity = growth_base_equity
    soft_stop_day = None

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()
        if soft_stop_day is not None and soft_stop_day != today:
            soft_stop_day = None

        if is_weekend(now):
            my_positions = [p for p in (mt5.positions_get(symbol=symbol) or ()) if p.magic == magic]
            if my_positions:
                logger.info(f"WEEKEND SAFETY: Closing {len(my_positions)} positions")
                close_all_positions(reason="WEEKEND")
                last_close_time = time.time()
            log_skip_once("Weekend - forex market closed")
            time.sleep(300)
            continue
        session_open = is_entry_session_open(now)

        account = mt5.account_info()
        if not account:
            log_skip_once("No account info from MT5")
            time.sleep(check_interval)
            continue

        balance = account.balance
        equity = account.equity
        free_margin = get_account_free_margin(account)
        if free_margin is None:
            log_skip_once("Account free margin unavailable (free_margin/margin_free)")
            time.sleep(check_interval)
            continue
        peak_equity = max(peak_equity, equity)

        growth_factor = growth_factor_from_equity(equity)
        lot_scale = growth_factor ** growth_lot_exponent
        tp_scale = growth_factor ** growth_tp_exponent
        risk_scale = growth_factor ** growth_risk_exponent

        adaptive_start_lot = fixed_start_lot * lot_scale
        adaptive_max_lot = max_lot * lot_scale
        adaptive_base_basket_tp = base_basket_tp_usd * tp_scale
        adaptive_tp_per_level = tp_per_level_usd * tp_scale
        adaptive_daily_max_loss = daily_max_loss_usd * risk_scale
        adaptive_global_floating_dd = global_max_floating_dd * risk_scale
        adaptive_global_min_free_margin = global_min_free_margin * (1 + 0.25 * (growth_factor - 1))
        adaptive_min_equity_stop = max(
            min_equity_stop,
            min_equity_stop + max(0.0, peak_equity - growth_base_equity) * growth_equity_lock_ratio,
        )
        adaptive_global_soft_equity_stop = max(
            global_soft_equity_stop,
            global_soft_equity_stop + max(0.0, peak_equity - growth_base_equity) * growth_equity_lock_ratio,
        )

        scoped_daily_pnl = fetch_scoped_daily_pnl(
            mt5,
            symbol=symbol if daily_loss_scope_members is None else None,
            magic=magic if daily_loss_scope_members is None else None,
            members=daily_loss_scope_members,
            now=now,
        )
        if scoped_daily_pnl is None:
            log_skip_once("MT5 deal history unavailable for bot-scoped daily loss")
            time.sleep(check_interval)
            continue
        daily_loss = daily_loss_from_pnl(scoped_daily_pnl)

        all_positions = mt5.positions_get() or ()
        global_open_count = len(all_positions)
        global_floating = sum(p.profit for p in all_positions)

        my_positions = [p for p in all_positions if p.symbol == symbol and p.magic == magic]
        total_profit = sum(p.profit for p in my_positions)
        soft_stop_active = soft_stop_day == today

        margin_level = account.margin_level if account.margin_level and account.margin_level > 0 else None

        # In parallel mode, all bots must respect account-wide risk first.
        severe_safety_reason = None
        if equity <= adaptive_global_soft_equity_stop:
            severe_safety_reason = f"Global equity stop reached (${equity:.2f} <= ${adaptive_global_soft_equity_stop:.2f})"
        elif global_floating <= -adaptive_global_floating_dd:
            severe_safety_reason = f"Global floating DD exceeded (${global_floating:.2f} <= -${adaptive_global_floating_dd:.2f})"
        elif free_margin <= adaptive_global_min_free_margin:
            severe_safety_reason = f"Free margin too low (${free_margin:.2f} <= ${adaptive_global_min_free_margin:.2f})"
        elif margin_level is not None and margin_level <= global_min_margin_level:
            severe_safety_reason = f"Margin level too low ({margin_level:.1f}% <= {global_min_margin_level:.1f}%)"

        if severe_safety_reason:
            if my_positions:
                logger.info(f"GLOBAL SAFETY: Closing {len(my_positions)} positions | {severe_safety_reason}")
                close_all_positions(reason="GLOBAL_SAFETY")
                last_close_time = time.time()
            log_skip_once(severe_safety_reason)
            time.sleep(global_cooldown_after_safety)
            continue

        if equity < adaptive_min_equity_stop:
            log_error(f"Equity ${equity:.2f} below ${adaptive_min_equity_stop:.2f} - Emergency stop!")
            close_all_positions(reason="EQUITY_STOP")
            print("BOT STOPPED - EQUITY PROTECTION")
            break

        if daily_loss >= adaptive_daily_max_loss and not soft_stop_active:
            trimmed = trim_positions_to_core(reason="DAILY_LOSS_TRIM")
            soft_stop_day = today
            soft_stop_active = True
            if trimmed:
                last_close_time = time.time()
                logger.info(
                    f"DAILY LOSS SOFT STOP: Trimmed {trimmed} expansion positions | "
                    f"{daily_loss_scope_label} daily loss ${daily_loss:.2f} >= ${adaptive_daily_max_loss:.2f}"
                )
            else:
                logger.info(
                    f"DAILY LOSS SOFT STOP: No expansion legs to trim | "
                    f"{daily_loss_scope_label} daily loss ${daily_loss:.2f} >= ${adaptive_daily_max_loss:.2f}"
                )
            all_positions = mt5.positions_get() or ()
            global_open_count = len(all_positions)
            global_floating = sum(p.profit for p in all_positions)
            my_positions = [p for p in all_positions if p.symbol == symbol and p.magic == magic]
            total_profit = sum(p.profit for p in my_positions)

        cooldown_active = time.time() - last_close_time < cooldown_after_close

        vol_df = get_data(symbol, atr_timeframe, atr_bars)
        trend_df = get_data(symbol, trend_timeframe, trend_bars)
        if vol_df is None or trend_df is None:
            log_skip_once("Insufficient bars for ATR/ADX metrics")
            time.sleep(check_interval)
            continue

        atr_series = calculate_atr(vol_df, atr_period)
        adx_series = calculate_adx(trend_df, atr_period)
        atr = float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else None
        adx = float(adx_series.iloc[-1]) if not pd.isna(adx_series.iloc[-1]) else None
        if atr is None or atr <= 0 or adx is None:
            log_skip_once(f"Invalid ATR/ADX values | ATR={atr} ADX={adx}")
            time.sleep(check_interval)
            continue

        sym_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if sym_info is None or tick is None:
            log_skip_once(f"No symbol or tick info for {symbol}")
            time.sleep(check_interval)
            continue

        pip_value = sym_info.point * 10
        if pip_value <= 0:
            log_skip_once(f"Invalid pip value for {symbol}")
            time.sleep(check_interval)
            continue

        spread_price = tick.ask - tick.bid
        spread_pips = spread_price / pip_value
        atr_pips = atr / pip_value

        max_allowed_spread = max(max_spread_pips, atr_pips * max_spread_atr_ratio)
        if spread_pips > max_allowed_spread:
            log_skip_once(
                f"Spread too wide: {spread_pips:.2f} pips > {max_allowed_spread:.2f} pips (ATR={atr_pips:.2f})"
            )
            time.sleep(check_interval)
            continue

        tp_target = dynamic_basket_tp(adaptive_base_basket_tp, adaptive_tp_per_level, len(my_positions))
        if my_positions and total_profit >= tp_target:
            logger.info(
                f"BASKET TP HIT | P/L=${total_profit:.2f} >= ${tp_target:.2f} | Closing {len(my_positions)} positions"
            )
            close_all_positions(reason="BASKET_TP")
            print(f"BASKET PROFIT ${total_profit:.2f} - Grid reset")
            last_close_time = time.time()
            time.sleep(5)
            continue

        start_entries_blocked = global_open_count >= global_start_entry_cap
        expansion_entries_blocked = global_open_count >= global_max_account_positions
        entry_pause_reason = None
        if soft_stop_active:
            entry_pause_reason = f"{daily_loss_scope_label} daily loss lock active until next UTC day"
        elif not session_open:
            entry_pause_reason = "Outside Asia session - managing existing basket only"

        if not my_positions:
            if entry_pause_reason:
                log_skip_once(entry_pause_reason)
                time.sleep(check_interval)
                continue

            if cooldown_active:
                log_skip_once(f"Cooldown active ({cooldown_after_close}s after last close)")
                time.sleep(check_interval)
                continue

            if start_entries_blocked:
                log_skip_once(
                    f"Global start cap reached ({global_open_count}/{global_start_entry_cap}, reserve={global_position_reserve_for_expansion})"
                )
                time.sleep(check_interval)
                continue

            if adx >= trend_pause_adx:
                log_skip_once(f"Trend too strong to start grid | ADX={adx:.1f} >= {trend_pause_adx}")
                time.sleep(check_interval)
                continue

            start_lot = normalize_lot(min(adaptive_start_lot, adaptive_max_lot), sym_info)
            logger.info(
                f"GRID START | Opening BUY @ {tick.ask:.{price_digits}f} + SELL @ {tick.bid:.{price_digits}f} | "
                f"Lot={start_lot} | ATR={atr_pips:.2f} pips ADX={adx:.1f} | growth=x{growth_factor:.2f}"
            )

            result_buy = send_market_order(mt5.ORDER_TYPE_BUY, start_lot, tick.ask, start_buy_comment)
            if is_trade_success(result_buy):
                log_trade(
                    "BUY",
                    f"Grid start @ {tick.ask:.{price_digits}f} | Lot={start_lot} | retcode={result_buy.retcode}",
                )
            else:
                retcode = result_buy.retcode if result_buy else "None"
                comment = result_buy.comment if result_buy else "No result"
                log_error(f"Grid start BUY failed | retcode={retcode} | {comment}")
            time.sleep(1)

            result_sell = send_market_order(mt5.ORDER_TYPE_SELL, start_lot, tick.bid, start_sell_comment)
            if is_trade_success(result_sell):
                log_trade(
                    "SELL",
                    f"Grid start @ {tick.bid:.{price_digits}f} | Lot={start_lot} | retcode={result_sell.retcode}",
                )
            else:
                retcode = result_sell.retcode if result_sell else "None"
                comment = result_sell.comment if result_sell else "No result"
                log_error(f"Grid start SELL failed | retcode={retcode} | {comment}")
            time.sleep(1)

            my_positions = [p for p in (mt5.positions_get(symbol=symbol) or ()) if p.magic == magic]
            if len(my_positions) == 2:
                logger.info("Grid initialized successfully with BUY + SELL")
                print("New grid started successfully!")
            else:
                log_error(f"Grid incomplete: expected 2 positions, got {len(my_positions)} - retrying")
                close_all_positions(reason="INCOMPLETE_START")
                print("Initial grid incomplete - retrying...")

        else:
            prices = [p.price_open for p in my_positions]
            avg_price = sum(prices) / len(prices)
            current_price = (tick.ask + tick.bid) / 2
            distance_pips = abs(current_price - avg_price) / pip_value

            levels_now = max(1, len(my_positions) // 2)
            step_pips = max(min_grid_step_pips, min(max_grid_step_pips, atr_pips * grid_atr_multiplier))
            needed_distance = step_pips * levels_now

            if entry_pause_reason:
                log_skip_once(entry_pause_reason)
            elif cooldown_active:
                log_skip_once(f"Cooldown active ({cooldown_after_close}s after last close)")
            elif adx >= trend_pause_adx:
                log_skip_once(f"Trend too strong for expansion | ADX={adx:.1f} >= {trend_pause_adx}")
            elif expansion_entries_blocked:
                log_skip_once(
                    f"Global hard cap reached ({global_open_count}/{global_max_account_positions})"
                )
            elif distance_pips >= needed_distance and len(my_positions) < max_levels * 2:
                raw_lot = adaptive_start_lot * (lot_multiplier ** levels_now)
                level_lot = normalize_lot(min(raw_lot, adaptive_max_lot), sym_info)

                if current_price < avg_price:
                    result = send_market_order(mt5.ORDER_TYPE_BUY, level_lot, tick.ask, grid_buy_comment)
                    if is_trade_success(result):
                        log_trade(
                            "BUY",
                            f"Grid level {levels_now + 1} | Lot={level_lot} | dist={distance_pips:.2f} pips | "
                            f"step={step_pips:.2f} | retcode={result.retcode}",
                        )
                    else:
                        retcode = result.retcode if result else "None"
                        comment = result.comment if result else "No result"
                        log_error(f"Grid BUY level failed | Lvl={levels_now + 1} | retcode={retcode} | {comment}")
                else:
                    result = send_market_order(mt5.ORDER_TYPE_SELL, level_lot, tick.bid, grid_sell_comment)
                    if is_trade_success(result):
                        log_trade(
                            "SELL",
                            f"Grid level {levels_now + 1} | Lot={level_lot} | dist={distance_pips:.2f} pips | "
                            f"step={step_pips:.2f} | retcode={result.retcode}",
                        )
                    else:
                        retcode = result.retcode if result else "None"
                        comment = result.comment if result else "No result"
                        log_error(f"Grid SELL level failed | Lvl={levels_now + 1} | retcode={retcode} | {comment}")
            else:
                log_skip_once(
                    f"Grid waiting | {len(my_positions)} pos | dist={distance_pips:.2f}/{needed_distance:.2f} pips needed"
                )

        os.system("cls")
        print("=" * 95)
        print(f"   {bot_title}")
        print(f"   Balance     : ${balance:.2f} | Equity: ${equity:.2f}")
        print(f"   Growth      : x{growth_factor:.2f} | Peak Equity: ${peak_equity:.2f}")
        print(f"   My Positions: {len(my_positions)} / {max_levels * 2}")
        print(f"   Global Pos  : {global_open_count} / {global_max_account_positions}")
        print(f"   Start Cap   : {global_start_entry_cap} (reserve {global_position_reserve_for_expansion})")
        print(f"   Basket P/L  : ${total_profit:.2f} (TP at +${tp_target:.2f})")
        print(
            f"   Global Float: ${global_floating:.2f} | {daily_loss_scope_label} Day P/L: ${scoped_daily_pnl:.2f} | "
            f"Daily Loss: ${daily_loss:.2f} / ${adaptive_daily_max_loss:.2f}"
        )
        print(f"   Start/MaxLot: {adaptive_start_lot:.3f}/{adaptive_max_lot:.3f}")
        print(f"   ATR(M5)     : {atr_pips:.2f} pips | ADX(M15): {adx:.1f}")
        print(f"   Spread      : {spread_pips:.2f} pips | Max allowed: {max_allowed_spread:.2f}")
        print(f"   Free Margin : ${free_margin:.2f} | Margin Level: {margin_level if margin_level is not None else 0:.1f}%")
        session_label = "Asia Session" if session_open else "Outside Asia Session - Core Management Only"
        print(f"   Time        : {now.strftime('%Y-%m-%d %H:%M:%S')} UTC ({session_label})")
        print("=" * 95)

        time.sleep(check_interval)

    mt5.shutdown()
