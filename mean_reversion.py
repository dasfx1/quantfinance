import backtrader as bt

# ZScore-Indikator
class ZScore(bt.Indicator):
    lines = ('zscore',)
    params = (('period', 20),)

    def __init__(self):
        sma = bt.indicators.SMA(self.data, period=self.p.period)
        std = bt.indicators.StdDev(self.data, period=self.p.period)
        self.lines.zscore = (self.data - sma) / std


# Mean-Reversion-Strategie mit Trendfilter & TP/SL
class MeanReversion(bt.Strategy):
    params = (
        ('period', 20),         # statt 'sma_period'
        ('z_entry', 1.5),
        ('z_exit', 0.5),
        ('sl_distance', 2.0),
        ('tp_distance', 4.0),
    )

    def __init__(self):
        self.zscore = ZScore(self.data.close, period=self.p.period)
        self.adx = bt.indicators.ADX(self.data, period=14)

        self.sl_price = None
        self.tp_price = None

    def next(self):
        if len(self) < self.p.period:
            return

        if self.adx[0] >= 20:
            return

        price = self.data.close[0]

        if not self.position:
            if self.zscore[0] < -self.p.z_entry:
                self.buy()
                self.sl_price = price - self.p.sl_distance
                self.tp_price = price + self.p.tp_distance

            elif self.zscore[0] > self.p.z_entry:
                self.sell()
                self.sl_price = price + self.p.sl_distance
                self.tp_price = price - self.p.tp_distance

        else:
            if self.position.size > 0:
                if price <= self.sl_price or price >= self.tp_price:
                    self.close()
            elif self.position.size < 0:
                if price >= self.sl_price or price <= self.tp_price:
                    self.close()
