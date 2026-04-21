from src.service.candle_service import get_candles_dataframe
from src.utils.enumeration import Strategy
from src.dto.backtest_dto import BacktestDTO
from src.dto.trade_dto import TradeDTO


def run_backtest(strategy) -> BacktestDTO:
    if strategy == Strategy.PDHL:
        return _run_pdhl()
    if strategy == Strategy.ASRS:
        return _run_asrs()
    if strategy == Strategy.EXPRESSO:
        return _run_expresso()
    raise NotImplementedError(f"Strategy {strategy!r} not implemented")


# ── Shared helpers ────────────────────────────────────────────────────────────

_SKIP_MONTHS = {1, 7, 8}


def _simulate_day(day_bars, sig_high: float, sig_low: float, buffer: float):
    """Simule un jour OCO stop : entre sur le premier niveau touché, sort SL ou EOD."""
    el = sig_high + buffer  # long entry
    es = sig_low  - buffer  # short entry

    direction = entry_price = stop = entry_time = None

    for ts, bar in day_bars.iterrows():
        bh, bl = bar["high"], bar["low"]
        if bh >= el and bl <= es:
            direction    = "LONG" if bar["open"] >= el else "SHORT"
            entry_price  = el if direction == "LONG" else es
            stop         = es if direction == "LONG" else el
            entry_time   = ts
            break
        elif bh >= el:
            direction, entry_price, stop, entry_time = "LONG",  el, es, ts
            break
        elif bl <= es:
            direction, entry_price, stop, entry_time = "SHORT", es, el, ts
            break

    if not direction:
        return None

    exit_price = None
    for _, bar in day_bars[day_bars.index >= entry_time].iterrows():
        if direction == "LONG" and bar["low"] <= stop:
            exit_price = stop
            break
        if direction == "SHORT" and bar["high"] >= stop:
            exit_price = stop
            break

    if exit_price is None:
        exit_price = float(day_bars["close"].iloc[-1])

    pnl = (exit_price - entry_price) if direction == "LONG" else (entry_price - exit_price)
    return {
        "direction":   direction,
        "entry":       round(entry_price, 2),
        "exit":        round(exit_price,  2),
        "stop":        round(stop,        2),
        "pnl":         round(pnl,         2),
    }


def _make_result(strategy: Strategy, trades: list[TradeDTO]) -> BacktestDTO:
    n = len(trades)
    if n == 0:
        return _empty(strategy)
    winners      = [t for t in trades if t.pnl > 0]
    losers       = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in winners)
    gross_loss   = abs(sum(t.pnl for t in losers))
    return BacktestDTO(
        strategy=strategy.value,
        n_trades=n,
        win_rate=round(len(winners) / n, 4),
        profit_factor=round(gross_profit / gross_loss, 4) if gross_loss > 0 else float("inf"),
        total_pnl=round(sum(t.pnl for t in trades), 2),
        trades=trades,
    )


def _empty(strategy: Strategy) -> BacktestDTO:
    return BacktestDTO(
        strategy=strategy.value, n_trades=0,
        win_rate=0.0, profit_factor=0.0, total_pnl=0.0, trades=[],
    )


# ── PDHL ─────────────────────────────────────────────────────────────────────

def _run_pdhl() -> BacktestDTO:
    df = get_candles_dataframe()
    if df.empty:
        return _empty(Strategy.PDHL)

    trades: list[TradeDTO] = []
    dates = sorted(set(df.index.date))

    for i in range(1, len(dates)):
        today, yesterday = dates[i], dates[i - 1]
        if today.month in _SKIP_MONTHS or today.weekday() == 4:
            continue

        prev = df[df.index.date == yesterday]
        curr = df[df.index.date == today]
        if prev.empty or curr.empty:
            continue

        pdh  = prev["high"].max()
        pdl  = prev["low"].min()
        rang = pdh - pdl
        if not (50 <= rang <= 300):
            continue

        entry_long  = pdh + 5
        entry_short = pdl - 5
        stop_long   = pdl
        stop_short  = pdh
        risk_long   = entry_long  - stop_long
        risk_short  = stop_short  - entry_short
        target_long  = entry_long  + risk_long  * 1.5
        target_short = entry_short - risk_short * 1.5

        if curr["high"].max() >= entry_long:
            hit_tp  = curr["high"].max() >= target_long
            exit_p  = target_long if hit_tp else float(curr["close"].iloc[-1])
            trades.append(TradeDTO(
                date=str(today), strategy=Strategy.PDHL.value, direction="LONG",
                entry=round(entry_long, 2), exit=round(exit_p, 2),
                stop=round(stop_long, 2),   pnl=round(exit_p - entry_long, 2),
            ))
        elif curr["low"].min() <= entry_short:
            hit_tp  = curr["low"].min() <= target_short
            exit_p  = target_short if hit_tp else float(curr["close"].iloc[-1])
            trades.append(TradeDTO(
                date=str(today), strategy=Strategy.PDHL.value, direction="SHORT",
                entry=round(entry_short, 2), exit=round(exit_p, 2),
                stop=round(stop_short, 2),   pnl=round(entry_short - exit_p, 2),
            ))

    return _make_result(Strategy.PDHL, trades)


# ── ASRS ─────────────────────────────────────────────────────────────────────

def _run_asrs() -> BacktestDTO:
    df = get_candles_dataframe()  # 09:00–17:35
    if df.empty:
        return _empty(Strategy.ASRS)

    trades: list[TradeDTO] = []
    signal_time = "09:15"

    for day, group in df.groupby(df.index.date):
        if day.month in _SKIP_MONTHS or day.weekday() == 4:
            continue

        sig_bars = group[group.index.strftime("%H:%M") == signal_time]
        if sig_bars.empty:
            continue

        sig      = sig_bars.iloc[0]
        sig_high = sig["high"]
        sig_low  = sig["low"]
        sig_range = sig_high - sig_low

        if not (10 <= sig_range <= 55):
            continue

        # Candles après la bougie signal (à partir de 09:20)
        after_signal = group[group.index > sig_bars.index[0]]
        if after_signal.empty:
            continue

        result = _simulate_day(after_signal, sig_high, sig_low, buffer=2)
        if result is None:
            continue

        trades.append(TradeDTO(
            date=str(day), strategy=Strategy.ASRS.value,
            **result,
        ))

    return _make_result(Strategy.ASRS, trades)


# ── EXPRESSO ──────────────────────────────────────────────────────────────────

def _run_expresso() -> BacktestDTO:
    # Bougie signal 08:55 → besoin de données à partir de 08:45
    df = get_candles_dataframe(start_time="08:45")
    if df.empty:
        return _empty(Strategy.EXPRESSO)

    trades: list[TradeDTO] = []
    signal_time = "08:55"

    for day, group in df.groupby(df.index.date):
        if day.month in _SKIP_MONTHS or day.weekday() == 4:
            continue

        sig_bars = group[group.index.strftime("%H:%M") == signal_time]
        if sig_bars.empty:
            continue

        sig       = sig_bars.iloc[0]
        sig_high  = sig["high"]
        sig_low   = sig["low"]
        sig_range = sig_high - sig_low

        if not (10 <= sig_range <= 55):
            continue

        after_signal = group[group.index > sig_bars.index[0]]
        if after_signal.empty:
            continue

        result = _simulate_day(after_signal, sig_high, sig_low, buffer=17)
        if result is None:
            continue

        trades.append(TradeDTO(
            date=str(day), strategy=Strategy.EXPRESSO.value,
            **result,
        ))

    return _make_result(Strategy.EXPRESSO, trades)
