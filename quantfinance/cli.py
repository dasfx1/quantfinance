from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from quantfinance.backtesting.engine import BacktestEngine
from quantfinance.data.loader import load_price_bars, load_tick_csv, resample_ticks_to_bars
from quantfinance.mt5.export import export_mean_reversion_ea, load_best_params_from_csv
from quantfinance.optimization.grid_search import mean_reversion_grid_search
from quantfinance.strategies.mean_reversion import MeanReversionParams


def _add_common_strategy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--period", type=int, default=20, help="Lookback-Periode für den Z-Score")
    parser.add_argument("--z-entry", type=float, default=1.5, help="Z-Score für Einstieg")
    parser.add_argument("--z-exit", type=float, default=0.5, help="Z-Score für Ausstieg")
    parser.add_argument("--sl-distance", type=float, default=2.0, help="Stop-Loss-Distanz in Preis-Einheiten")
    parser.add_argument("--tp-distance", type=float, default=4.0, help="Take-Profit-Distanz in Preis-Einheiten")
    parser.add_argument("--stake", type=int, default=10, help="Positionsgröße")
    parser.add_argument("--initial-cash", type=float, default=10_000.0, help="Startkapital")


def _params_from_args(args: argparse.Namespace) -> MeanReversionParams:
    return MeanReversionParams(
        period=args.period,
        z_entry=args.z_entry,
        z_exit=args.z_exit,
        sl_distance=args.sl_distance,
        tp_distance=args.tp_distance,
        stake=args.stake,
        initial_cash=args.initial_cash,
    )


def _load_price_data(args: argparse.Namespace) -> List[dict]:
    if args.tick_file:
        ticks = load_tick_csv(args.tick_file)
        return resample_ticks_to_bars(ticks, args.tick_interval)
    return load_price_bars(args.ticker, args.start, args.end)


def backtest_command(args: argparse.Namespace) -> None:
    params = _params_from_args(args)
    engine = BacktestEngine()
    price_data = _load_price_data(args)
    result = engine.run_mean_reversion(price_data, params, label=args.label)

    print("\nBacktest fertig. Wichtigste Kennzahlen:")
    for key, value in result.report.as_row().items():
        print(f"- {key}: {value}")

    print(f"\nErgebnisse gespeichert unter: {engine.output_dir}")


def optimize_command(args: argparse.Namespace) -> None:
    params = _params_from_args(args)
    price_data = _load_price_data(args)

    results = mean_reversion_grid_search(
        price_data,
        z_entries=args.z_entries,
        sl_distances=args.sl_distances,
        tp_distances=args.tp_distances,
        base_params=params,
        output_dir=Path("reports/optimization"),
        persist_runs=args.persist_runs,
    )

    best = results[0]
    print("\nBeste Parameterkombination:")
    print(best.to_row())
    print("\nVollständige Tabelle: reports/optimization/optimization_results.csv")


def export_mt5_command(args: argparse.Namespace) -> None:
    params = _params_from_args(args)

    if args.optimization_csv:
        loaded = load_best_params_from_csv(Path(args.optimization_csv))
        if loaded:
            params = loaded
            print("Parameter aus Optimierungsdatei geladen.")

    output_path = export_mean_reversion_ea(params, output_dir=Path("dist"))
    print(f"EA-Template gespeichert unter: {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kompaktes Toolkit für Backtests und Optimierung")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backtest = subparsers.add_parser("backtest", help="Einzelnen Backtest ausführen")
    backtest.add_argument("--ticker", type=str, default="AAPL", help="Ticker für OHLCV-Daten")
    backtest.add_argument("--start", type=str, default="2020-01-01", help="Startdatum (YYYY-MM-DD)")
    backtest.add_argument("--end", type=str, default="2023-01-01", help="Enddatum (YYYY-MM-DD)")
    backtest.add_argument("--tick-file", type=str, help="Pfad zu Tickdaten (CSV)")
    backtest.add_argument("--tick-interval", type=str, default="1min", help="Intervall für Tick-Aggregation")
    backtest.add_argument("--label", type=str, default="manual_run", help="Dateinamenspräfix für Reports")
    _add_common_strategy_args(backtest)
    backtest.set_defaults(func=backtest_command)

    optimize = subparsers.add_parser("optimize", help="Grid-Suche über Parameterräume")
    optimize.add_argument("--ticker", type=str, default="AAPL")
    optimize.add_argument("--start", type=str, default="2020-01-01")
    optimize.add_argument("--end", type=str, default="2023-01-01")
    optimize.add_argument("--tick-file", type=str)
    optimize.add_argument("--tick-interval", type=str, default="1min")
    optimize.add_argument("--z-entries", type=float, nargs="+", default=[1.0, 1.5, 2.0])
    optimize.add_argument("--sl-distances", type=float, nargs="+", default=[1.0, 2.0])
    optimize.add_argument("--tp-distances", type=float, nargs="+", default=[2.0, 4.0])
    optimize.add_argument("--persist-runs", action="store_true", help="Jeden Backtest als Datei sichern")
    _add_common_strategy_args(optimize)
    optimize.set_defaults(func=optimize_command)

    export_parser = subparsers.add_parser(
        "export-mt5", help="Exportiere eine Strategiekonfiguration als MQL5-Template"
    )
    export_parser.add_argument("--optimization-csv", type=str, help="Nutze die beste Reihe aus der CSV")
    _add_common_strategy_args(export_parser)
    export_parser.set_defaults(func=export_mt5_command)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
