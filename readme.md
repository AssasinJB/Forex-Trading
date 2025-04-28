# %% [markdown]
# Quant Developer Submission: EUR/USD RSI Mean Reversion Strategy

**Objective:**
Implement a mean-reversion trading strategy on EUR/USD using the Relative Strength Index (RSI) and backtest its performance with key metrics.

**Dataset:**
Daily EUR/USD from 2005 to present (no external data files in submission).

**Assumptions:**
- Trading on close price at end of each day.
- No transaction costs/slippage.
- Position sizing: fixed 1 unit per trade.

# %% [markdown]
## 1. Environment Setup

Install required libraries:

```bash
pip install backtesting pandas ta
```


# %%
# Imports
define_imports = '''
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import ta
'''
print(define_imports)

# %% [markdown]
## 2. Load Data

Read the provided Excel file into a pandas DataFrame and preprocess it.

# %%
load_data = '''
# Load data (ensure eurusd-forex-data.xlsx is in working directory)
df = pd.read_excel('eurusd-forex-data.xlsx', parse_dates=['Timestamp'])
df.set_index('Timestamp', inplace=True)

# Rename columns to lowercase
df.columns = [c.lower() for c in df.columns]
# Show head
print(df.head())
'''
print(load_data)

# %% [markdown]
## 3. Strategy Definition

Use RSI (14) for mean-reversion:
- **Long** when RSI < 30 (oversold)
- **Exit Long** when RSI > 50
- **Short** when RSI > 70 (overbought)
- **Exit Short** when RSI < 50

# %%
define_strategy = '''
class RSIMeanReversion(Strategy):
    rsi_period = 14
    oversold = 30
    overbought = 70
    exit_level = 50

    def init(self):
        # Compute RSI indicator
        price = self.data.Close
        self.rsi = self.I(ta.momentum.rsi, price, self.rsi_period)

    def next(self):
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
'''
print(define_strategy)

# %% [markdown]
## 4. Backtesting and Performance Metrics

Run the backtest and compute Win Rate, Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio, CAGR.

# %%
backtest_code = '''
# Initialize backtest
bt = Backtest(df, RSIMeanReversion, cash=10000, commission=0)

# Run
stats = bt.run()
print(stats)

# Plot equity curve
bt.plot()  # Comment this out if running headless
'''
print(backtest_code)

# %% [markdown]
## 5. Results and Interpretation

Add commentary on key metrics and possible improvements (e.g., transaction costs, stop-losses, parameter optimization).

# %% [markdown]
**Notes:**
- You may optimize parameters using `bt.optimize()`.
- Consider adding a volatility filter or ATR-based stop-loss for risk management.
