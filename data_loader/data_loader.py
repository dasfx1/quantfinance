"""Utilities for providing market data to the Backtrader scripts.

The original implementation relied on :mod:`yfinance` and :mod:`pandas`,
which are not available in the execution environment. To keep the examples
running we fall back to deterministic CSV snapshots stored in ``data/``.

If ``yfinance`` and ``pandas`` are available, the loader will use them to
download fresh data and return a :class:`pandas.DataFrame`. Otherwise a
light-weight :class:`CSVDataSource` is returned which can be consumed by
``bt.feeds.GenericCSVData``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

try:  # pragma: no cover - optional dependency
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed when pandas missing
    pd = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import yfinance as yf  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed when yfinance missing
    yf = None  # type: ignore


DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class CSVDataSource:
    """Path-based fallback representation for OHLCV data."""

    path: Path
    fromdate: datetime
    todate: datetime


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _load_via_yfinance(ticker: str, start: str, end: str):
    if pd is None or yf is None:
        return None

    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
    except Exception:
        return None

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.index.name = "datetime"
    return df


def _fallback_csv_path(ticker: str) -> Path:
    filename = f"{ticker}_2020_2023.csv"
    csv_path = DATA_DIR / filename
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Kein lokaler Datensatz gefunden: {csv_path}. Bitte lege eine CSV-Datei an."
        )
    return csv_path


def get_data(ticker: str, start: str, end: str) -> Union["pd.DataFrame", CSVDataSource]:
    """Return OHLCV data for ``ticker``.

    The preferred return type is a :class:`pandas.DataFrame`. If pandas or
    yfinance are not installed we fall back to :class:`CSVDataSource`.
    """

    df = _load_via_yfinance(ticker, start, end)
    if df is not None:
        return df

    return CSVDataSource(
        path=_fallback_csv_path(ticker),
        fromdate=_parse_date(start),
        todate=_parse_date(end),
    )


def is_dataframe(obj: object) -> bool:
    """Return ``True`` if ``obj`` looks like a pandas DataFrame."""

    if pd is None:
        return False
    return isinstance(obj, pd.DataFrame)


def load_price_bars(ticker: str, start: str, end: str) -> List[Dict[str, float]]:
    """Return OHLCV records as a list of dictionaries.

    Each dictionary contains ``datetime``, ``Open``, ``High``, ``Low``, ``Close``
    and ``Volume`` keys. This helper hides whether the data came from pandas or
    the CSV fallback, making it easier to build lightweight backtests.
    """

    data = get_data(ticker, start, end)
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)

    records: List[Dict[str, float]] = []

    if is_dataframe(data):
        df = data.loc[start:end][["Open", "High", "Low", "Close", "Volume"]]
        for dt, row in df.iterrows():
            records.append({
                "datetime": dt.to_pydatetime(),
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "Volume": float(row["Volume"]),
            })
    else:
        assert isinstance(data, CSVDataSource)
        with data.path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dt = datetime.strptime(row["datetime"], "%Y-%m-%d")
                if dt < data.fromdate or dt > data.todate:
                    continue
                if dt < start_dt or dt > end_dt:
                    continue
                records.append({
                    "datetime": dt,
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "Volume": float(row["Volume"]),
                })

    if not records:
        raise ValueError("Keine Preisdaten im angegebenen Zeitraum gefunden.")

    return records

