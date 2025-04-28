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


class RSIMeanReversion(Strategy):
    """
    Mean-reversion strategy using RSI:
      - Long when RSI < oversold
      - Short when RSI > overbought
      - Exit to flat when RSI crosses exit_level
    """
    rsi_period = 14
    oversold = 30
    overbought = 70
    exit_level = 50

    def init(self):
        close = pd.Series(self.data.Close)

        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        self.rsi = self.I(lambda: rsi.values, name='RSI')


    def next(self):
        # Entry
        if not self.position:
            if self.rsi[-1] < self.oversold:
                self.buy()
            elif self.rsi[-1] > self.overbought:
                self.sell()
        else:
            # Exit conditions
            if self.position.is_long and self.rsi[-1] > self.exit_level:
                self.position.close()
            elif self.position.is_short and self.rsi[-1] < self.exit_level:
                self.position.close()


def run_backtest(data: pd.DataFrame):
    """
    Execute backtest and display performance.
    """
    bt = Backtest(
        data,
        RSIMeanReversion,
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
        description='Backtest RSI mean-reversion on EUR/USD Forex data.'
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
