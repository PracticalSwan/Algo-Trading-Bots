from datetime import datetime, timedelta, timezone


def utc_day_window(now=None):
    now = now or datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    return day_start, day_start + timedelta(days=1)


def _as_float(value):
    if value is None:
        return 0.0
    return float(value)


def _matches_scope(record, *, symbol, magic):
    return getattr(record, "symbol", None) == symbol and getattr(record, "magic", None) == magic


def calculate_scoped_daily_pnl(deals, positions, *, symbol, magic):
    realized_pnl = 0.0
    for deal in deals or ():
        if _matches_scope(deal, symbol=symbol, magic=magic):
            realized_pnl += _as_float(getattr(deal, "profit", 0.0))
            realized_pnl += _as_float(getattr(deal, "commission", 0.0))
            realized_pnl += _as_float(getattr(deal, "swap", 0.0))
            realized_pnl += _as_float(getattr(deal, "fee", 0.0))

    floating_pnl = 0.0
    for position in positions or ():
        if _matches_scope(position, symbol=symbol, magic=magic):
            floating_pnl += _as_float(getattr(position, "profit", 0.0))
            floating_pnl += _as_float(getattr(position, "swap", 0.0))

    return realized_pnl + floating_pnl


def fetch_scoped_daily_pnl(mt5_module, *, symbol, magic, now=None):
    day_start, day_end = utc_day_window(now)
    deals = mt5_module.history_deals_get(day_start, day_end)
    if deals is None:
        return None

    positions = mt5_module.positions_get()
    if positions is None:
        positions = ()

    return calculate_scoped_daily_pnl(
        deals,
        positions,
        symbol=symbol,
        magic=magic,
    )


def daily_loss_from_pnl(daily_pnl):
    return max(0.0, -float(daily_pnl))
