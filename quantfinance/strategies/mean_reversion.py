from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


def _rolling_zscore(values: Sequence[float], period: int) -> List[float]:
    zscores = [0.0] * len(values)
    for idx in range(len(values)):
        if idx + 1 < period:
            zscores[idx] = 0.0
            continue
        window = values[idx + 1 - period : idx + 1]
        mean = sum(window) / period
        variance = sum((v - mean) ** 2 for v in window) / period
        std = variance ** 0.5
        zscores[idx] = (values[idx] - mean) / std if std else 0.0
    return zscores


def _calculate_adx(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14
) -> List[float]:
    length = len(closes)
    adx = [0.0] * length
    if length <= period:
        return adx

    plus_dm = [0.0] * length
    minus_dm = [0.0] * length
    tr = [0.0] * length

    for i in range(1, length):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm[i] = up_move if up_move > down_move and up_move > 0 else 0.0
        minus_dm[i] = down_move if down_move > up_move and down_move > 0 else 0.0
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    atr = [0.0] * length
    atr[period] = sum(tr[1 : period + 1]) / period
    plus_dm_smooth = sum(plus_dm[1 : period + 1])
    minus_dm_smooth = sum(minus_dm[1 : period + 1])

    plus_di = [0.0] * length
    minus_di = [0.0] * length
    dx = [0.0] * length

    if atr[period] != 0:
        plus_di[period] = 100 * (plus_dm_smooth / atr[period])
        minus_di[period] = 100 * (minus_dm_smooth / atr[period])
        denominator = plus_di[period] + minus_di[period]
        if denominator != 0:
            dx[period] = 100 * abs(plus_di[period] - minus_di[period]) / denominator

    adx[period] = dx[period]

    for i in range(period + 1, length):
        atr[i] = ((atr[i - 1] * (period - 1)) + tr[i]) / period
        plus_dm_smooth = plus_dm_smooth - (plus_dm_smooth / period) + plus_dm[i]
        minus_dm_smooth = minus_dm_smooth - (minus_dm_smooth / period) + minus_dm[i]

        if atr[i] != 0:
            plus_di[i] = 100 * (plus_dm_smooth / atr[i])
            minus_di[i] = 100 * (minus_dm_smooth / atr[i])
            denominator = plus_di[i] + minus_di[i]
            if denominator != 0:
                dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / denominator

        adx[i] = ((adx[i - 1] * (period - 1)) + dx[i]) / period

    return adx


@dataclass(frozen=True)
class MeanReversionParams:
    period: int = 20
    z_entry: float = 1.5
    z_exit: float = 0.5
    sl_distance: float = 2.0
    tp_distance: float = 4.0
    stake: int = 10
    initial_cash: float = 10_000.0


@dataclass
class MeanReversionReport:
    total_trades: int
    wins: int
    losses: int
    winrate: float
    drawdown_percent: float
    end_capital: float
    equity_curve: List[float]

    def as_row(self) -> Dict[str, float]:
        return {
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "winrate": round(self.winrate, 2),
            "drawdown_%": round(self.drawdown_percent, 2),
            "end_capital": round(self.end_capital, 2),
        }


def simulate_mean_reversion(
    prices: Iterable[Dict[str, float]], params: MeanReversionParams
) -> MeanReversionReport:
    data = list(prices) if not isinstance(prices, list) else prices
    closes = [row["Close"] for row in data]
    highs = [row["High"] for row in data]
    lows = [row["Low"] for row in data]

    zscores = _rolling_zscore(closes, params.period)
    adx = _calculate_adx(highs, lows, closes, period=14)

    cash = params.initial_cash
    equity_curve = [cash]

    position = 0  # -1 short, 1 long
    entry_price = 0.0
    sl_price = 0.0
    tp_price = 0.0

    total_trades = 0
    wins = 0
    losses = 0

    for idx, row in enumerate(data):
        price = row["Close"]
        z = zscores[idx]
        current_adx = adx[idx]

        if position == 0:
            if idx + 1 < params.period:
                equity_curve.append(cash)
                continue

            if current_adx >= 20:
                equity_curve.append(cash)
                continue

            if z <= -params.z_entry:
                position = 1
                entry_price = price
                sl_price = price - params.sl_distance
                tp_price = price + params.tp_distance
            elif z >= params.z_entry:
                position = -1
                entry_price = price
                sl_price = price + params.sl_distance
                tp_price = price - params.tp_distance

        else:
            exit_trade = False
            exit_price = price

            if position == 1:
                if price <= sl_price or price >= tp_price or abs(z) <= params.z_exit:
                    exit_trade = True
            else:
                if price >= sl_price or price <= tp_price or abs(z) <= params.z_exit:
                    exit_trade = True

            if exit_trade:
                if position == 1:
                    pnl = (exit_price - entry_price) * params.stake
                else:
                    pnl = (entry_price - exit_price) * params.stake

                cash += pnl
                total_trades += 1
                if pnl > 0:
                    wins += 1
                elif pnl < 0:
                    losses += 1

                position = 0
                entry_price = 0.0
                sl_price = 0.0
                tp_price = 0.0

        equity_curve.append(cash)

    if position != 0 and entry_price:
        final_price = closes[-1]
        if position == 1:
            pnl = (final_price - entry_price) * params.stake
        else:
            pnl = (entry_price - final_price) * params.stake
        cash += pnl
        total_trades += 1
        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1
        equity_curve[-1] = cash

    peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100 if peak else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    winrate = (wins / total_trades * 100) if total_trades else 0.0

    return MeanReversionReport(
        total_trades=total_trades,
        wins=wins,
        losses=losses,
        winrate=winrate,
        drawdown_percent=round(max_drawdown, 2),
        end_capital=round(cash, 2),
        equity_curve=equity_curve,
    )
