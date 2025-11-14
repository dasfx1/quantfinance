import sys
import os
import backtrader as bt
import pandas as pd

# Projektverzeichnis zum Pfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_loader.data_loader import get_data
from strategies.mean_reversion import MeanReversion

# 1. Daten laden
data = get_data("AAPL", "2020-01-01", "2023-01-01")
bt_data = bt.feeds.PandasData(dataname=data)

# 2. Cerebro vorbereiten
cerebro = bt.Cerebro()
cerebro.adddata(bt_data)
cerebro.addstrategy(MeanReversion)

# 3. Broker und Sizer
cerebro.broker.setcash(10000)
cerebro.addsizer(bt.sizers.FixedSize, stake=10)

# 4. Analyzer hinzufügen
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

# 5. Backtest starten
print("Startkapital:", cerebro.broker.getvalue())
results = cerebro.run()
final_value = cerebro.broker.getvalue()
print("Endkapital:", final_value)

# 6. Auswertung
strat = results[0]
trades = strat.analyzers.trades.get_analysis()
drawdown = strat.analyzers.drawdown.get_analysis()

total = trades.total.closed or 0
won = trades.won.total or 0
winrate = (won / total * 100) if total else 0
dd_percent = drawdown.max.drawdown if drawdown.max else 0

print("\n--- Statistik ---")
print(f"Trades gesamt: {total}")
print(f"Gewonnen: {won} | Winrate: {winrate:.2f}%")
print(f"Max Drawdown: {dd_percent:.2f}%")

# 7. Optional: CSV speichern
results_dir = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(results_dir, exist_ok=True)
output_path = os.path.join(results_dir, "backtest_results.csv")

pd.DataFrame(data).to_csv(output_path)
print(f"\n✅ Backtest-Daten gespeichert unter: {output_path}")
