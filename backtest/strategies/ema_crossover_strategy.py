import backtrader as bt

from utils.logging import get_logger

logger = get_logger(__name__)


class EMACrossoverStrategy(bt.Strategy):
    params = (
        ("ema_short_period", 10),
        ("ema_long_period", 30),
        ("printlog", True),  # For logging trades
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.ema_short = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=self.params.ema_short_period
        )
        self.ema_long = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=self.params.ema_long_period
        )
        self.crossover = bt.indicators.CrossOver(self.ema_short, self.ema_long)

    def log(self, txt: str, dt: object = None, doprint: bool = False) -> None:
        """Logging function for this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.datetime(0)
            logger.info(f"{dt.isoformat()} - {txt}")

    def notify_order(self, order: bt.Order) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return  # Active order - Nothing to do

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, Price: {order.executed.price:.5f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(
                    f"SELL EXECUTED, Price: {order.executed.price:.5f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
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
        if self.order:  # Check if an order is pending
            return

        if not self.position:  # Not in the market
            if self.crossover > 0:  # If short EMA crosses above long EMA
                self.log(f"BUY CREATE, Close: {self.dataclose[0]:.5f}")
                self.order = self.buy()
        else:  # Already in the market
            if self.crossover < 0:  # If short EMA crosses below long EMA
                self.log(
                    f"SELL CREATE (Close Position), Close: {self.dataclose[0]:.5f}")
                self.order = self.sell()  # Or self.close()
