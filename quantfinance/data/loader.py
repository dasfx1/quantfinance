from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

try:  # pragma: no cover - optional dependency
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    pd = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import yfinance as yf  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yf = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class CSVDataSource:
    """Simple container pointing to a CSV file with OHLCV data."""

    path: Path
    fromdate: datetime
    todate: datetime


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    return DATA_DIR


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


def load_ohlcv(
    ticker: str,
    start: str,
    end: str,
    *,
    prefer_local: bool = True,
) -> Union["pd.DataFrame", CSVDataSource]:
    """Load OHLCV bars from Yahoo Finance or from the local ``data/`` folder."""

    if not prefer_local:
        df = _load_via_yfinance(ticker, start, end)
        if df is not None:
            return df

    csv_path = _fallback_csv_path(ticker)
    return CSVDataSource(path=csv_path, fromdate=_parse_date(start), todate=_parse_date(end))


def is_dataframe(obj: object) -> bool:
    if pd is None:
        return False
    return isinstance(obj, pd.DataFrame)


def load_price_bars(ticker: str, start: str, end: str) -> List[Dict[str, float]]:
    """Return OHLCV records as dictionaries that are easy to feed into the simulators."""

    source = load_ohlcv(ticker, start, end)
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)
    rows: List[Dict[str, float]] = []

    if is_dataframe(source):
        df = source.loc[start:end][["Open", "High", "Low", "Close", "Volume"]]
        for dt, row in df.iterrows():
            rows.append(
                {
                    "datetime": dt.to_pydatetime(),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "Volume": float(row["Volume"]),
                }
            )
    else:
        assert isinstance(source, CSVDataSource)
        with source.path.open("r", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                dt = datetime.strptime(row["datetime"], "%Y-%m-%d")
                if dt < source.fromdate or dt > source.todate:
                    continue
                if dt < start_dt or dt > end_dt:
                    continue
                rows.append(
                    {
                        "datetime": dt,
                        "Open": float(row["Open"]),
                        "High": float(row["High"]),
                        "Low": float(row["Low"]),
                        "Close": float(row["Close"]),
                        "Volume": float(row["Volume"]),
                    }
                )

    if not rows:
        raise ValueError("Keine Preisdaten im angegebenen Zeitraum gefunden.")

    return rows


def load_tick_csv(path: Union[str, Path]) -> List[Dict[str, float]]:
    """Load tick data from a CSV file with columns ``datetime``, ``price`` and ``volume``.

    ``datetime`` must be ISO formatted; ``price`` may be a mid, bid, or ask price.
    If both ``bid`` and ``ask`` columns exist, the mid price is used automatically.
    """

    path = Path(path)
    ticks: List[Dict[str, float]] = []

    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            dt = _parse_date(row["datetime"])
            price: Optional[float] = None
            if "price" in row and row["price"]:
                price = float(row["price"])
            elif "bid" in row and "ask" in row and row["bid"] and row["ask"]:
                price = (float(row["bid"]) + float(row["ask"])) / 2
            if price is None:
                continue
            volume = float(row.get("volume", 0) or 0)
            ticks.append({"datetime": dt, "price": price, "volume": volume})

    if not ticks:
        raise ValueError(f"Keine Tickdaten in {path} gefunden.")

    return ticks


def _parse_interval_seconds(interval: str) -> int:
    match = re.match(r"^(\d+)(s|min|h)$", interval)
    if not match:
        raise ValueError("Intervall muss z.B. '1min', '5min' oder '30s' sein.")
    value, unit = match.groups()
    value_int = int(value)
    if unit == "s":
        return value_int
    if unit == "min":
        return value_int * 60
    return value_int * 3600


def resample_ticks_to_bars(
    ticks: Iterable[Dict[str, float]], interval: str = "1min"
) -> List[Dict[str, float]]:
    """Aggregate raw ticks into OHLCV bars.

    The implementation is dependency-free and therefore works in restricted
    environments. ``interval`` accepts values like ``"30s"`` or ``"5min"``.
    """

    seconds = _parse_interval_seconds(interval)
    buckets: Dict[datetime, Dict[str, float]] = {}

    for tick in sorted(ticks, key=lambda item: item["datetime"]):
        bucket_start = tick["datetime"] - timedelta(
            seconds=tick["datetime"].timestamp() % seconds
        )

        if bucket_start not in buckets:
            buckets[bucket_start] = {
                "datetime": bucket_start,
                "Open": tick["price"],
                "High": tick["price"],
                "Low": tick["price"],
                "Close": tick["price"],
                "Volume": tick.get("volume", 0.0),
            }
            continue

        bucket = buckets[bucket_start]
        price = tick["price"]
        bucket["High"] = max(bucket["High"], price)
        bucket["Low"] = min(bucket["Low"], price)
        bucket["Close"] = price
        bucket["Volume"] += tick.get("volume", 0.0)

    return [bucket for _, bucket in sorted(buckets.items(), key=lambda item: item[0])]
