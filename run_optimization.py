from data_loader import get_data
from mean_reversion import MeanReversion
import backtrader as bt
import pandas as pd

# 1. Daten laden
df = get_data("AAPL", "2020-01-01", "2023-01-01")
bt_data = bt.feeds.PandasData(dataname=df)

# 2. Cerebro vorbereiten
cerebro = bt.Cerebro(maxcpus=1)
cerebro.adddata(bt_data)

# 3. Strategie mit Parametern optimieren
cerebro.optstrategy(
    MeanReversion,
    z_entry=[1.0, 1.5, 2.0],
    sl_distance=[1.0, 2.0],
    tp_distance=[2.0, 4.0],
)

# 4. Kapital und Positionsgröße
cerebro.broker.setcash(10000)
cerebro.addsizer(bt.sizers.FixedSize, stake=10)

# 5. Analyzer aktivieren
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

# 6. Run starten
results = cerebro.run()

# 7. Ergebnisse einsammeln
rows = []

for result in results:
    strat = result[0]

    # Nur echte Strategieobjekte weiterverarbeiten
    if not isinstance(strat, bt.Strategy):
        continue

    p = strat.params

    try:
        trades = strat.analyzers.trades.get_analysis()
        dd = strat.analyzers.drawdown.get_analysis()

        total = trades.total.closed or 0
        won = trades.won.total or 0
        lost = trades.lost.total or 0
        winrate = (won / total * 100) if total else 0
        dd_percent = dd.max.drawdown if dd.max else 0
        final_value = strat.broker.getvalue()

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
        print(f"⚠️ Fehler bei Parametern: z={p.z_entry}, sl={p.sl_distance}, tp={p.tp_distance}")
        print(str(e))

# 8. Ausgabe + Export
if rows:
    df_results = pd.DataFrame(rows)
    df_results = df_results.sort_values(by='end_capital', ascending=False)
    print(df_results)
    df_results.to_csv("optimization_results.csv", index=False)
    print("\n✅ Ergebnisse gespeichert als: optimization_results.csv")
else:
    print("⚠️ Keine gültigen Ergebnisse generiert.")

