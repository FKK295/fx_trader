import argparse
import os
from datetime import datetime

import backtrader as bt
import pandas as pd
import quantstats as qs
from backtrader.feeds import PandasData

from config import settings
from config.trading_params import TradingParameters
# For fetching live-like data
from data_ingest.oanda_client import OandaClient
from backtest.strategies import STRATEGY_MAPPING
from utils.logging import configure_logging, get_logger

# Dask for parallelization (optional, more complex setup)
# import dask
# from dask.distributed import Client

configure_logging()
logger = get_logger(__name__)


class PandasDataFX(PandasData):
    """
    Custom PandasData feed for FX data, ensuring correct column names.
    Assumes 'time' is the index or a column.
    """
    lines = ('open', 'high', 'low', 'close', 'volume')
    params = (
        ('datetime', None),  # If 'time' is not the index, specify column name or index
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )


def run_backtest(
    strategy_name: str,
    data_path: Optional[str] = None,  # Path to CSV/Parquet data file
    instrument: Optional[str] = None,  # e.g., EUR_USD, for OANDA download
    granularity: str = "H1",
    start_date_str: str = "2022-01-01",
    end_date_str: str = "2023-01-01",
    initial_cash: float = 100000.0,
    commission_bps: float = 2.0,  # Commission in basis points (0.01%)
    slippage_bps: int = settings.TRADING.SLIPPAGE_TOLERANCE_BPS,  # From config
    output_dir: str = "backtest_results",
    strategy_params: Optional[dict] = None,
    plot_results: bool = True,
):
    if strategy_name not in STRATEGY_MAPPING:
        logger.error(
            f"Strategy '{strategy_name}' not found. Available: {list(STRATEGY_MAPPING.keys())}")
        return

    StrategyClass = STRATEGY_MAPPING[strategy_name]

    cerebro = bt.Cerebro()

    # Add Strategy
    strat_params = strategy_params if strategy_params else {}
    cerebro.addstrategy(StrategyClass, **strat_params)

    # Data Loading
    if data_path:
        logger.info(f"Loading data from file: {data_path}")
        if data_path.endswith(".csv"):
            dataframe = pd.read_csv(
                data_path, index_col='time', parse_dates=True)
        elif data_path.endswith(".parquet"):
            dataframe = pd.read_parquet(data_path)
            if 'time' in dataframe.columns:  # Ensure 'time' is index
                dataframe.set_index('time', inplace=True)
            dataframe.index = pd.to_datetime(dataframe.index)
        else:
            logger.error(f"Unsupported data file format: {data_path}")
            return

        # Filter by date range if specified
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
        dataframe = dataframe[(dataframe.index >= start_date)
                              & (dataframe.index <= end_date)]

    elif instrument:  # Fetch from OANDA
        logger.info(
            f"Fetching data for {instrument} from OANDA ({start_date_str} to {end_date_str})")
        oanda_client = OandaClient()  # Uses settings from config
        # Note: OandaClient.get_historical_candles is async, backtrader is sync.
        # For simplicity, one might use a sync wrapper or pre-download data.
        # Here, we'll assume a utility function or direct sync call if oandapyV20 was used.
        # This part needs to be adapted if using the async OandaClient.
        # For now, let's simulate that data is fetched and converted to DataFrame.
        # This is a placeholder for actual async data fetching and conversion.
        logger.warning(
            "Live OANDA data fetching in backtest runner is simplified. Consider pre-downloading or using a sync client.")
        # Example structure if data was fetched:
        # candles = asyncio.run(oanda_client.get_historical_candles(instrument, granularity, from_time=start_date, to_time=end_date))
        # dataframe = pd.DataFrame([c.dict() for c in candles])
        # dataframe['time'] = pd.to_datetime(dataframe['time'])
        # dataframe.set_index('time', inplace=True)
        # dataframe = dataframe[['open', 'high', 'low', 'close', 'volume']]
        logger.error(
            "OANDA live data fetching for backtest needs proper async handling or pre-download.")
        return  # Exit if trying to fetch live without proper setup
    else:
        logger.error("No data source specified (data_path or instrument).")
        return

    if dataframe.empty:
        logger.error(
            "DataFrame is empty after loading/filtering. Cannot run backtest.")
        return

    data_feed = PandasDataFX(dataname=dataframe, name=instrument or "DATA")
    cerebro.adddata(data_feed)

    # Set initial cash and commission
    cerebro.broker.setcash(initial_cash)
    # Commission in percentage, e.g., 0.0002 for 2 BPS
    cerebro.broker.setcommission(commission=commission_bps / 10000.0)

    # Add Slippage (Backtrader's built-in slippage is basic)
    # For more realistic slippage, custom slippage models are needed.
    # This is a fixed slippage model.
    # cerebro.broker.set_slippage_fixed(slippage_bps / 10000.0, slip_open=True, slip_limit=True, slip_market=True)
    # A common way to simulate slippage is by adjusting entry/exit prices slightly.
    # Backtrader's default slippage model might not be as granular as basis points directly.
    # One approach is to use `SlippagePercent` if available or a custom slippage class.
    # For now, we acknowledge slippage_bps from config but direct application needs care.
    logger.info(
        f"Slippage tolerance from config: {slippage_bps} BPS (manual application or custom slippage model needed for precise effect).")

    # Analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="tradeanalyzer")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe",
                        timeframe=bt.TimeFrame.Days, annualization=252)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.PyFolio,
                        _name='pyfolio')  # For QuantStats

    # Run backtest
    logger.info(
        f"Running backtest for {strategy_name} on {instrument or data_path}...")
    results = cerebro.run()
    strat_instance = results[0]

    # Output results
    os.makedirs(output_dir, exist_ok=True)
    output_prefix = f"{output_dir}/{strategy_name}_{instrument or 'custom_data'}_{start_date_str}_to_{end_date_str}"

    logger.info("Backtest complete. Generating reports...")
    logger.info(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # QuantStats report
    try:
        portfolio_stats = strat_instance.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
        returns.index = returns.index.tz_convert(
            None)  # QuantStats expects tz-naive

        qs.reports.html(
            returns, output=f"{output_prefix}_quantstats_report.html", title=f"{strategy_name} Backtest")
        logger.info(
            f"QuantStats report saved to {output_prefix}_quantstats_report.html")

        # Save structured results (example: trade list)
        trade_analysis = strat_instance.analyzers.tradeanalyzer.get_analysis()
        if trade_analysis and 'trades' in trade_analysis and trade_analysis.trades:
            trades_df = pd.DataFrame(trade_analysis.trades)
            trades_df.to_csv(f"{output_prefix}_trades.csv", index=False)
            logger.info(f"Trades list saved to {output_prefix}_trades.csv")

    except Exception as e:
        logger.error(
            f"Error generating QuantStats report or saving trades: {e}")

    # Plotting (optional)
    if plot_results:
        try:
            # Ensure matplotlib backend is suitable (e.g., Agg for non-GUI environments)
            # import matplotlib
            # matplotlib.use('Agg')
            figure = cerebro.plot(style='candlestick',
                                  barup='green', bardown='red')[0][0]
            figure.savefig(f"{output_prefix}_plot.png")
            logger.info(f"Backtrader plot saved to {output_prefix}_plot.png")
        except Exception as e:
            logger.error(
                f"Error generating plot: {e}. Ensure plotting libraries are correctly installed and configured.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Backtrader Backtest")
    parser.add_argument("--strategy", type=str, required=True,
                        choices=list(STRATEGY_MAPPING.keys()), help="Strategy name")
    parser.add_argument("--data_path", type=str,
                        help="Path to historical data CSV/Parquet file (OHLCV format, 'time' as index or column)")
    parser.add_argument("--instrument", type=str,
                        help="Instrument symbol for OANDA (e.g., EUR_USD). If provided, data_path is ignored.")
    parser.add_argument("--granularity", type=str, default="H1",
                        help="Data granularity (e.g., M1, H1, D1)")
    parser.add_argument("--start_date", type=str,
                        default="2022-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str,
                        default="2023-01-01", help="End date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float,
                        default=100000.0, help="Initial cash")
    parser.add_argument("--commission_bps", type=float,
                        default=2.0, help="Commission in basis points")
    parser.add_argument("--output_dir", type=str,
                        default="backtest_results", help="Directory for results")
    parser.add_argument("--plot", action="store_true",
                        help="Generate and save plot")
    # Example for strategy-specific params: --strategy_params '{"ema_short_period": 10, "ema_long_period": 50}'
    parser.add_argument("--strategy_params", type=str,
                        help="JSON string of strategy parameters")

    args = parser.parse_args()

    strategy_custom_params = {}
    if args.strategy_params:
        try:
            strategy_custom_params = json.loads(args.strategy_params)
        except json.JSONDecodeError:
            logger.error(
                f"Invalid JSON for strategy_params: {args.strategy_params}")
            exit(1)

    run_backtest(
        strategy_name=args.strategy,
        data_path=args.data_path,
        instrument=args.instrument,
        granularity=args.granularity,
        start_date_str=args.start_date,
        end_date_str=args.end_date,
        initial_cash=args.cash,
        commission_bps=args.commission_bps,
        output_dir=args.output_dir,
        strategy_params=strategy_custom_params,
        plot_results=args.plot,
    )
