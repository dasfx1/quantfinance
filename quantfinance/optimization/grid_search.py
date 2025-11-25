from __future__ import annotations

from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from quantfinance.backtesting.engine import BacktestEngine, BacktestResult
from quantfinance.strategies.mean_reversion import MeanReversionParams


def mean_reversion_grid_search(
    price_data: Iterable[Dict[str, float]],
    *,
    z_entries: Sequence[float] = (1.0, 1.5, 2.0),
    sl_distances: Sequence[float] = (1.0, 2.0),
    tp_distances: Sequence[float] = (2.0, 4.0),
    base_params: MeanReversionParams | None = None,
    output_dir: Path | None = None,
    persist_runs: bool = False,
) -> List[BacktestResult]:
    """Grid search helper that stays dependency-free."""

    params_template = base_params or MeanReversionParams()
    engine = BacktestEngine(output_dir=output_dir, persist=persist_runs)
    results: List[BacktestResult] = []

    for z_entry, sl_distance, tp_distance in product(z_entries, sl_distances, tp_distances):
        params = replace(
            params_template,
            z_entry=z_entry,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
        )
        label = f"mr_z{z_entry}_sl{sl_distance}_tp{tp_distance}"
        result = engine.run_mean_reversion(price_data, params, label=label)
        results.append(result)

    results.sort(key=lambda res: res.report.end_capital, reverse=True)

    if output_dir:
        _write_leaderboard(results, Path(output_dir) / "optimization_results.csv")

    return results


def _write_leaderboard(results: Sequence[BacktestResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(results[0].to_row().keys()) if results else []

    with path.open("w", newline="") as handle:
        if not fieldnames:
            handle.write("Keine Ergebnisse vorhanden")
            return
        import csv

        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_row())
