import pandas as pd
import ta 
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import argparse # Keep argparse as it was in your original structure

# Keep your original data loading function
def load_data(path: str) -> pd.DataFrame:
    """
    Load EUR/USD data from Excel and prepare DataFrame for backtesting.
    """
    print(f"Loading data from: {path}")
    try:
        df = pd.read_excel(path, parse_dates=['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        # Ensure column names are suitable for backtesting.py
        # Assuming original columns might be different, explicitly rename/select
        # Adjust column names based on your EXACT Excel file headers if needed
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume'] # Standard names
        print("Data loaded successfully.")
        print(df.head())
        return df
    except FileNotFoundError:
        print(f"Error: Data file not found at {path}")
        return pd.DataFrame() # Return empty DataFrame on error
    except Exception as e:
        print(f"Error loading or processing data: {e}")
        return pd.DataFrame()


# Replace the previous strategy class with the new complex one
class TrendFilteredRSI(Strategy):
    """
    Combines RSI mean-reversion signals with an EMA trend filter and ATR stop-loss.
    (Integrated into the local file loading structure)
    """
    # Strategy Parameters
    rsi_period = 14
    ema_period = 200
    atr_period = 14
    oversold = 30
    overbought = 70
    exit_level = 50
    stop_loss_atr_multiplier = 2.0 # e.g., Stop Loss at 2 * ATR

    def init(self):
        # --- Indicators ---
        # Ensure data is available
        if self.data.Close.shape[0] < max(self.rsi_period, self.ema_period, self.atr_period):
             print("Warning: Not enough data points for indicator calculation during init.")
             # You might want to handle this more gracefully, maybe raise error or avoid calculation
             # For now, let 'ta' library handle potential NaN values initially

        # RSI
        self.rsi = self.I(ta.momentum.rsi, pd.Series(self.data.Close), window=self.rsi_period, name='RSI')

        # EMA Trend Filter
        self.ema_long = self.I(ta.trend.ema_indicator, pd.Series(self.data.Close), window=self.ema_period, name='EMA_Long')

        # ATR for Stop Loss calculation
        # Need High, Low, Close as pd.Series for ta.atr
        high_series = pd.Series(self.data.High)
        low_series = pd.Series(self.data.Low)
        close_series = pd.Series(self.data.Close)
        self.atr = self.I(ta.volatility.average_true_range, high_series, low_series, close_series, window=self.atr_period, name='ATR')

        print("Strategy Initialized with RSI, EMA, ATR indicators.")


    def next(self):
        # --- Current Market State ---
        # Access data for the current step correctly
        # Check if enough data points have passed for indicators to be valid
        # Using `len(self.data.Close)` checks total length up to current point
        if len(self.data.Close) < max(self.rsi_period, self.ema_period, self.atr_period):
             return # Skip bar if not enough history for all indicators

        current_price = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_ema = self.ema_long[-1]
        current_atr = self.atr[-1]

        # Check if indicators have calculated valid numbers
        if pd.isna(current_rsi) or pd.isna(current_ema) or pd.isna(current_atr) or current_atr <= 0:
            # print(f"Skipping bar {self.data.index[-1]}: Indicator values not ready (RSI={current_rsi}, EMA={current_ema}, ATR={current_atr})")
            return # Skip if any indicator is NaN or ATR is non-positive

        # --- Define Stop Loss Levels ---
        long_stop_loss = current_price - self.stop_loss_atr_multiplier * current_atr
        short_stop_loss = current_price + self.stop_loss_atr_multiplier * current_atr

        # --- Trading Logic ---

        # Conditions for Entry
        is_uptrend = current_price > current_ema
        is_downtrend = current_price < current_ema
        is_oversold = current_rsi < self.oversold
        is_overbought = current_rsi > self.overbought

        # Exit conditions (based on RSI crossing midpoint)
        # Check if RSI crosses the exit level using backtesting.lib.crossover
        rsi_crossed_above_exit = crossover(self.rsi, self.exit_level)
        rsi_crossed_below_exit = crossover(self.exit_level, self.rsi)

        # --- Execute Trades ---

        # No Position: Check for Entries
        if not self.position:
            if is_uptrend and is_oversold:
                # print(f"{self.data.index[-1]}: BUY signal - Uptrend & Oversold RSI ({current_rsi:.1f}). SL @ {long_stop_loss:.4f}")
                # Ensure stop loss is not negative or illogical
                if long_stop_loss < current_price:
                    self.buy(sl=long_stop_loss)
                else:
                    print(f"Warning: Illogical SL for Buy {long_stop_loss:.4f} vs Price {current_price:.4f}. Skipping trade.")
            elif is_downtrend and is_overbought:
                # print(f"{self.data.index[-1]}: SELL signal - Downtrend & Overbought RSI ({current_rsi:.1f}). SL @ {short_stop_loss:.4f}")
                 # Ensure stop loss is not illogical
                if short_stop_loss > current_price:
                    self.sell(sl=short_stop_loss)
                else:
                     print(f"Warning: Illogical SL for Sell {short_stop_loss:.4f} vs Price {current_price:.4f}. Skipping trade.")


        # Position Exists: Check for RSI-based Exit
        else:
            if self.position.is_long and rsi_crossed_above_exit:
                # print(f"{self.data.index[-1]}: CLOSE LONG signal - RSI ({current_rsi:.1f}) crossed above {self.exit_level}")
                self.position.close()
            elif self.position.is_short and rsi_crossed_below_exit:
                # print(f"{self.data.index[-1]}: CLOSE SHORT signal - RSI ({current_rsi:.1f}) crossed below {self.exit_level}")
                self.position.close()

            # Stop Loss is handled by backtesting.py framework automatically using the 'sl' parameter set during buy/sell


# Keep your original backtest execution function, but ensure it uses the NEW strategy
def run_backtest(data: pd.DataFrame):
    """
    Execute backtest using the TrendFilteredRSI strategy and display performance.
    (Using the local file loading structure)
    """
    if data.empty:
        print("Data is empty, cannot run backtest.")
        return

    print("\n--- Running Backtest with TrendFilteredRSI ---")
    bt = Backtest(
        data,
        TrendFilteredRSI, # USE THE NEW STRATEGY HERE
        cash=10000,
        commission=0.0, # Adjust commission if needed
        exclusive_orders=True
    )
    output = bt.run()
    print("Backtest Results:")
    # Print the specific metrics requested in the assignment
    print(output[['Win Rate [%]', 'Sharpe Ratio', 'Sortino Ratio', 'Max. Drawdown [%]',
                  'Calmar Ratio', 'Return [%]']])

    # Plotting (keep the try-except block from your original code)
    print("\nAttempting to generate plot...")
    try:
        bt.plot()
        print("Plot generated (check browser or notebook output).")
    except Exception as e:
        print(f"Could not generate plot: {e}")
        pass


# Keep your original main execution block using argparse
if __name__ == '__main__':
    # Use argparse to get the data file path from the command line
    parser = argparse.ArgumentParser(
        description='Backtest Trend-Filtered RSI strategy on EUR/USD Forex data.'
    )
    parser.add_argument(
        '--data', '-d',
        type=str,
        default='eurusd-forex-data.xlsx', # Default file name from your original code
        help='Path to the EUR/USD Excel data file.'
    )
    args = parser.parse_args()

    # Load data using your function
    df = load_data(args.data)

    # Run backtest if data was loaded successfully
    if not df.empty:
        run_backtest(df)
    else:
        print("Exiting due to data loading failure.")