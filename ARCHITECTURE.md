# Poly-Maker: Automated Market Making Bot for Polymarket

> Complete documentation for understanding, operating, and extending the poly-maker trading bot.

---

## Table of Contents

1. [What This Bot Does](#what-this-bot-does)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [System Architecture](#system-architecture)
5. [Entry Points](#entry-points)
6. [Module Reference](#module-reference)
7. [Configuration](#configuration)
8. [Data Flow](#data-flow)
9. [Trading Logic](#trading-logic)
10. [For Future Developers](#for-future-developers)

---

## What This Bot Does

**Poly-Maker** is an automated market-making bot for [Polymarket](https://polymarket.com), a prediction market platform on Polygon blockchain.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Market Making** | Places bid/ask orders on prediction markets to earn spread + maker rewards |
| **Real-time Trading** | Uses WebSockets for instant order book updates and trade execution |
| **Position Management** | Tracks positions, calculates PnL, manages exposure across markets |
| **Risk Management** | Stop-loss triggers, volatility checks, position limits, risk-off periods |
| **Position Merging** | Automatically merges opposing YES/NO positions to recover USDC |
| **Market Discovery** | Scans all markets hourly to find high-reward opportunities |

### How Market Making Works

1. **Provide Liquidity**: Place buy orders below mid-price, sell orders above
2. **Earn Spread**: Profit from the difference between buy and sell prices
3. **Earn Rewards**: Polymarket pays daily USDC rewards to liquidity providers
4. **Manage Risk**: Close positions when volatility spikes or PnL drops

---

## Quick Start

### Prerequisites

```bash
# Python 3.10+
pip install -r requirements.txt

# Node.js (for position merging)
cd merger && npm install
```

### Environment Variables (.env)

```env
PK=your_private_key_here
BROWSER_ADDRESS=your_gnosis_safe_address
```

### Run the Bot

```bash
# Main market maker (runs continuously)
python main.py

# Market scanner (run separately, updates hourly)
python update_markets.py

# Account stats (run separately, updates every 3 hours)
python update_stats.py
```

---

## Project Structure

```
poly-maker/
│
├── main.py                 # 🚀 Main entry - runs the market maker
├── update_markets.py       # 📊 Market scanner - finds profitable markets
├── update_stats.py         # 📈 Account statistics collector
│
├── config/                 # Configuration files
│   ├── markets.json        # Markets you want to trade (edit this!)
│   ├── params.json         # Trading parameters (stop-loss, etc.)
│   ├── all_markets.json    # All available markets (auto-generated)
│   ├── volatility_markets.json  # Low-volatility markets (auto-generated)
│   ├── full_markets.json   # Complete market data (auto-generated)
│   └── account_summary.json     # Account stats (auto-generated)
│
├── src/                    # Source code modules
│   ├── core/               # Core client and state
│   │   ├── polymarket_client.py  # API + blockchain client
│   │   ├── global_state.py       # Shared application state
│   │   └── CONSTANTS.py          # System constants
│   │
│   ├── trading/            # Trading engine
│   │   ├── trading.py            # Main trading logic
│   │   └── trading_utils.py      # Price calculation helpers
│   │
│   ├── data/               # Data processing
│   │   ├── websocket_handlers.py # WebSocket connections
│   │   ├── data_processing.py    # Process incoming data
│   │   └── data_utils.py         # Position/order CRUD
│   │
│   ├── utils/              # Shared utilities
│   │   ├── utils.py              # JSON loading, config
│   │   ├── abis.py               # Smart contract ABIs
│   │   └── erc20ABI.json         # ERC-20 ABI file
│   │
│   ├── updater/            # Market discovery
│   │   ├── find_markets.py       # Market analysis
│   │   └── updater_utils.py      # API client helpers
│   │
│   └── stats/              # Statistics
│       └── account_stats.py      # Account performance
│
├── merger/                 # Position merging (Node.js)
│   ├── merge.js            # Main merge script
│   ├── safe-helpers.js     # Gnosis Safe transaction helpers
│   ├── safeAbi.js          # Safe contract ABI
│   └── package.json        # Node dependencies
│
└── positions/              # Runtime data (auto-created)
    └── {market_id}.json    # Risk-off timestamps per market
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS                             │
├───────────────────┬───────────────────┬─────────────────────────┤
│     main.py       │ update_markets.py │    update_stats.py      │
│  (Market Maker)   │ (Market Scanner)  │   (Statistics)          │
│   Runs 24/7       │   Hourly          │   Every 3 hours         │
└────────┬──────────┴─────────┬─────────┴────────────┬────────────┘
         │                    │                      │
         ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SRC MODULES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │  src/core/  │   │src/trading/ │   │     src/data/       │   │
│  │             │   │             │   │                     │   │
│  │ • Client    │◄──│ • Strategy  │◄──│ • WebSocket handlers│   │
│  │ • State     │   │ • Orders    │   │ • Data processing   │   │
│  │ • Constants │   │ • Risk mgmt │   │ • Position tracking │   │
│  └─────────────┘   └─────────────┘   └─────────────────────┘   │
│         │                                       │                │
│         ▼                                       ▼                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │ src/utils/  │   │src/updater/ │   │    src/stats/       │   │
│  │             │   │             │   │                     │   │
│  │ • Config    │   │ • Scanner   │   │ • Account stats     │   │
│  │ • ABIs      │   │ • Volatility│   │ • Earnings          │   │
│  └─────────────┘   └─────────────┘   └─────────────────────┘   │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  Polymarket API │  │ Polygon Blockchain│  │  merger/       │  │
│  │                 │  │                   │  │  (Node.js)     │  │
│  │ • CLOB API      │  │ • Web3 RPC        │  │                │  │
│  │ • WebSocket     │  │ • Smart Contracts │  │ • Gnosis Safe  │  │
│  │ • Rewards API   │  │ • USDC, CTF       │  │ • Merge txns   │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Entry Points

### 1. `main.py` - The Market Maker (Primary)

**Purpose**: Runs the automated market making bot continuously.

**What it does**:
1. Initializes `PolymarketClient` (API + blockchain connections)
2. Loads market config from `config/markets.json`
3. Fetches current positions and orders from Polymarket
4. Starts background thread for periodic updates (every 5s)
5. Connects to WebSockets for real-time market data
6. Triggers `perform_trade()` on every order book update

**Execution Flow**:
```
main.py
   │
   ├── PolymarketClient() ──► Connect to API + Polygon
   │
   ├── update_once()
   │   ├── update_markets() ──► Load config/markets.json
   │   ├── update_positions() ──► Fetch positions from API
   │   └── update_orders() ──► Fetch open orders
   │
   ├── Thread: update_periodically()
   │   └── Every 5s: refresh positions, orders, markets
   │
   └── async main loop
       ├── connect_market_websocket() ──► Order book updates
       └── connect_user_websocket() ──► Trade confirmations
                │
                ▼
           perform_trade() ──► Place/update orders
```

---

### 2. `update_markets.py` - Market Scanner

**Purpose**: Discovers profitable markets and calculates volatility metrics.

**Run frequency**: Every hour (runs in infinite loop)

**What it does**:
1. Fetches ALL markets from Polymarket API
2. Calculates maker rewards for each market
3. Fetches price history and calculates volatility
4. Saves results to JSON files

**Output files**:
- `config/all_markets.json` - All markets sorted by reward
- `config/volatility_markets.json` - Low-volatility markets only
- `config/full_markets.json` - Complete market data

---

### 3. `update_stats.py` - Account Statistics

**Purpose**: Tracks account performance and earnings.

**Run frequency**: Every 3 hours

**What it does**:
1. Fetches current positions and orders
2. Fetches maker rewards earned
3. Combines into summary report
4. Saves to `config/account_summary.json`

---

## Module Reference

### src/core/ - Core Infrastructure

#### `polymarket_client.py`

The main client class for interacting with Polymarket.

```python
class PolymarketClient:
    """
    Handles all API and blockchain interactions.
    
    Connections:
    - Polymarket CLOB API (orders, positions)
    - Polygon RPC (balances, contract calls)
    - Gnosis Safe (via merger/ for position merging)
    """
```

| Method | Description |
|--------|-------------|
| `create_order(token, side, price, size, neg_risk)` | Place a new order |
| `get_order_book(market)` | Get current bids/asks |
| `get_position(tokenId)` | Get token balance from blockchain |
| `get_all_positions()` | Get all positions via API |
| `get_all_orders()` | Get all open orders |
| `cancel_all_asset(token)` | Cancel all orders for a token |
| `cancel_all_market(market)` | Cancel all orders in a market |
| `merge_positions(amount, condition_id, is_neg_risk)` | Merge YES+NO positions |
| `get_usdc_balance()` | Get USDC balance |
| `get_total_balance()` | Get total account value |

---

#### `global_state.py`

Centralized state management - all modules share this state.

```python
# Market Data
all_tokens = []          # List of tokens being tracked
REVERSE_TOKENS = {}      # Maps token1 <-> token2
all_data = {}            # Order book data per market
df = None                # Market config DataFrame

# Client & Params
client = None            # PolymarketClient instance
params = {}              # Trading hyperparameters

# Trading State
orders = {}              # Current open orders
positions = {}           # Current positions
performing = {}          # Trades in progress (matched but not confirmed)
performing_timestamps = {}  # When trades were matched
last_trade_update = {}   # Last position update time
lock = threading.Lock()  # Thread safety
```

---

#### `CONSTANTS.py`

System-wide constants.

```python
MIN_MERGE_SIZE = 20  # Minimum position size to trigger merging
```

---

### src/trading/ - Trading Engine

#### `trading.py`

The core trading logic - this is where all decisions are made.

| Function | Description |
|----------|-------------|
| `send_buy_order(order)` | Place a buy order with smart cancellation |
| `send_sell_order(order)` | Place a sell order with smart cancellation |
| `perform_trade(market)` | Main trading function - called on every update |

**`perform_trade()` Logic**:
1. Get market config and parameters
2. Check for mergeable positions (YES + NO)
3. For each outcome (token1, token2):
   - Get order book depth
   - Calculate optimal bid/ask prices
   - Check current position size
   - **SELL logic**: Stop-loss, take-profit
   - **BUY logic**: Position building with risk checks

---

#### `trading_utils.py`

Helper functions for price calculations.

| Function | Description |
|----------|-------------|
| `get_best_bid_ask_deets(market, name, size)` | Get order book depth analysis |
| `find_best_price_with_size(prices, min_size)` | Find price level with enough liquidity |
| `get_order_prices(bid, ask, avgPrice, row)` | Calculate optimal order prices |
| `get_buy_sell_amount(position, price, row)` | Determine buy/sell quantities |
| `round_down(number, decimals)` | Floor rounding |
| `round_up(number, decimals)` | Ceiling rounding |

---

### src/data/ - Data Processing

#### `websocket_handlers.py`

Manages WebSocket connections to Polymarket.

| Function | Description |
|----------|-------------|
| `connect_market_websocket(tokens)` | Subscribe to order book updates |
| `connect_user_websocket()` | Subscribe to user trade/order updates |

---

#### `data_processing.py`

Processes incoming WebSocket data.

| Function | Description |
|----------|-------------|
| `process_book_data(asset, data)` | Store full order book snapshot |
| `process_price_change(asset, side, price, size)` | Update single price level |
| `process_data(json_data)` | Route market updates → trigger trading |
| `process_user_data(rows)` | Handle trade/order confirmations |
| `add_to_performing(col, id)` | Track matched trades |
| `remove_from_performing(col, id)` | Clear confirmed trades |

---

#### `data_utils.py`

CRUD operations for positions and orders.

| Function | Description |
|----------|-------------|
| `update_markets()` | Load config from JSON files |
| `update_positions(avgOnly)` | Fetch positions from API |
| `update_orders()` | Fetch orders from API |
| `get_position(token)` | Get local position state |
| `set_position(token, side, size, price)` | Update local position |
| `get_order(token)` | Get local order state |
| `set_order(token, side, size, price)` | Update local order |

---

### src/utils/ - Utilities

#### `utils.py`

Configuration and JSON helpers.

| Function | Description |
|----------|-------------|
| `load_config()` | Load markets.json + params.json |
| `load_json(filename)` | Load any JSON from config/ |
| `save_to_json(data, filename)` | Save data to config/ |
| `pretty_print(txt, dic)` | Debug printing |

---

#### `abis.py`

Smart contract ABIs for blockchain interactions.

- `erc20_abi` - Standard ERC-20 (USDC)
- `NegRiskAdapterABI` - Negative risk position merging
- `ConditionalTokenABI` - Position queries

---

### src/updater/ - Market Discovery

#### `find_markets.py`

Scans and analyzes all Polymarket markets.

| Function | Description |
|----------|-------------|
| `get_all_markets(client)` | Fetch all markets via pagination |
| `process_single_row(row, client)` | Analyze one market |
| `get_all_results(df, client)` | Process all markets in parallel |
| `add_volatility_to_df(df)` | Calculate price volatility |
| `get_markets(results, sel_df)` | Filter by reward threshold |
| `calculate_annualized_volatility(df, hours)` | Volatility calculation |

---

#### `updater_utils.py`

Utility functions for market updates.

| Function | Description |
|----------|-------------|
| `get_clob_client()` | Initialize Polymarket API client |
| `approveContracts()` | Approve USDC/CTF for trading |

---

### src/stats/ - Statistics

#### `account_stats.py`

Account performance tracking.

| Function | Description |
|----------|-------------|
| `get_markets_df()` | Load all markets data |
| `get_selected_df()` | Load selected markets |
| `get_all_orders(client)` | Format current orders |
| `get_all_positions(client)` | Format current positions |
| `get_earnings(client)` | Fetch maker rewards |
| `combine_dfs(...)` | Merge data into report |
| `update_stats_once(client)` | Main stats function |

---

### merger/ - Position Merging (Node.js)

When you hold both YES and NO positions in the same market, you can merge them to recover USDC. This is handled by Node.js because it requires Gnosis Safe transaction signing.

#### `merge.js`

```bash
node merger/merge.js <amount> <conditionId> <isNegRisk>
```

Calls either:
- `negRiskAdapter.mergePositions()` for neg-risk markets
- `conditionalTokens.mergePositions()` for regular markets

#### `safe-helpers.js`

Handles Gnosis Safe transaction signing and execution.

---

## Configuration

### `config/markets.json` - Markets to Trade

```json
{
  "markets": [
    {
      "question": "Will X happen?",
      "answer1": "Yes",
      "answer2": "No",
      "token1": "123...",
      "token2": "456...",
      "condition_id": "0x...",
      "tick_size": 0.01,
      "min_size": 5,
      "trade_size": 20,
      "max_size": 100,
      "max_spread": 3,
      "neg_risk": "FALSE",
      "param_type": "default",
      "best_bid": 0.45,
      "best_ask": 0.55,
      "3_hour": 5.2
    }
  ]
}
```

**Key fields**:
- `trade_size`: How much to quote per order
- `max_size`: Maximum position per side
- `max_spread`: Maximum spread for rewards (from Polymarket)
- `param_type`: Which parameter set to use (default, high, mid, etc.)

---

### `config/params.json` - Trading Parameters

```json
{
  "default": {
    "stop_loss_threshold": -5,
    "take_profit_threshold": 3,
    "spread_threshold": 0.02,
    "volatility_threshold": 10,
    "sleep_period": 2
  },
  "high": {
    "stop_loss_threshold": -8,
    ...
  }
}
```

**Parameters**:
- `stop_loss_threshold`: PnL % to trigger stop-loss
- `take_profit_threshold`: PnL % for take-profit pricing
- `spread_threshold`: Max spread to allow stop-loss exit
- `volatility_threshold`: Max 3-hour volatility to trade
- `sleep_period`: Hours to wait after stop-loss

---

## Data Flow

### 1. Startup Flow

```
main.py starts
    │
    ├── Create PolymarketClient
    │   ├── Connect to Polymarket API
    │   ├── Connect to Polygon RPC
    │   └── Set up contract interfaces
    │
    ├── update_markets()
    │   ├── Load config/markets.json
    │   ├── Populate global_state.df
    │   ├── Build REVERSE_TOKENS mapping
    │   └── Initialize all_tokens list
    │
    ├── update_positions()
    │   └── Fetch positions → global_state.positions
    │
    └── update_orders()
        └── Fetch orders → global_state.orders
```

### 2. Real-time Trading Flow

```
WebSocket receives order book update
    │
    ▼
process_data(json_data)
    │
    ├── Update global_state.all_data[market]
    │
    └── asyncio.create_task(perform_trade(market))
            │
            ▼
        perform_trade(market)
            │
            ├── Check for mergeable positions
            │   └── If YES+NO > MIN_MERGE_SIZE → merge_positions()
            │
            └── For each token (YES, NO):
                │
                ├── get_best_bid_ask_deets() → analyze order book
                ├── get_order_prices() → calculate bid/ask
                ├── get_buy_sell_amount() → determine quantities
                │
                ├── SELL LOGIC:
                │   ├── Check PnL vs stop_loss_threshold
                │   ├── Check volatility
                │   └── send_sell_order() or take-profit
                │
                └── BUY LOGIC:
                    ├── Check position < max_size
                    ├── Check risk-off period
                    ├── Check volatility
                    └── send_buy_order()
```

### 3. User Trade Confirmation Flow

```
WebSocket receives trade update
    │
    ▼
process_user_data(rows)
    │
    ├── status == 'MATCHED'
    │   ├── add_to_performing(col, trade_id)
    │   ├── set_position() → update local position
    │   └── perform_trade() → check for more opportunities
    │
    ├── status == 'CONFIRMED'
    │   ├── remove_from_performing(col, trade_id)
    │   └── perform_trade() → re-evaluate
    │
    └── status == 'FAILED'
        └── update_positions() → refresh from API
```

---

## Trading Logic

### Position Building

1. **Entry**: Buy up to `trade_size` at best bid + tick_size
2. **Accumulate**: Keep buying until position = `max_size`
3. **Quote Both Sides**: Always have sell orders at take-profit price

### Risk Management

1. **Stop-Loss**: Sell at market if PnL < `stop_loss_threshold` AND spread ≤ `spread_threshold`
2. **Volatility Exit**: Cancel all orders if 3-hour volatility > `volatility_threshold`
3. **Risk-Off Period**: After stop-loss, don't buy for `sleep_period` hours
4. **Position Limits**: Never exceed `max_size` per side, 250 absolute cap

### Position Merging

When you hold both YES and NO:
- Example: 100 YES + 100 NO = 100 USDC (minus fees)
- Triggered when both positions > `MIN_MERGE_SIZE` (20)
- Executed via Node.js → Gnosis Safe transaction

---

## For Future Developers

### Adding a New Market

1. Run `update_markets.py` to refresh market data
2. Find your market in `config/all_markets.json` or `config/volatility_markets.json`
3. Copy the market entry to `config/markets.json` under `"markets": []`
4. Set your preferred `trade_size`, `max_size`, and `param_type`
5. Restart `main.py`

### Modifying Trading Strategy

1. Edit `src/trading/trading.py` → `perform_trade()` function
2. Adjust parameters in `config/params.json`
3. Key areas to customize:
   - Stop-loss logic (lines ~285-320)
   - Buy conditions (lines ~340-420)
   - Take-profit pricing (lines ~430-460)

### Adding New Risk Checks

1. Add to `config/params.json` under each profile
2. Access in trading.py via `params['your_new_param']`
3. Implement check in the BUY or SELL logic blocks

### Common Issues

| Issue | Solution |
|-------|----------|
| "Import could not be resolved" | Run from project root, ensure `__init__.py` exists |
| WebSocket disconnects | Normal - auto-reconnects after 5 seconds |
| Orders not placing | Check USDC balance, contract approvals |
| Merge failing | Ensure Node.js installed, run `npm install` in merger/ |

### Key Files to Understand First

1. `main.py` - Entry point and main loop
2. `src/trading/trading.py` - All trading decisions
3. `src/core/global_state.py` - Shared state structure
4. `config/markets.json` - What you're trading
5. `config/params.json` - How aggressively

---

## License

See LICENSE file.
