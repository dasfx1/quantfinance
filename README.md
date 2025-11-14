# QuantFinance

Backtest- und Optimierungsframework für algorithmische Handelsstrategien mit Python. Die ursprüngliche Version nutzte Backtrader,
die aktuelle Ausführung setzt auf eine leichtgewichtige Eigen-Implementierung und funktioniert dadurch komplett offline.

## 🔧 Projektstruktur

- `data_loader.py` – Lädt Daten entweder via Yahoo Finance (falls verfügbar) oder aus der lokalen `data/`-Ablage.
- `mean_reversion.py` – Mean-Reversion-Strategie mit Z-Score und ADX-Filter in purem Python.
- `run_backtest.py` – Einzelner Backtest einer Strategie mit Standardparametern.
- `run_optimization.py` – Grid-basierte Parameter-Optimierung ohne Backtrader-Abhängigkeit.

## 🚀 Start

```bash
python run_backtest.py
python run_optimization.py
```

Eine Beispieldatei (`data/AAPL_2020_2023.csv`) ist bereits enthalten. Eigene Datensätze können im gleichen Format ergänzt werden.

## 📊 Ziel

Strategien entwickeln und testen, um Kapital für Proprietary Trading Firmen wie FTMO zu ertraden. Fokus auf systematischen, robusten Ansätzen (Mean-Reversion, Trendfolge, Volatilität).
