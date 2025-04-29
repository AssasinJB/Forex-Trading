import pandas as pd
import ta
from backtesting import Backtest, Strategy


def load_data(path: str) -> pd.DataFrame:
    """
    Load EUR/USD data from Excel and prepare DataFrame for backtesting.
    """
    df = pd.read_excel(path, parse_dates=['Timestamp'])
    df.set_index('Timestamp', inplace=True)
    # Rename columns to match backtesting.py expectations
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return df


import numpy as np

class MACDCrossover(Strategy):
    fast_period = 12
    slow_period = 26
    signal_period = 9

    def init(self):
        close = self.data.Close

        self.ema_fast = self.I(self.ema, close, self.fast_period)
        self.ema_slow = self.I(self.ema, close, self.slow_period)
        self.macd_line = self.I(lambda: self.ema_fast() - self.ema_slow())
        self.signal_line = self.I(self.ema, self.macd_line, self.signal_period)

    def next(self):
        if len(self.macd_line) < 2 or len(self.signal_line) < 2:
            return

        # Bullish crossover
        if not self.position and self.macd_line[-2] < self.signal_line[-2] and self.macd_line[-1] > self.signal_line[-1]:
            self.buy()
        # Bearish crossover
        elif not self.position and self.macd_line[-2] > self.signal_line[-2] and self.macd_line[-1] < self.signal_line[-1]:
            self.sell()
        # Exit long
        elif self.position.is_long and self.macd_line[-2] > self.signal_line[-2] and self.macd_line[-1] < self.signal_line[-1]:
            self.position.close()
        # Exit short
        elif self.position.is_short and self.macd_line[-2] < self.signal_line[-2] and self.macd_line[-1] > self.signal_line[-1]:
            self.position.close()

    @staticmethod
    def ema(arr, n):
        """
        Helper function to calculate Exponential Moving Average
        """
        arr = np.asarray(arr)
        ema_arr = np.empty_like(arr)
        alpha = 2 / (n + 1)
        ema_arr[0] = arr[0]
        for i in range(1, len(arr)):
            ema_arr[i] = alpha * arr[i] + (1 - alpha) * ema_arr[i - 1]
        return ema_arr
    """
    MACD Crossover strategy:
      - Buy when MACD crosses above Signal line
      - Sell when MACD crosses below Signal line
    """
    fast_period = 12
    slow_period = 26
    signal_period = 9

    def init(self):
        close = self.data.Close
        self.macd_line = self.I(ta.trend.macd, close, self.fast_period, self.slow_period)
        self.signal_line = self.I(ta.trend.macd_signal, close, self.fast_period, self.slow_period, self.signal_period)

    def next(self):
        if len(self.macd_line) < 2 or len(self.signal_line) < 2:
            return

        # Bullish crossover
        if not self.position and self.macd_line[-2] < self.signal_line[-2] and self.macd_line[-1] > self.signal_line[-1]:
            self.buy()
        # Bearish crossover
        elif not self.position and self.macd_line[-2] > self.signal_line[-2] and self.macd_line[-1] < self.signal_line[-1]:
            self.sell()
        # Exit long
        elif self.position.is_long and self.macd_line[-2] > self.signal_line[-2] and self.macd_line[-1] < self.signal_line[-1]:
            self.position.close()
        # Exit short
        elif self.position.is_short and self.macd_line[-2] < self.signal_line[-2] and self.macd_line[-1] > self.signal_line[-1]:
            self.position.close()


def run_backtest(data: pd.DataFrame):
    """
    Execute backtest and display performance.
    """
    bt = Backtest(
        data,
        MACDCrossover,
        cash=10000,
        commission=0.0,
        exclusive_orders=True
    )
    output = bt.run()
    print("Backtest Results:")
    print(output[['Win Rate [%]', 'Sharpe Ratio', 'Sortino Ratio', 'Max. Drawdown [%]',
                  'Calmar Ratio', 'Return [%]']])
    try:
        bt.plot()
    except Exception:
        pass


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Backtest MACD Crossover on EUR/USD Forex data.'
    )
    parser.add_argument(
        '--data', '-d',
        type=str,
        default='eurusd-forex-data.xlsx',
        help='Path to the EUR/USD Excel data file.'
    )
    args = parser.parse_args()

    df = load_data(args.data)
    run_backtest(df)
