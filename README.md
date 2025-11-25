# QuantFinance – Minimal Toolkit

Ein kompakter Werkzeugkasten, um Strategien schnell zu testen, zu optimieren und als Expert Advisor (MT5) vorzubereiten. Alles funktioniert offline mit den mitgelieferten Beispieldaten und bleibt damit auch für Einsteiger handhabbar.

## 📁 Struktur

```
quantfinance/
├── cli.py                     # Einstieg über die Kommandozeile
├── backtesting/engine.py      # Lightweight-Backtester mit Report-Ausgabe
├── data/loader.py             # OHLCV- und Tick-Handling inkl. Resampling
├── optimization/grid_search.py# Grid-Suche für die Mean-Reversion-Strategie
├── strategies/mean_reversion.py
├── mt5/export.py              # Export eines MQL5-Templates
└── __init__.py
reports/                       # Wird automatisch für Ergebnisse angelegt
data/AAPL_2020_2023.csv        # Beispiel-Datensatz (OHLCV)
```

## 🚀 Schnellstart

1. **Python-Umgebung anlegen (optional, aber empfohlen)**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt  # rein optional, nur für Pandas/YFinance
   ```

2. **Einzelnen Backtest ausführen** (nutzt den beigefügten Datensatz):

   ```bash
   python -m quantfinance.cli backtest \
     --ticker AAPL --start 2020-01-01 --end 2023-01-01
   ```

   Die wichtigsten Kennzahlen sowie CSV/Equity-Curve landen automatisch unter `reports/backtests/`.

3. **Parameter optimieren** (kleines Grid, jederzeit erweiterbar):

   ```bash
   python -m quantfinance.cli optimize \
     --z-entries 1.0 1.5 2.0 --sl-distances 1.0 2.0 --tp-distances 2.0 4.0
   ```

   Die Rangliste wird nach Endkapital sortiert und als `reports/optimization/optimization_results.csv` gespeichert.

4. **MT5-Template erzeugen** (nutzt optional die beste Zeile aus der Optimierung):

   ```bash
   python -m quantfinance.cli export-mt5 --optimization-csv reports/optimization/optimization_results.csv
   ```

   Das MQL5-Template liegt anschließend in `dist/mean_reversion_auto.mq5` und kann in MetaEditor weiter verfeinert werden.

## 🧠 Funktionsweise

- **Backtests**: Eine leichte Mean-Reversion-Simulation mit Z-Score-Ein-/Ausstieg, ADX-Filter und einfachen Risiko-Parametern. Keine externen Abhängigkeiten notwendig.
- **Optimierung**: Grid-Suche über Z-Entry, Stop-Loss- und Take-Profit-Distanzen. Ergebnisse werden automatisch sortiert und dokumentiert.
- **Reporting**: Jeder Lauf erzeugt gut lesbare CSVs sowie eine Kurz-Zusammenfassung (`*_README.md`). So bleiben Ergebnisse nachvollziehbar.
- **MT5-Export**: Ein generiertes `.mq5`-Gerüst überträgt die gewählten Parameter. Die Handelslogik kann im MetaEditor schnell ergänzt werden.

## 📥 Tickdaten einbinden

1. CSV mit Spalten `datetime`, `price` und optional `volume` (oder `bid`/`ask`) ablegen, z. B. `data/ticks.csv`.
2. Beim Backtest/der Optimierung den Pfad angeben:

   ```bash
   python -m quantfinance.cli backtest --tick-file data/ticks.csv --tick-interval 1min
   ```

   Die Tickdaten werden offline in OHLCV-Balken aggregiert (`tick-interval` akzeptiert z. B. `30s`, `1min`, `5min`).

## 🔧 Anpassungen

- **Strategie verfeinern**: `quantfinance/strategies/mean_reversion.py`
- **Weitere Strategien**: Neue Module im Ordner `quantfinance/strategies/` anlegen und in `cli.py` registrieren.
- **Datenschnittstellen**: `quantfinance/data/loader.py` erweitert die Datenquellen oder passt das Tick-Resampling an.

## 🧪 Hinweise für Einsteiger

- Alle Befehle lassen sich ohne weitere Setups ausführen, da ein Beispieldatensatz beiliegt.
- Ergebnisse erscheinen in klar benannten Ordnern (`reports/backtests`, `reports/optimization`, `dist`).
- Für Live-Daten oder größere Historien können optional `pandas` und `yfinance` installiert werden (siehe `requirements.txt`).

Viel Erfolg beim Testen, Optimieren und Exportieren! 
