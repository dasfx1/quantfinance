# QuantFinance

Backtest- und Optimierungsframework für algorithmische Handelsstrategien mit Python & Backtrader.

## 🔧 Projektstruktur

- `data_loader.py` – Datenabruf via Yahoo Finance
- `mean_reversion.py` – Mean-Reversion-Strategie mit Z-Score und ADX-Filter
- `run_backtest.py` – Einzelner Backtest einer Strategie
- `run_optimization.py` – Grid-basierte Parameter-Optimierung

## 🚀 Start

```bash
pip install -r requirements.txt
python run_backtest.py
python run_optimization.py
```

## 📊 Ziel

Strategien entwickeln und testen, um Kapital für Proprietary Trading Firmen wie FTMO zu ertraden. Fokus auf systematischen, robusten Ansätzen (Mean-Reversion, Trendfolge, Volatilität).
