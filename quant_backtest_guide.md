# QuantFinance Projekt – Handbuch für Strategieentwicklung, Backtests & Optimierung

Dieses Handbuch erklärt so, dass **jede Person mit Grundkenntnissen in Python** mit diesem Projekt arbeiten kann:

- Wie der Code aufgebaut ist
- Wie du Daten lädst
- Wie Strategien strukturiert sind
- Wie du Backtests startest
- Wie du Parameter optimierst
- Wie du Ergebnisse in Jupyter analysierst

Alles ist auf das Ziel ausgerichtet: **systematisch Strategien für Prop-Trading-Challenges (z. B. FTMO) entwickeln und testen**.

---

## 1. Technischer Überblick

### 1.1. Was dieses Projekt benutzt

- **Python 3.10+** (bei dir 3.13)
- **Backtrader** – Backtesting-Framework
- **pandas** – Datenverarbeitung
- **yfinance** – Kursdaten von Yahoo Finance laden
- **matplotlib** – Charts (optional in Notebooks)
- **VS Code** – Haupt-IDE
- **Jupyter Notebooks** – Analyse & Visualisierung
- **Git/GitHub** – Versionskontrolle (optional, aber empfohlen)

### 1.2. Ziel des Projekts

Das Projekt ist so aufgebaut, dass du:

1. **Daten laden** kannst (z. B. AAPL, EURUSD via CFD-Proxy etc.)
2. **Strategien in `strategies/` definierst** (z. B. Mean Reversion, Trendfolge, Breakout)
3. **Backtests mit `backtest/run_backtest.py`** fährst
4. **Parameter-Optimierungen mit `optimization/run_optimization.py`** durchführst
5. **Ergebnisse per CSV** speicherst und
6. **in Jupyter Notebooks** analysierst.

---

## 2. Ordnerstruktur & Rollen

Die Projektstruktur ist bewusst klar gehalten:

```text
quantfinance/
├── backtest/
│   ├── run_backtest.py         # Einzelner Backtest für eine Strategie
│   └── results/                # CSV-Ergebnisse der Backtests
├── optimization/
│   ├── run_optimization.py     # Grid-Search / Parameter-Optimierung
│   └── results/                # CSV-Ergebnisse der Optimierung
├── data_loader/
│   └── data_loader.py          # Funktionen zum Laden von Kursdaten
├── strategies/
│   └── mean_reversion.py       # Mean-Reversion-Strategie & Logik
└── notebooks/
    └── analyse.ipynb           # Jupyter Notebook für Auswertung
```

### 2.1. `data_loader/`

Enthält Funktionen, die dafür zuständig sind:

- Historische Daten mit `yfinance` zu laden
- Sie in das Format zu bringen, das Backtrader erwartet
- Hilfsfunktionen wie `is_dataframe` oder `load_price_bars`

### 2.2. `strategies/`

Hier kommen alle Trading-Strategien als Klassen hin, z. B.:

- `MeanReversion` (Z-Score-basierte Mean-Reversion)
- Später z. B. `TrendFollower`, `Breakout`, `Scalper` etc.

Jede Strategie ist eine Klasse, die von `backtrader.Strategy` erbt.

### 2.3. `backtest/`

- `run_backtest.py` führt **einen Backtest** für **eine Strategie** mit **festen Parametern** aus.
- Speichert die wichtigsten Kennzahlen (Trades, Winrate, Drawdown, Endkapital) in `backtest/results/backtest_results.csv`.

### 2.4. `optimization/`

- `run_optimization.py` führt **viele Backtests mit verschiedenen Parametern** aus
- Speichert die Resultate in `optimization/results/optimization_results.csv`
- Dient dazu, sinnvolle Parameter-Kombinationen zu finden

### 2.5. `notebooks/`

- Notebooks für Analyse, Visualisierung, Vergleich von Strategien
- Zugriff auf die CSVs aus `backtest/results/` und `optimization/results/`

---

## 3. Daten laden – `data_loader/data_loader.py`

Ein typischer Aufbau sieht (vereinfacht) so aus:

```python
import yfinance as yf
import pandas as pd


def get_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Lädt historische Kursdaten von Yahoo Finance.

    Args:
        ticker: Tickersymbol, z.B. "AAPL" oder "SPY".
        start: Startdatum im Format "YYYY-MM-DD".
        end: Enddatum im Format "YYYY-MM-DD".

    Returns:
        Ein DataFrame mit Spalten wie Open, High, Low, Close, Volume.
    """
    df = yf.download(ticker, start=start, end=end, progress=False)
    df.dropna(inplace=True)
    return df


def is_dataframe(obj) -> bool:
    """Hilfsfunktion: Prüft, ob es ein DataFrame mit Close-Spalte ist."""
    return hasattr(obj, "columns") and "Close" in obj.columns
```

### 3.1. Was hier wichtig ist

- **`get_data`** kapselt den Zugriff auf Yahoo Finance. Wenn du später auf andere Datenquellen wechselst (CSV, Datenbank, Broker API), änderst du nur dieses Modul.
- **`is_dataframe`** ist eine kleine Sicherheitsfunktion, um Fehler früh zu erkennen.

---

## 4. Mean-Reversion-Strategie – `strategies/mean_reversion.py`

Die Strategie basiert auf einem **Z-Score** der Preise zur gleitenden Durchschnittslinie (SMA). Idee:

- Wenn der Preis weit **unter** dem Durchschnitt liegt → überverkauft → Long-Einstieg
- Wenn der Preis weit **über** dem Durchschnitt liegt → überkauft → Short-Einstieg
- Ausstieg, wenn der Preis wieder in Richtung Mittelwert zurückkehrt

Ein möglicher Aufbau (vereinfacht und an dein Projekt angelehnt):

```python
import backtrader as bt


class ZScore(bt.Indicator):
    lines = ("zscore",)
    params = ("period", 20)

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.p.period)
        std = bt.indicators.StdDev(self.data, period=self.p.period)
        self.lines.zscore = (self.data - sma) / std


class MeanReversion(bt.Strategy):
    params = (
        ("sma_period", 20),
        ("z_entry", 1.5),
        ("z_exit", 0.5),
        ("sl_distance", 2.0),
        ("tp_distance", 4.0),
    )

    def __init__(self):
        self.zscore = ZScore(self.data.close, period=self.p.sma_period)
        self.sl_price = None
        self.tp_price = None

    def next(self):
        price = self.data.close[0]

        # Einstieg
        if not self.position:
            if self.zscore[0] < -self.p.z_entry:
                self.buy()
                self.sl_price = price - self.p.sl_distance
                self.tp_price = price + self.p.tp_distance
            elif self.zscore[0] > self.p.z_entry:
                self.sell()
                self.sl_price = price + self.p.sl_distance
                self.tp_price = price - self.p.tp_distance

        # Ausstieg (SL / TP)
        else:
            if self.position.size > 0:  # Long
                if price <= self.sl_price or price >= self.tp_price:
                    self.close()
            elif self.position.size < 0:  # Short
                if price >= self.sl_price or price <= self.tp_price:
                    self.close()
```

### 4.1. Wichtige Punkte im Code

- `params`: Alle wichtigen Einstellungen sind als Parameter definiert → ideal für Optimierungen.
- `__init__`: Hier werden Indikatoren initialisiert (SMA, StdDev, ZScore).
- `next()`: Diese Methode wird **bei jeder neuen Kerze** aufgerufen und enthält die Handelslogik:
  - Einstieg nur, wenn aktuell keine Position offen ist
  - Stop-Loss und Take-Profit werden direkt beim Einstieg berechnet
  - Ausstieg, wenn SL/TP erreicht sind

---

## 5. Backtest – `backtest/run_backtest.py`

Beispiel (angepasst an dein Projekt):

```python
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

# 7. Ergebnisse speichern
results_dir = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(results_dir, exist_ok=True)
output_path = os.path.join(results_dir, "backtest_results.csv")

pd.DataFrame([
    {
        "total_trades": total,
        "won": won,
        "winrate": round(winrate, 2),
        "drawdown_%": round(dd_percent, 2),
        "end_capital": round(final_value, 2),
    }
]).to_csv(output_path, index=False)

print(f"\n✅ Backtest-Ergebnisse gespeichert unter: {output_path}")
```

### 5.1. Wie du den Backtest startest

Im Terminal im Projektordner `quantfinance/`:

```bash
python backtest/run_backtest.py
```

Dann siehst du im Terminal:

- Startkapital
- Endkapital
- Anzahl der Trades
- Winrate
- Max Drawdown

Und die CSV liegt in:

```text
backtest/results/backtest_results.csv
```

---

## 6. Parameter-Optimierung – `optimization/run_optimization.py`

Die Optimierung testet automatisch **mehrere Parameterkombinationen** und speichert die Ergebnisse.

Vereinfacht funktioniert es so:

- Verschiedene Werte für `z_entry`, `sl_distance`, `tp_distance` werden durchprobiert.
- Für jede Kombination wird ein Backtest durchgeführt.
- Die Kennzahlen werden gesammelt und als Tabelle ausgegeben.

Beispielhafter Ablauf im Code:

```python
rows = []
for z_entry in [1.0, 1.5, 2.0]:
    for sl in [1.0, 2.0]:
        for tp in [2.0, 4.0]:
            # Strategie mit diesen Parametern starten
            # Ergebnisse (Trades, Winrate, Drawdown, Endkapital) sammeln
            rows.append({ ... })
```

Am Ende wird:

- eine Tabelle im Terminal ausgegeben
- eine CSV in `optimization/results/optimization_results.csv` gespeichert

### 6.1. Optimierung starten

Im Terminal:

```bash
python optimization/run_optimization.py
```

Eine typische Ausgabe sieht z. B. so aus:

```text
z_entry | sl_distance | tp_distance | total_trades | winrate | drawdown_% | end_capital
--------+-------------+-------------+--------------+---------+------------+-----------
    2.0 |         1.0 |         2.0 |           49 |   46.94 |       1.25 | 10088.02
    1.5 |         1.0 |         2.0 |           91 |   48.35 |       2.68 | 10004.96
    ...
```

Damit kannst du auf einen Blick sehen, welche Parameter-Kombinationen:

- am meisten Gewinn bringen
- gleichzeitig moderaten Drawdown haben

---

## 7. Analyse in Jupyter Notebooks

Für tiefere Analyse (Heatmaps, Verteilungen, Equity-Kurven etc.) nutzt du ein Notebook in `notebooks/`, z. B. `analyse.ipynb`.

Beispielcode zur Auswertung der Optimierung:

```python
import pandas as pd
import matplotlib.pyplot as plt

# CSV laden
df = pd.read_csv("../optimization/results/optimization_results.csv")

# Beste Zeilen anzeigen
print(df.sort_values(by="end_capital", ascending=False).head())

# Beziehung zwischen Winrate und Drawdown plotten
plt.scatter(df["drawdown_%"], df["winrate"])
plt.xlabel("Max Drawdown [%]")
plt.ylabel("Winrate [%]")
plt.title("Drawdown vs. Winrate")
plt.show()
```

Du kannst dir so z. B. Strategien mit:

- geringerem Drawdown
- aber akzeptabler Winrate

heraussuchen.

---

## 8. Eigene Strategien hinzufügen – Schritt für Schritt

Angenommen, du willst eine neue Strategie `Breakout` erstellen.

### 8.1. Datei anlegen

Lege eine neue Datei an:

```text
strategies/breakout.py
```

### 8.2. Minimaler Strategie-Skeleton

```python
import backtrader as bt


class Breakout(bt.Strategy):
    params = (
        ("period", 20),
        ("risk", 0.01),
    )

    def __init__(self):
        self.highest = bt.ind.Highest(self.data.high, period=self.p.period)
        self.lowest = bt.ind.Lowest(self.data.low, period=self.p.period)

    def next(self):
        price = self.data.close[0]

        if not self.position:
            if price > self.highest[-1]:
                self.buy()
            elif price < self.lowest[-1]:
                self.sell()
        else:
            # einfache Exit-Regeln, z. B. Gegensignal
            if self.position.size > 0 and price < self.lowest[-1]:
                self.close()
            elif self.position.size < 0 and price > self.highest[-1]:
                self.close()
```

### 8.3. Backtest mit neuer Strategie

In `backtest/run_backtest.py` anpassen:

```python
from strategies.breakout import Breakout

# statt MeanReversion:
# cerebro.addstrategy(MeanReversion)
cerebro.addstrategy(Breakout)
```

Jetzt:

```bash
python backtest/run_backtest.py
```

### 8.4. Optimierung für neue Strategie

Du kannst `run_optimization.py` so erweitern, dass statt `MeanReversion` die `Breakout`-Strategie verwendet wird und andere Parameter-Ranges getestet werden.

---

## 9. Typische Fehler & Lösungen

### 9.1. `ModuleNotFoundError: No module named 'data_loader'`

Ursache:
- Python kennt das Projekt-Root nicht.

Lösung:

- Am Anfang von `run_backtest.py` und `run_optimization.py`:

```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

### 9.2. `FileNotFoundError` beim Laden von CSVs im Notebook

Ursache:
- Falscher relativer Pfad.

Lösung:

1. Im Notebook prüfen:

```python
import os
print(os.getcwd())
```

2. Pfad dann daran anpassen, z. B.:

```python
df = pd.read_csv("../optimization/results/optimization_results.csv")
```

### 9.3. Leere Daten oder komische Ergebnisse

- Überprüfe das Datum: Yahoo-Finance-Daten müssen verfügbar sein.
- Fx-Ticker haben teilweise andere Symbole (z. B. `EURUSD=X`).
- Immer zuerst `print(df.head())` machen, bevor du backtestest.

---

## 10. Git & Versionierung (Kurz)

Damit du Änderungen sicherst und zurückverfolgen kannst:

```bash
git status                  # Was ist geändert?
git add .                   # Alles zum Commit vormerken
git commit -m "Beschreibung"  # Änderungen speichern
```

Push nach GitHub (falls eingerichtet):

```bash
git push
```

Für Experimente empfiehlt sich:

- Neue Branches für neue Strategien
- Commits mit klaren Messages, z. B. `"Add ADX trend filter to MeanReversion"`

---

## 11. Standard-Workflow für dieses Projekt

Wenn du an einer neuen Idee arbeitest, kannst du dich immer an diesen Ablauf halten:

1. **Daten festlegen**
   - Welches Symbol? (z. B. AAPL, SPY, EURUSD=X)
   - Welcher Zeitraum? (z. B. 2015–2025 für Robustheit)

2. **Strategie in `strategies/` definieren**
   - Klasse anlegen, Parameter definieren
   - `__init__()` für Indikatoren
   - `next()` für Entry/Exit-Regeln

3. **Backtest aufsetzen** (`backtest/run_backtest.py`)
   - Strategie importieren
   - Startkapital & Positionsgröße definieren
   - Analyzer hinzufügen
   - Ergebnisse prüfen + CSV speichern

4. **Parameter optimieren** (`optimization/run_optimization.py`)
   - Parameter-Ranges definieren
   - Ergebnisse sortieren (z. B. nach Endkapital, Drawdown)

5. **Analyse im Notebook** (`notebooks/analyse.ipynb`)
   - CSV laden
   - Top-Kandidaten vergleichen
   - Grafiken & Metriken ansehen

6. **Dokumentieren**
   - Kurze Notiz: Was wurde getestet? Welche Parameter funktionieren gut? Was ist fragwürdig?

---

## 12. Ausblick: Richtung Prop-Trading

Damit dieses Setup wirklich für Prop-Firmen wie FTMO brauchbar wird, brauchst du:

- Tests über verschiedene Marktphasen (Crash, Seitwärts, Bullenmarkt)
- Robustheitsprüfungen (Walk-Forward, Out-of-Sample)
- Anpassung auf Instrumente, die du in MT5 handeln willst (später Brücke von Backtrader → MQL5/MT5)

Dieses Projekt gibt dir dafür das **Fundament**:

- Saubere Struktur
- Wiederholbare Backtests
- Systematische Optimierung
- Klare Trennung von Daten, Strategie, Backtest & Analyse

Damit kannst du Schritt für Schritt vom Python-Backtester zum robusten EA im Prop-Umfeld kommen.

