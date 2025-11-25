from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from quantfinance.strategies.mean_reversion import (
    MeanReversionParams,
    MeanReversionReport,
    simulate_mean_reversion,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class BacktestResult:
    strategy: str
    params: MeanReversionParams
    report: MeanReversionReport

    def to_row(self) -> Dict[str, object]:
        row = {
            "strategy": self.strategy,
            **asdict(self.params),
            **self.report.as_row(),
        }
        return row


class BacktestEngine:
    """Minimal backtesting runner for deterministic, dependency-free simulations."""

    def __init__(self, output_dir: Optional[Path] = None, persist: bool = True) -> None:
        self.output_dir = output_dir or (PROJECT_ROOT / "reports" / "backtests")
        self.persist = persist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_mean_reversion(
        self, price_data: Iterable[Dict[str, float]], params: MeanReversionParams, label: Optional[str] = None
    ) -> BacktestResult:
        label = label or datetime.now().strftime("%Y%m%d_%H%M%S")
        report = simulate_mean_reversion(price_data, params)
        result = BacktestResult(strategy="mean_reversion", params=params, report=report)

        if self.persist:
            self._write_backtest_files(result, label)

        return result

    def _write_backtest_files(self, result: BacktestResult, label: str) -> None:
        summary_path = self.output_dir / f"{label}_summary.csv"
        equity_path = self.output_dir / f"{label}_equity_curve.csv"
        markdown_path = self.output_dir / f"{label}_README.md"

        with summary_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(result.to_row().keys()))
            writer.writeheader()
            writer.writerow(result.to_row())

        with equity_path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["index", "equity"])
            for idx, value in enumerate(result.report.equity_curve):
                writer.writerow([idx, value])

        markdown_path.write_text(
            "\n".join(
                [
                    "# Backtest-Zusammenfassung",
                    "",
                    f"**Strategie:** {result.strategy}",
                    f"**Parameter:** {result.params}",
                    "",
                    "**Kennzahlen**:",
                    f"- Endkapital: {result.report.end_capital}",
                    f"- Trades: {result.report.total_trades} (Winrate {result.report.winrate:.2f}%)",
                    f"- Max. Drawdown: {result.report.drawdown_percent:.2f}%",
                    "",
                    f"CSV: {summary_path.name}",
                    f"Equity Curve: {equity_path.name}",
                ]
            )
        )


__all__ = ["BacktestEngine", "BacktestResult", "MeanReversionParams", "MeanReversionReport"]
