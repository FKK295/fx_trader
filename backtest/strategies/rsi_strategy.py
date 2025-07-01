import backtrader as bt

from utils.logging import get_logger

logger = get_logger(__name__)


class RSIStrategy(bt.Strategy):
    params = (
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("printlog", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.rsi = bt.indicators.RelativeStrengthIndex(
            period=self.params.rsi_period
        )

    def log(self, txt: str, dt: object = None, doprint: bool = False) -> None:
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.datetime(0)
            logger.info(f"{dt.isoformat()} - {txt}")

    def notify_order(self, order: bt.Order) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.5f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.5f}")
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(
                f"Order Canceled/Margin/Rejected: {order.Status[order.status]}")
        self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return
        self.log(
            f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")

    def next(self):
        if self.order:
            return

        if not self.position:  # Not in the market
            if self.rsi < self.params.rsi_oversold:
                self.log(
                    f"BUY CREATE (RSI Oversold), Close: {self.dataclose[0]:.5f}, RSI: {self.rsi[0]:.2f}")
                self.order = self.buy()
        else:  # In the market
            if self.rsi > self.params.rsi_overbought:
                self.log(
                    f"SELL CREATE (RSI Overbought - Close Position), Close: {self.dataclose[0]:.5f}, RSI: {self.rsi[0]:.2f}")
                self.order = self.sell()
