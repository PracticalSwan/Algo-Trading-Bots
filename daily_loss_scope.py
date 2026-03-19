from datetime import datetime, timedelta, timezone

FOREX_GROUP_MEMBERS = {
    ("EURUSDm", 20250311),
    ("USDJPYm", 20250312),
    ("AUDUSDm", 20250313),
    ("GBPUSDm", 20250314),
    ("NZDUSDm", 20250315),
    ("USDCADm", 20250316),
}


def utc_day_window(now=None):
    now = now or datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    return day_start, day_start + timedelta(days=1)


def _as_float(value):
    if value is None:
        return 0.0
    return float(value)


def _record_key(record):
    return getattr(record, "symbol", None), getattr(record, "magic", None)


def _matches_scope(record, *, symbol=None, magic=None, members=None):
    if members is not None:
        return _record_key(record) in members
    return getattr(record, "symbol", None) == symbol and getattr(record, "magic", None) == magic


def calculate_scoped_daily_pnl(deals, positions, *, symbol=None, magic=None, members=None):
    realized_pnl = 0.0
    for deal in deals or ():
        if _matches_scope(deal, symbol=symbol, magic=magic, members=members):
            realized_pnl += _as_float(getattr(deal, "profit", 0.0))
            realized_pnl += _as_float(getattr(deal, "commission", 0.0))
            realized_pnl += _as_float(getattr(deal, "swap", 0.0))
            realized_pnl += _as_float(getattr(deal, "fee", 0.0))

    floating_pnl = 0.0
    for position in positions or ():
        if _matches_scope(position, symbol=symbol, magic=magic, members=members):
            floating_pnl += _as_float(getattr(position, "profit", 0.0))
            floating_pnl += _as_float(getattr(position, "swap", 0.0))

    return realized_pnl + floating_pnl


def fetch_scoped_daily_pnl(mt5_module, *, symbol=None, magic=None, members=None, now=None):
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
        members=members,
    )


def daily_loss_from_pnl(daily_pnl):
    return max(0.0, -float(daily_pnl))


def select_trim_positions(positions):
    if not positions or len(positions) <= 2:
        return []

    positions = list(positions)
    grouped = {}
    for position in positions:
        grouped.setdefault(getattr(position, "type", None), []).append(position)

    keep_tickets = set()
    for same_side_positions in grouped.values():
        oldest_position = min(
            same_side_positions,
            key=lambda pos: (getattr(pos, "time", 0), getattr(pos, "ticket", 0)),
        )
        keep_tickets.add(getattr(oldest_position, "ticket", None))

    trim_positions = [
        position for position in positions
        if getattr(position, "ticket", None) not in keep_tickets
    ]
    trim_positions.sort(
        key=lambda pos: (getattr(pos, "time", 0), getattr(pos, "ticket", 0)),
        reverse=True,
    )
    return trim_positions
