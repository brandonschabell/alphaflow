# Getting Started

AlphaFlow was designed to be very easy to use, but offers a great deal of extensibility and additional complexity when needed.

Let's walk through an example of setting up a basic buy and hold strategy in which we will regularly rebalance our portfolio to maintain a 75%/25% split of Berkshire Hathaway stock (BRK-B) and bonds (BND).

## Creating a `flow`
The first step of running AlphaFlow is to create a `flow`. Think of a `flow` as the central hub of our backtest to which every component will be attached.

```python
import alphaflow as af

flow = af.AlphaFlow()
```
That's it! You're done with step 1.

## Customizing a `flow`
Before adding data or strategies, you'll want to set some of the most fundamental aspects of your backtest: your starting cash and the backtest time period. 

### Starting Cash
Setting the initial cash value of your backtest is quite simple.

```python
flow.set_cash(100000)  # Sets the initial portfolio cash to $100,000.
```

### Backtest Time Range
The time period you set is optional- if you omit a starting or ending date, you'll use as much data as your data source will give you. Let's limit the time period of our backtest for reproducibility's sake.

```python
flow.set_backtest_start_timestamp(datetime(2000, 1, 1))
flow.set_backtest_end_timestamp(datetime(2025, 1, 1))
```

### Adding a Benchmark
Benchmarking allows us to compare the performance of our strategy to another equity/ETF. Let's add `SPY` as a benchmark- this is a commonly used benchmark representing the performance of the S&P 500.

```python
flow.set_benchmark("SPY")
```

### Defining a Universe
Finally, we must define a universe of stocks. This represents the list of all stock tickers for which data should be pulled. Since we want to invest in Berkshire Hathaway (BRK-B) and bonds (BND), we will add both of these stock tickers to our universe. Note that `SPY` was automatically added to our universe when we set it as our benchmark.

```python
flow.add_equity("BRK-B")
flow.add_equity("BND")
```

## Adding a Data Source
Now that the basics of the `flow` have been configured, we're ready to add our data source. You are not limited to the number of data sources that you add. In fact, many complex strategies use dozens, if not hundreds of data sources! In our example, however, we only need a single source of data that yields market price information. A connection to [FinancialMarketingPrep](https://site.financialmodelingprep.com/)'s API is available through the `FMPDataFeed` class, although you'll need an [API key](https://site.financialmodelingprep.com/developer/docs) to actually pull data.

```python
from alphaflow.data_feeds import FMPDataFeed

flow.set_data_feed(FMPDataFeed(api_key="<USE YOUR API KEY HERE>"))
# The API key can also be set via environment variable:
# export FMP_API_KEY="<USE YOUR API KEY HERE>"
```

### Managing API Keys with .env Files
For better security and convenience, you can store your API keys in a `.env` file instead of hardcoding them. AlphaFlow automatically loads environment variables from a `.env` file in your project directory.

Create a `.env` file in your project directory:

```
FMP_API_KEY=your_actual_api_key_here
POLYGON_API_KEY=your_polygon_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

Then in your code, simply use:

```python
from alphaflow.data_feeds import FMPDataFeed

# API key will be loaded from .env automatically
flow.set_data_feed(FMPDataFeed())
```

!!! warning
    Never commit your `.env` file to version control! Add it to your `.gitignore` file.

### Other Data Feed Options
AlphaFlow supports multiple data providers:

- **PolygonDataFeed**: Real-time and historical data from [Polygon.io](https://polygon.io/)
- **AlphaVantageFeed**: Free market data from [Alpha Vantage](https://www.alphavantage.co/)
- **CSVDataFeed**: Load data from local CSV files for testing or custom data sources

Example using Polygon:

```python
from alphaflow.data_feeds import PolygonDataFeed

# Requires POLYGON_API_KEY in .env or environment
flow.set_data_feed(PolygonDataFeed())
```

## Add a Strategy
Just like with data sources, there are no limits to the number of strategies that you define. Each strategy is able to subscribe to any events required, and each can generate their own `OrderEvents`. For our example, however, we only need a simple `BuyAndHoldStrategy`. This strategy will look at the market value of your portfolio's positions, and will generate `OrderEvents` if it needs to rebalance your portfolio to maintain the specified distribution. Let's create a `BuyAndHoldStrategy` that maintains a portfolio comprised of 75% Berkshire Hathaway (BRK-B) and 25% bonds (BND).

```python
from alphaflow.strategies import BuyAndHoldStrategy

flow.add_strategy(
    BuyAndHoldStrategy(symbol="BRK-B", target_weight=0.75, min_dollar_delta=500, share_quantization=1),
)
flow.add_strategy(
    BuyAndHoldStrategy(symbol="BND", target_weight=0.25, min_dollar_delta=500, share_quantization=1),
)
```
Note the use of `share_quantization` and `min_dollar_delta` in the example above. `min_dollar_delta` prevents `OrderEvents` from being issued unless the difference in the actual position value and the target position value differ by at least this amount. In this example, we will only attempt a trade if the difference between our target position value and actual position value differ by at least $500. `share_quantization` is used to quantize the size of our orders. In our example, we set this value to 1 to prevent fractional share trades.

## Setting a Broker
A broker handles the trade execution. It receives `OrderEvents` from your strategies and decides if/when/how to place those orders. When it successfully executes a trade, it will generate a `FillEvent`. The broker is where you will set commissions, estimate fees, simulate slippage, etc. For our example, we can just use a `SimpleBroker` which executes trades as soon as it sees an `OrderEvent`.

```python
from alphaflow.brokers import SimpleBroker

flow.set_broker(SimpleBroker())
```

## Attach an Analyzer
An analyzer is used to evaluate the performance of our strategy. The `DefaultAnalyzer` will plot the performance of your strategy over time, along with the performance of the benchmark (SPY) that we set earlier. Additionally, it will display several metrics such as annualized return, Sharpe ratio, Sortino ratio, max drawdown, etc. You can build more sophisticated analyzers that subscribe to any event types that you'd like.

```python
from alphaflow.analyzers import DefaultAnalyzer

flow.add_analyzer(DefaultAnalyzer(plot_path="example_analysis.png", plot_title="Example Analysis"))
```

## Run the Backtest
We're all done setting up our backtest! Now all that's left to do is run it.

```python
flow.run()
```

## Putting it All Together
Here's a full working example of the backtest we just created.
```python
import os
from datetime import datetime

import alphaflow as af
from alphaflow.analyzers import DefaultAnalyzer
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import FMPDataFeed
from alphaflow.strategies import BuyAndHoldStrategy

# Set FinancialModelingPrep API key
os.environ["FMP_API_KEY"] = "<YOUR API KEY>"

# Create flow
flow = af.AlphaFlow()

# Set cash and backtest time period
flow.set_cash(100000)
flow.set_backtest_start_timestamp(datetime(2000, 1, 1))
flow.set_backtest_end_timestamp(datetime(2025, 1, 1))

# Set benchmark
flow.set_benchmark("SPY")

# Set universe
flow.add_equity("BRK-B")
flow.add_equity("BND")

# Add datafeed
flow.set_data_feed(FMPDataFeed())

# Add strategies
flow.add_strategy(
    BuyAndHoldStrategy(symbol="BRK-B", target_weight=0.75, min_dollar_delta=500, share_quantization=1),
)
flow.add_strategy(
    BuyAndHoldStrategy(symbol="BND", target_weight=0.25, min_dollar_delta=500, share_quantization=1),
)

# Set broker
flow.set_broker(SimpleBroker())

# Add analyzer
flow.add_analyzer(DefaultAnalyzer(plot_path="example_analysis.png", plot_title="Example Analysis"))

# Run backtest
flow.run()
```
