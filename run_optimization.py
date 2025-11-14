
import csv
import os
from itertools import product
from typing import Dict, Iterable, List, Sequence

from data_loader import get_data, is_dataframe, load_price_bars
from mean_reversion import MeanReversion, MeanReversionParams, run_mean_reversion

try:
    import backtrader as bt
except ModuleNotFoundError:
    bt = None


def _format_table(rows: Sequence[Dict[str, object]]) -> None:
    headers = list(rows[0].keys())
    widths = {
        header: max([len(header)] + [len(str(row[header])) for row in rows])
        for header in headers
    }

    def format_row(row: Dict[str, object]) -> str:
        return " | ".join(str(row[h]).rjust(widths[h]) for h in headers)

    header_line = format_row({h: h for h in headers})
    separator = "-+-".join("-" * widths[h] for h in headers)

    print(header_line)
    print(separator)
    for row in rows:
        print(format_row(row))


def _write_csv(rows: Sequence[Dict[str, object]]) -> None:
    headers = list(rows[0].keys())

    # Pfad zum Projektordner (wo dieses Skript liegt)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "results")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "optimization_results.csv")

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _optimise_with_backtrader() -> List[Dict[str, object]]:
    if bt is None or MeanReversion is None:
        return []

    data = get_data("AAPL", "2020-01-01", "2023-01-01")
    if not is_dataframe(data):
        return []

    cerebro = bt.Cerebro(maxcpus=1)
    cerebro.adddata(bt.feeds.PandasData(dataname=data))
    cerebro.optstrategy(
        MeanReversion,
        z_entry=[1.0, 1.25, 1.5, 1.75, 2.0],
        sl_distance=[1.0, 2.0],
        tp_distance=[2.0, 4.0],
    )

    cerebro.broker.setcash(10_000)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    results = cerebro.run()

    rows: List[Dict[str, object]] = []
    for result in results:
        strat = result[0]
        if not isinstance(strat, bt.Strategy):
            continue

        params = strat.params

        try:
            trades = strat.analyzers.trades.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()

            total_trades = getattr(trades.total, "closed", 0) or 0
            wins = getattr(trades.won, "total", 0) or 0
            winrate = (wins / total_trades * 100) if total_trades else 0.0

            dd_max = getattr(drawdown, "max", None)
            dd_percent = getattr(dd_max, "drawdown", 0.0) if dd_max else 0.0

            final_value = strat.broker.getvalue()

            rows.append(
                {
                    "z_entry": params.z_entry,
                    "sl_distance": params.sl_distance,
                    "tp_distance": params.tp_distance,
                    "total_trades": total_trades,
                    "winrate": round(winrate, 2),
                    "drawdown_%": round(dd_percent, 2),
                    "end_capital": round(final_value, 2),
                }
            )
        except Exception as exc:
            print(
                f"⚠️ Fehler bei Parametern: z={params.z_entry}, "
                f"sl={params.sl_distance}, tp={params.tp_distance}"
            )
            print(str(exc))

    return rows


def _optimise_with_python(price_data: Iterable[Dict[str, float]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for z_entry, sl_distance, tp_distance in product(
        [1.0, 1.5, 2.0], [1.0, 2.0], [2.0, 4.0]
    ):
        params = MeanReversionParams(
            z_entry=z_entry,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
        )

        try:
            stats = run_mean_reversion(price_data, params)
            rows.append(
                {
                    "z_entry": z_entry,
                    "sl_distance": sl_distance,
                    "tp_distance": tp_distance,
                    "total_trades": stats["total_trades"],
                    "winrate": stats["winrate"],
                    "drawdown_%": stats["drawdown_%"],
                    "end_capital": stats["end_capital"],
                }
            )
        except Exception as exc:
            print(
                f"⚠️ Fehler bei Parametern: z={z_entry}, "
                f"sl={sl_distance}, tp={tp_distance}"
            )
            print(str(exc))

    return rows


def main() -> None:
    rows: List[Dict[str, object]] = _optimise_with_backtrader()

    if not rows:
        price_data = load_price_bars("AAPL", "2015-01-01", "2025-01-11")
        rows = _optimise_with_python(price_data)

    if rows:
        rows.sort(key=lambda item: item["end_capital"], reverse=True)
        _format_table(rows)
        _write_csv(rows)
        print("\n✅ Ergebnisse gespeichert als: results/optimization_results.csv")
    else:
        print("⚠️ Keine gültigen Ergebnisse generiert.")


if __name__ == "__main__":
    main()
