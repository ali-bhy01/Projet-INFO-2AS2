import pandas as pd
from pathlib import Path

from src.utils.enumeration import Strategy
from src.dao import candle_dao
from src.dto.trade_dto import TradeDTO
from src.dto.backtest_dto import BacktestDTO

ROOT = Path(__file__).resolve().parents[2]

SKIP_DOW    = [4]
SKIP_MONTHS = [1, 7, 8]
BUFFER      = 5
RANGE_MIN   = 50
RANGE_MAX   = 300


def _load_csv() -> pd.DataFrame:
    path = ROOT / "data" / "dax_live_5min.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert("Europe/Berlin").tz_localize(None)
    df = df[~df.index.duplicated()].sort_index()
    return df.between_time("09:00", "17:35")


def _simulate_pdhl(day_bars: pd.DataFrame, sig_high: float, sig_low: float) -> dict | None:
    if day_bars.empty:
        return None
    el = sig_high + BUFFER
    es = sig_low  - BUFFER
    direction = entry_price = entry_time = stop = None

    for ts, bar in day_bars.iterrows():
        if direction:
            break
        bh, bl = bar["high"], bar["low"]
        if bh >= el and bl <= es:
            direction, entry_price, stop = ("long", el, es) if bar["open"] >= el else ("short", es, el)
        elif bh >= el:
            direction, entry_price, stop = "long",  el, es
        elif bl <= es:
            direction, entry_price, stop = "short", es, el
        if direction:
            entry_time = ts

    if not direction:
        return None

    exit_price = None
    for ts, bar in day_bars[day_bars.index >= entry_time].iterrows():
        if direction == "long":
            if bar["low"] <= stop:
                exit_price = stop
                break
        else:
            if bar["high"] >= stop:
                exit_price = stop
                break

    if exit_price is None:
        exit_price = day_bars[day_bars.index >= entry_time].iloc[-1]["close"]

    pnl = (exit_price - entry_price) if direction == "long" else (entry_price - exit_price)
    return {
        "direction": direction,
        "entry":     round(entry_price, 1),
        "exit":      round(exit_price, 1),
        "stop":      round(stop, 1),
        "pnl":       round(pnl, 2),
    }


def run_pdhl() -> BacktestDTO:
    df = _load_csv()
    dates = sorted(set(df.index.date))
    trades: list[TradeDTO] = []

    for i, d in enumerate(dates):
        if i == 0:
            continue
        ts = pd.Timestamp(d)
        if ts.dayofweek in SKIP_DOW or ts.month in SKIP_MONTHS:
            continue
        prev = dates[i - 1]
        prev_b = df.loc[str(prev)]
        if len(prev_b) < 2:
            continue
        sh = prev_b["high"].max()
        sl = prev_b["low"].min()
        if not (RANGE_MIN <= sh - sl <= RANGE_MAX):
            continue
        day_b = df.loc[str(d)]
        if len(day_b) < 2:
            continue
        r = _simulate_pdhl(day_b, sh, sl)
        if r:
            trades.append(TradeDTO(
                date=str(d),
                strategy=Strategy.PDHL,
                direction=r["direction"],
                entry=r["entry"],
                exit=r["exit"],
                stop=r["stop"],
                pnl=r["pnl"],
            ))

    if not trades:
        return BacktestDTO(strategy=Strategy.PDHL, n_trades=0, win_rate=0, profit_factor=0, total_pnl=0, trades=[])

    pnls = [t.pnl for t in trades]
    wins   = sum(p for p in pnls if p > 0)
    losses = abs(sum(p for p in pnls if p < 0))
    return BacktestDTO(
        strategy=Strategy.PDHL,
        n_trades=len(trades),
        win_rate=round(sum(1 for p in pnls if p > 0) / len(pnls), 4),
        profit_factor=round(wins / losses, 4) if losses else float("inf"),
        total_pnl=round(sum(pnls), 2),
        trades=trades,
    )


_RUNNERS = {
    Strategy.PDHL: run_pdhl,
}


def run_backtest(strategy: Strategy) -> BacktestDTO:
    runner = _RUNNERS.get(strategy)
    if runner is None:
        raise NotImplementedError(f"Stratégie {strategy} non implémentée")
    return runner()
