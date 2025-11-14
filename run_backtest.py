from data_loader import get_data
from mean_reversion import MeanReversion
import backtrader as bt
import pandas as pd

# 1. Daten laden
df = get_data("AAPL", "2020-01-01", "2023-01-01")
bt_data = bt.feeds.PandasData(dataname=df)

# 2. Cerebro vorbereiten
cerebro = bt.Cerebro()
cerebro.adddata(bt_data)

# 3. Strategie mit Parametern optimieren
cerebro.optstrategy(
    MeanReversion,
    z_entry=[1.0, 1.5, 2.0],
    sl_distance=[1.0, 2.0],
    tp_distance=[2.0, 4.0],
)

# 4. Startgeld und Sizer
cerebro.broker.setcash(10000)
cerebro.addsizer(bt.sizers.FixedSize, stake=10)

# 5. Analyzer hinzufügen
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

# 6. Backtest starten
results = cerebro.run()

# 7. Ergebnisse sammeln
rows = []

for strat in results:
    s = strat[0]
    p = s.params

    try:
        trades = s.analyzers.trades.get_analysis()
        dd = s.analyzers.drawdown.get_analysis()

        total = trades.total.closed or 0
        won = trades.won.total or 0
        lost = trades.lost.total or 0
        winrate = (won / total * 100) if total else 0
        dd_percent = dd.max.drawdown if dd.max else 0
        final_value = s.broker.getvalue()

        rows.append({
            'z_entry': p.z_entry,
            'sl_distance': p.sl_distance,
            'tp_distance': p.tp_distance,
            'total_trades': total,
            'winrate': round(winrate, 2),
            'drawdown_%': round(dd_percent, 2),
            'end_capital': round(final_value, 2)
        })

    except Exception as e:
        print(f"Fehler bei z={p.z_entry}, sl={p.sl_distance}, tp={p.tp_distance}")
        print(str(e))

# 8. Ergebnisse als Tabelle anzeigen und speichern
df_results = pd.DataFrame(rows)
df_results = df_results.sort_values(by='end_capital', ascending=False)
print(df_results)

# 9. Optional speichern
#df_results.to_csv("optimization_results.csv", index=False)
#print("\nErgebnisse gespeichert als: optimization_results.csv")


# 7. Chart anzeigen
#cerebro.plot(style='candlestick')

