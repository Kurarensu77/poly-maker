> [!WARNING]
> In today's market, this bot is not profitable and will lose money. Use it as a reference implementation for building your own market making strategies, not as a ready-to-deploy solution. Given the increased competition on Polymarket, I don't see a point in playing with this unless you're willing to dedicate a significant amount of time.
 
# Poly-Maker

A market making bot for Polymarket prediction markets. This bot automates the process of providing liquidity to markets on Polymarket by maintaining orders on both sides of the book with configurable parameters. A summary of my experience running this bot is available [here](https://x.com/defiance_cr/status/1906774862254800934)

## Overview

Poly-Maker is a comprehensive solution for automated market making on Polymarket. It includes:

- Real-time order book monitoring via WebSockets
- Position management with risk controls
- Customizable trade parameters fetched from Google Sheets
- Automated position merging functionality
- Sophisticated spread and price management

## Structure

The repository consists of several interconnected modules:

- `poly_data`: Core data management and market making logic
- `poly_merger`: Utility for merging positions (based on open-source Polymarket code)
- `poly_stats`: Account statistics tracking
- `poly_utils`: Shared utility functions
- `data_updater`: Separate module for collecting market information

## Requirements

- Python 3.9.10 or higher
- Node.js (for poly_merger)
- Google Sheets API credentials
- Polymarket account and API credentials

## Installation

This project uses UV for fast, reliable package management.

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Install Dependencies

```bash
# Install all dependencies
uv sync

# Install with development dependencies (black, pytest)
uv sync --extra dev
```

### Quick Start

```bash
# Run the market maker (recommended)
uv run python main.py

# Update market data
uv run python update_markets.py

# Update statistics
uv run python update_stats.py
```

### Setup Steps

#### 1. Clone the repository

```bash
git clone https://github.com/yourusername/poly-maker.git
cd poly-maker
```

#### 2. Install Python dependencies

```bash
uv sync
```

#### 3. Install Node.js dependencies for the merger

```bash
cd poly_merger
npm install
cd ..
```

#### 4. Set up environment variables

```bash
cp .env.example .env
```

#### 5. Configure your credentials in `.env`

Edit the `.env` file with your credentials:
- `PK`: Your private key for Polymarket
- `BROWSER_ADDRESS`: Your wallet address

**Important:** Make sure your wallet has done at least one trade through the UI so that the permissions are proper.

#### 6. Configure markets

Edit the JSON config files in the `config/` directory:
- `config/markets.json` - Add markets you want to trade
- `config/params.json` - Configure trading parameters (hyperparameters)

#### 7. Update market data (optional)

Run the market data updater to fetch all available markets:

```bash
python update_markets.py
```

This fetches market data and saves to `config/all_markets.json` and `config/volatility_markets.json`.

#### 8. Start the market making bot

```bash
python main.py
```

## Configuration

The bot is configured via JSON files in the `config/` directory:

- **markets.json**: Markets you want to trade (selected markets)
- **params.json**: Trading parameters/hyperparameters (default, high, mid, etc.)
- **all_markets.json**: All markets from Polymarket (auto-updated by update_markets.py)
- **volatility_markets.json**: Low volatility markets (auto-updated)
- **full_markets.json**: Full market data (auto-updated)
- **account_summary.json**: Your orders/positions/earnings (auto-updated by update_stats.py)


## Poly Merger

The `poly_merger` module is a particularly powerful utility that handles position merging on Polymarket. It's built on open-source Polymarket code and provides a smooth way to consolidate positions, reducing gas fees and improving capital efficiency.

## Important Notes

- This code interacts with real markets and can potentially lose real money
- Test thoroughly with small amounts before deploying with significant capital
- The `data_updater` is technically a separate repository but is included here for convenience

## License

MIT
