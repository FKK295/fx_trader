import backtrader as bt

from utils.logging import get_logger

logger = get_logger(__name__)


class BollingerBandsStrategy(bt.Strategy):
    params = (
        ("bb_period", 20),
        ("bb_devfactor", 2.0),  # Standard deviations
        ("printlog", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.bollinger = bt.indicators.BollingerBands(
            period=self.params.bb_period, devfactor=self.params.bb_devfactor
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

        # Example: Mean Reversion Strategy
        if not self.position:  # Not in the market
            # Price closes below lower band
            if self.dataclose[0] < self.bollinger.lines.bot[0]:
                self.log(
                    f"BUY CREATE (Mean Reversion), Close: {self.dataclose[0]:.5f}, BBot: {self.bollinger.lines.bot[0]:.5f}")
                self.order = self.buy()
        else:  # In the market
            # Exit if price touches middle band or upper band
            if self.position.size > 0:  # If long
                if self.dataclose[0] > self.bollinger.lines.mid[0] or self.dataclose[0] > self.bollinger.lines.top[0]:
                    self.log(
                        f"SELL CREATE (Mean Reversion Exit), Close: {self.dataclose[0]:.5f}, BMid: {self.bollinger.lines.mid[0]:.5f}")
                    self.order = self.sell()
            # Add logic for short positions if strategy supports them
            # elif self.position.size < 0: # If short
            #     if self.dataclose[0] > self.bollinger.lines.mid[0] or self.dataclose[0] < self.bollinger.lines.bot[0]:
            #         self.log(f"BUY CREATE (Mean Reversion Exit - Cover Short), Close: {self.dataclose[0]:.5f}")
            #         self.order = self.buy() # Cover short
