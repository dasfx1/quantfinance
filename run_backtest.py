import csv

from data_loader import load_price_bars
from mean_reversion import MeanReversionParams, run_mean_reversion

# 1. Daten laden
try:
    price_data = load_price_bars("AAPL", "2020-01-01", "2023-01-01", prefer_local=True)
except FileNotFoundError:
    price_data = load_price_bars("AAPL", "2020-01-01", "2023-01-01")

# 2. Strategie mit Standardparametern testen
params = MeanReversionParams()
stats = run_mean_reversion(price_data, params)

headers = ["Parameter", "Wert"]
rows = [
    {"Parameter": "z_entry", "Wert": params.z_entry},
    {"Parameter": "sl_distance", "Wert": params.sl_distance},
    {"Parameter": "tp_distance", "Wert": params.tp_distance},
    {"Parameter": "total_trades", "Wert": stats["total_trades"]},
    {"Parameter": "winrate", "Wert": f"{stats['winrate']}%"},
    {"Parameter": "drawdown_%", "Wert": stats["drawdown_%"]},
    {"Parameter": "end_capital", "Wert": stats["end_capital"]},
]

widths = {
    h: max([len(h)] + [len(str(row[h])) for row in rows])
    for h in headers
}

def format_row(row):
    return " | ".join(f"{str(row[h]).rjust(widths[h])}" for h in headers)

header_line = format_row({h: h for h in headers})
separator = "-+-".join("-" * widths[h] for h in headers)

print(header_line)
print(separator)
for row in rows:
    print(format_row(row))

with open("backtest_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)

print("\n✅ Ergebnisse gespeichert als: backtest_results.csv")

