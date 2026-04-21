"""
=============================================================
  ASRS — Feature Engineering  |  DAX 40 Futures
=============================================================

Construit le dataset features pour la modélisation XGBoost.
Toutes les features sont calculées AVANT 09:15 CET (pas de data leakage).

Usage :
    from features import build_features, download_ext_features, FEATURE_COLS

    ext = download_ext_features()          # télécharge VIX, VSTOXX, EUR/USD, SPX
    df  = build_features(raw, ext=ext)     # raw = DataFrame 5min dax-5m_bk.csv
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd


# ── Features externes (macro/sentiment) ───────────────────────────────────────

EXT_TICKERS = {
    "^VIX":    "vix",
    "^VSTOXX": "vstoxx",
    "EURUSD=X": "eurusd",
    "^GSPC":   "spx",
}

EXT_CACHE_PATH = Path(__file__).parent.parent / "data" / "ext_features.csv"


def download_ext_features(
    start: str = "2005-01-01",
    end:   str = "2027-01-01",
    cache: bool = True,
) -> pd.DataFrame:
    """
    Télécharge VIX, VSTOXX, EUR/USD et S&P 500 via yfinance.
    Met en cache dans data/ext_features.csv pour éviter les re-téléchargements.

    Returns
    -------
    DataFrame journalier indexé par date, colonnes :
        vix_prev, vix_5d_avg, vix_5d_change,
        vstoxx_prev, vstoxx_5d_avg,
        spx_prev_ret, eurusd_prev_ret, eurusd_5d_ret
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance non installé — uv add yfinance")

    if cache and EXT_CACHE_PATH.exists():
        ext = pd.read_csv(EXT_CACHE_PATH, index_col=0, parse_dates=True)
        # Refresh if data is more than 7 days stale
        if (pd.Timestamp.now() - ext.index[-1]).days <= 7:
            return ext

    raw_series = {}
    for ticker, name in EXT_TICKERS.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            close = df["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            close = close.squeeze()
            close.name = name
            close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
            raw_series[name] = close
        except Exception:
            pass  # ticker non disponible (ex: VSTOXX limité selon région)

    if not raw_series:
        raise RuntimeError("Aucune donnée externe téléchargée — vérifiez la connexion réseau")

    base = pd.concat(raw_series.values(), axis=1).sort_index()

    ext = pd.DataFrame(index=base.index)

    if "vix" in base:
        ext["vix_prev"]      = base["vix"].shift(1)
        ext["vix_5d_avg"]    = base["vix"].rolling(5, min_periods=1).mean().shift(1)
        ext["vix_5d_change"] = base["vix"].shift(1) - base["vix"].shift(6)

    if "vstoxx" in base:
        ext["vstoxx_prev"]   = base["vstoxx"].shift(1)
        ext["vstoxx_5d_avg"] = base["vstoxx"].rolling(5, min_periods=1).mean().shift(1)

    if "spx" in base:
        ext["spx_prev_ret"]  = base["spx"].pct_change().shift(1) * 100

    if "eurusd" in base:
        ext["eurusd_prev_ret"] = base["eurusd"].pct_change().shift(1) * 100
        ext["eurusd_5d_ret"]   = base["eurusd"].pct_change(5).shift(1) * 100

    ext = ext.dropna(how="all")

    if cache:
        EXT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        ext.to_csv(EXT_CACHE_PATH)

    return ext


EXT_FEATURE_COLS = [
    "vix_prev",
    "vix_5d_avg",
    "vix_5d_change",
    "vstoxx_prev",
    "vstoxx_5d_avg",
    "spx_prev_ret",
    "eurusd_prev_ret",
    "eurusd_5d_ret",
]


# ── Features techniques (intraday) ────────────────────────────────────────────

def build_features(raw: pd.DataFrame, ext: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Construit le dataset features à partir des données 5min brutes.

    Parameters
    ----------
    raw : DataFrame 5min avec colonnes [open, high, low, close, volume]
          index = datetime CET (sans timezone)
    ext : DataFrame journalier issu de download_ext_features() (optionnel).
          Si fourni, les colonnes macro sont ajoutées.

    Returns
    -------
    DataFrame avec une ligne par jour, indexé par date.
    """
    hm = raw.index.strftime("%H:%M")

    # ── Signal bar (09:15) ─────────────────────────────────────────────────
    sig = raw[hm == "09:15"].copy()
    sig.index = sig.index.normalize()
    sig = sig[~sig.index.duplicated(keep='first')]  # keep first bar per day
    sig_range = (sig["high"] - sig["low"]).replace(0, np.nan)

    df = pd.DataFrame(index=sig.index)
    df["range_signal"]     = (sig["high"] - sig["low"]).values
    df["body_ratio"]       = (abs(sig["close"] - sig["open"]) / sig_range).values
    df["close_position"]   = ((sig["close"] - sig["low"]) / sig_range).values
    df["direction_signal"] = np.where(sig["close"] > sig["open"], 1, -1)

    # ── Pré-session 08:00–09:10 ────────────────────────────────────────────
    pre = raw[(hm >= "08:00") & (hm < "09:15")].copy()
    pre_date = pre.index.normalize()
    pre_open  = pre.groupby(pre_date)["open"].first()
    pre_close = pre.groupby(pre_date)["close"].last()
    pre_high  = pre.groupby(pre_date)["high"].max()
    pre_low   = pre.groupby(pre_date)["low"].min()

    df["presession_move"]  = (pre_close - pre_open).reindex(df.index).values
    df["presession_range"] = (pre_high - pre_low).reindex(df.index).values

    # ── Gap d'ouverture (open 09:00 - close 17:30 de la veille) ───────────
    open_bar  = raw[hm == "09:00"].copy()
    open_bar.index = open_bar.index.normalize()
    close_bar = raw[hm == "17:30"].copy()
    close_bar.index = close_bar.index.normalize()

    prev_close = close_bar["close"].sort_index().shift(1)
    gap = open_bar["open"] - prev_close.reindex(open_bar.index)

    df["opening_gap"]   = gap.reindex(df.index).values
    df["gap_direction"] = np.sign(df["opening_gap"])

    # ── ATR 20 jours ──────────────────────────────────────────────────────
    daily_date  = raw.index.normalize()
    daily_high  = raw.groupby(daily_date)["high"].max()
    daily_low   = raw.groupby(daily_date)["low"].min()
    daily_close = raw.groupby(daily_date)["close"].last()

    prev_close_d = daily_close.shift(1)
    tr = pd.concat([
        daily_high - daily_low,
        (daily_high - prev_close_d).abs(),
        (daily_low  - prev_close_d).abs(),
    ], axis=1).max(axis=1)
    atr_20 = tr.rolling(20, min_periods=5).mean()

    df["atr_20"]       = atr_20.reindex(df.index).values
    df["range_vs_atr"] = df["range_signal"] / df["atr_20"]

    # ── PDH/PDL de la veille ──────────────────────────────────────────────
    session = raw[(hm >= "09:00") & (hm <= "17:35")].copy()
    sess_date = session.index.normalize()
    pdh = session.groupby(sess_date)["high"].max().shift(1)
    pdl = session.groupby(sess_date)["low"].min().shift(1)

    df["pdh_range"]  = (pdh - pdl).reindex(df.index).values
    df["sig_vs_pdh"] = (sig["open"].values - pdh.reindex(df.index).values)
    df["sig_vs_pdl"] = (sig["open"].values - pdl.reindex(df.index).values)

    # ── Calendrier ────────────────────────────────────────────────────────
    dt = pd.to_datetime(df.index)
    df["day_of_week"]   = dt.dayofweek
    df["month"]         = dt.month
    df["week_of_month"] = ((dt.day - 1) // 7 + 1)

    # ── Conditions de filtre comme features binaires ───────────────────────
    # (au lieu de filtrer avant l'entraînement, on laisse XGBoost décider)
    df["is_friday"]    = (dt.dayofweek == 4).astype(int)
    df["is_bad_month"] = dt.month.isin([1, 7, 8]).astype(int)
    df["range_narrow"] = (df["range_signal"] < 10).astype(int)   # range < 10 pts
    df["range_wide"]   = (df["range_signal"] > 55).astype(int)   # range > 55 pts

    # ── Features externes (VIX, VSTOXX, EUR/USD, SPX) ─────────────────────
    if ext is not None:
        ext_aligned = ext.reindex(df.index, method="ffill")
        for col in EXT_FEATURE_COLS:
            if col in ext_aligned.columns:
                df[col] = ext_aligned[col].values

    return df.round(4)


FILTER_FEATURE_COLS = [
    "is_friday",
    "is_bad_month",
    "range_narrow",
    "range_wide",
]

FEATURE_COLS = [
    # Signal bar
    "range_signal",
    "body_ratio",
    "close_position",
    "direction_signal",
    # Pré-session
    "presession_move",
    "presession_range",
    # Gap ouverture
    "opening_gap",
    "gap_direction",
    # Volatilité
    "atr_20",
    "range_vs_atr",
    # Niveaux PDH/PDL
    "pdh_range",
    "sig_vs_pdh",
    "sig_vs_pdl",
    # Calendrier
    "day_of_week",
    "month",
    "week_of_month",
    # Conditions de filtre (apprises par le modèle)
    "is_friday",
    "is_bad_month",
    "range_narrow",
    "range_wide",
]

FEATURE_COLS_EXT = FEATURE_COLS + EXT_FEATURE_COLS

__all__ = [
    "build_features",
    "download_ext_features",
    "FEATURE_COLS",
    "FEATURE_COLS_EXT",
    "FILTER_FEATURE_COLS",
    "EXT_FEATURE_COLS",
]
