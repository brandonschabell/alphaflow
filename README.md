# AlphaFlow

**AlphaFlow** is a Python-based, event-driven backtesting framework designed for professional-grade trading research and strategy development. By focusing on realism (partial fills, slippage, custom commissions) and a robust pub-sub architecture, AlphaFlow aims to provide a flexible, high-performance environment for quantitative analysts and algorithmic traders. 

> **Vision**: Combine Pythonic ease of use with modern software engineering principles and optional Rust-based optimizations to handle large-scale data and complex trading logic—without sacrificing maintainability.

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
5. [Roadmap](#roadmap)  
6. [Contributing](#contributing)  
7. [License](#license)

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
  Planned **Rust** integration for speed-critical components (like indicator calculations on large datasets).

- **Extendable & Modular**  
  - Swap out data sources (CSV, APIs, real-time feeds).  
  - Plugin-style architecture for custom brokers, strategies, analytics, and risk management.  
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
   \```bash
   pip install alphaflow
   \```

2. **Basic Example**  
   ```python
   import alphaflow as af

   # 1. Initialize EventBus
   event_bus = af.EventBus()

   # 2. Create DataFeed (e.g., CSV-based daily bars)
   data_feed = af.datafeeds.CSVDataFeed(
       file_path="historical_data.csv",
       event_bus=event_bus
   )

   # 3. Initialize Strategy
   strategy = af.strategies.SimpleMovingAverageStrategy(
       event_bus=event_bus,
       short_window=10,
       long_window=30
   )

   # 4. Create Broker
   broker = af.brokers.SimulatedBroker(
       event_bus=event_bus,
       slippage_model=af.slippage.FixedSlippage(0.02),
       commission_model=af.commissions.PerShare(0.005)
   )

   # 5. Initialize Portfolio
   portfolio = af.portfolio.Portfolio(
       event_bus=event_bus,
       initial_cash=100000
   )

   # 6. Run the backtest
   data_feed.run()   # This drives events into the system
   ```

3. **Monitor Results**  
   - Use built-in **analytics** or your own custom module to generate metrics and charts.  
   - Check logs to see partial fills, order details, and event flows.

---

## Roadmap

- **v0.1 (MVP)**  
  - Basic event-driven backtest engine with daily/intraday data.  
  - Core modules (DataFeed, Strategy, Broker, Portfolio, Analytics).  

- **v0.2**  
  - Slippage & commission models.

- **v0.3**  
  - Add advanced features: multiple timeframes, earnings/news events.  

- **v0.4**
  - Additional analytics & risk management tools.

- **v0.5**
  - **Live Trading** integration with a real-time broker plugin.

- **v1.0**
  - Performance optimization and bug fixes.

- **v1.x**
  - Support for additional asset classes (futures, forex, crypto, options).

- **v2.0**  
  - **Rust** acceleration for computationally heavy tasks (indicators, large datasets).  

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
