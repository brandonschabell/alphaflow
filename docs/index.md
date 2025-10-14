# Welcome to AlphaFlow

**AlphaFlow** is a Python-based, event-driven backtesting framework designed for professional-grade trading research and strategy development. Built on a robust pub-sub architecture, AlphaFlow provides a flexible, high-performance environment for quantitative analysts and algorithmic traders. 

> **Vision**: Offer a "batteries included" backtesting experience leveraging the simplicity of Python, while also enabling unlimited customization and optimization using an event-driven architecture that can support components written in any language.

## Key Features (v0.1.0)

  - **Event-Driven Core**  
    - Uses a **publish-subscribe (pub-sub)** architecture to simulate market data, order placements, and trade executions in a realistic, decoupled manner.
    - Priority-based event queue ensures proper chronological ordering of events.

  - **Commission Tracking**  
    - Built-in commission handling for realistic transaction costs.
    - Customizable broker implementations for different commission structures.

  - **Multi-Asset Support**  
    - Focused on **stocks & ETFs** with daily or intraday data.
    - Built to extend to futures, forex, cryptocurrencies, and **options** in future releases.

  - **Benchmark Comparison**  
    - Compare strategy performance against market benchmarks (e.g., SPY for S&P 500).
    - Side-by-side performance visualization.

  - **Extendable & Modular**  
    - Swap out data sources (CSV, Alpha Vantage API, Financial Modeling Prep API, or build your own).
    - Plugin-style architecture for custom brokers, strategies, analytics, and risk management.
    - Components are planned to be made language agnostic in a future release (v1).
    - A solid foundation for **live trading** integration in a future version (v1).

  - **Professional-Grade Analytics**  
    - Built-in performance metrics: Sharpe ratio, Sortino ratio, maximum drawdown, annualized returns.
    - Customizable analytics modules for specialized reporting.

## Coming in Future Releases

  - **v0.2**: Slippage models, partial fills, basic technical indicators
  - **v0.3**: Multiple timeframes, earnings/news events
  - **v0.4**: Advanced risk management tools
  - **v0.5**: Live trading integration
  - **v1.0**: Performance optimization with Rust components

---

## Why AlphaFlow?

1. **Maintainable & Modern**  
   Many legacy libraries are no longer actively maintained or don’t follow best practices. AlphaFlow focuses on code quality, modular design, and clear APIs.

2. **Powerful & Future-Proof**  
   By embracing an **event-driven** architecture, you get fine-grained control over every aspect of your trading simulation. The transition to real-time or **live trading** is also more natural compared to purely vectorized solutions.

3. **Commission-Aware Backtesting**  
   Built-in commission tracking ensures realistic transaction costs are accounted for in your strategy performance.

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

