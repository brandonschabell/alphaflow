# AlphaFlow

[![CI](https://github.com/brandonschabell/alphaflow/actions/workflows/ci.yml/badge.svg)](https://github.com/brandonschabell/alphaflow/actions/workflows/ci.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/alphaflow.svg)](https://pypi.org/project/alphaflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AlphaFlow** is a Python-based, event-driven backtesting framework designed for professional-grade trading research and strategy development. By focusing on realism (partial fills, slippage, custom commissions) and a robust pub-sub architecture, AlphaFlow aims to provide a flexible, high-performance environment for quantitative analysts and algorithmic traders. 

> **Vision**: Offer a "batteries included" backtesting experience leveraging the simplicity of Python, while also enabling unlimited customization and optimization using an event-driven architecture that can support components written in any language.

---

## Table of Contents

1. [Key Features](#key-features)  
2. [Why AlphaFlow?](#why-alphaflow)  
3. [High-Level Architecture](#high-level-architecture)  
   - [EventBus (Pub-Sub)](#1-eventbus-pub-sub)  
   - [DataFeed](#2-datafeed)  
   - [Strategy](#3-strategy)  
   - [Broker (Execution Engine)](#4-broker-execution-engine)  
   - [Portfolio](#5-portfolio)  
   - [Analytics](#6-analytics)  
4. [Getting Started](#getting-started)  
5. [Contributing](#contributing)  
6. [License](#license)

---

## Key Features

- **Event-Driven Core**  
  Uses a **publish-subscribe (pub-sub)** architecture to simulate market data, order placements, and trade executions in a realistic, decoupled manner.  

- **Realistic Execution & Fill Logic**  
  - **Partial Fills**: Simulate large orders that fill over time.  
  - **Slippage Models**: Fixed or volume-based for more accurate PnL.  
  - **Custom Commissions**: Flat fees, per-share, tiered, or user-defined.  

- **Multi-Asset Support**  
  Initially focused on **stocks & ETFs** with daily or intraday data, but built to extend to futures, forex, cryptocurrencies, and **options** in future releases.

- **Performance-Oriented**  
  Planned message queue integration which will enable optimization of speed-critical components (like indicator calculations on large datasets).

- **Extendable & Modular**  
  - Swap out data sources (CSV, APIs, real-time feeds).  
  - Plugin-style architecture for custom brokers, strategies, analytics, and risk management.
  - Components are planned to be made language agnostic in a future release (v1).
  - A solid foundation for **live trading** integration in a future version (v1).

- **Professional-Grade Analytics**  
  - Built-in and user-defined performance metrics (Sharpe, Sortino, drawdown, custom risk models).  
  - Ongoing support for event-based analytics and reporting modules.

---

## Why AlphaFlow?

1. **Maintainable & Modern**  
   Many legacy libraries are no longer actively maintained or don’t follow best practices. AlphaFlow focuses on code quality, modular design, and clear APIs.

2. **Powerful & Future-Proof**  
   By embracing an **event-driven** architecture, you get fine-grained control over every aspect of your trading simulation. The transition to real-time or **live trading** is also more natural compared to purely vectorized solutions.

3. **Professional Realism**  
   Partial fills, slippage, and commission models ensure closer-to-reality simulation. Ideal for institutional or advanced retail traders needing robust prototyping.

4. **Performance Upgrades**  
   Future **Rust** integration will offload compute-heavy tasks, enabling large-scale backtests without major slowdowns or memory bottlenecks.

5. **Community & Extensibility**  
   Built to be **plugin-friendly**, allowing the community to add new data feeds, brokers, analytics modules, and advanced features without modifying the core.

---

## High-Level Architecture

### 1. EventBus (Pub-Sub)

- The **heart** of AlphaFlow.  
- Components (DataFeed, Strategy, Broker, Portfolio, Analytics) **subscribe** to and **publish** events.  
- Ensures a loose coupling: each module only needs to know how to react to specific event types.

### 2. DataFeed

- Responsible for providing market data (historical or real-time).  
- Publishes **MarketDataEvents** (price bars, ticks, earnings, news, etc.) to the EventBus.  
- Can support multiple timeframes (daily, intraday, tick data in v2).

### 3. Strategy

- Subscribes to **MarketDataEvents** from the DataFeed.  
- Generates trading signals and **publishes** `OrderEvents` to the Broker.  
- Can also subscribe to **Portfolio** updates if needed (to track position sizing, risk limits, etc.).

### 4. Broker (Execution Engine)

- Subscribes to `OrderEvents` from the Strategy.  
- Simulates **fills** (partial or full) and **slippage**, calculates commissions, and **publishes** `FillEvents`.  
- Centralizes order handling logic, making it easy to swap in a real-time broker later.

### 5. Portfolio

- Subscribes to `FillEvents` to track positions, cash balances, and profit/loss.  
- Optionally **publishes** portfolio updates (like margin calls, risk alerts) to other modules.

### 6. Analytics

- Subscribes to relevant events (MarketData, FillEvents, or PortfolioUpdates) to compile performance metrics, visualize PnL curves, or generate custom reports.  
- Encourages real-time or post-backtest reporting, ideal for quick iteration.

---

## Getting Started

1. **Install AlphaFlow**  
    ```bash
    pip install alphaflow
    ```

2. **Basic Example**  
    ```python
    from datetime import datetime

    import alphaflow as af

    # 1. Initialize AlphaFlow
    flow = af.AlphaFlow()
    flow.set_cash(100000)
    flow.set_backtest_start_timestamp(datetime(1990, 2, 10))
    flow.set_backtest_end_timestamp(datetime(2025, 1, 5))

    # 2. Create DataFeed (e.g., CSV-based daily bars)
    flow.set_data_feed(
        af.data_feeds.CSVDataFeed(
            file_path="historical_data.csv",
        )
    )

    # 3. Set Equity Universe
    flow.add_equity("BND")
    flow.add_equity("SPY")

    # 4. Initialize Strategy
    flow.add_strategy(
        af.strategies.BuyAndHoldStrategy(
            symbol="SPY",
            target_weight=0.9
        )
    )
    flow.add_strategy(
        af.strategies.BuyAndHoldStrategy(
            symbol="BND",
            target_weight=0.1
        )
    )

    # 5. Create Broker
    flow.set_broker(
        af.brokers.SimpleBroker()
    )

    # 6. Run the backtest
    flow.run()
    ```

3. **Monitor Results**  
   - Use built-in **analytics** or your own custom module to generate metrics and charts.  
   - Check logs to see partial fills, order details, and event flows.

---

## Contributing

We welcome contributions from the community! To get started:

1. **Fork** the repository and create a new branch.
2. **Implement** or **fix** a feature.
3. **Submit** a pull request describing your changes.

---

## License

AlphaFlow is released under the **MIT License**. See [LICENSE](./LICENSE) for details.

---

## Contact & Community

- **GitHub**: [github.com/brandonschabell/alphaflow](https://github.com/brandonschabell/alphaflow)

---

*Thank you for choosing AlphaFlow! We’re excited to see what you’ll build.*
