"""
Crypto Markets Updater
Fetches active crypto up/down markets (15m, hourly, daily) and saves to crypto_markets.json
"""

import requests
import time
import datetime
import pytz
from src.utils.utils import save_to_json

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

# Crypto assets to track
CRYPTO_ASSETS = ['bitcoin', 'solana', 'xrp', 'eth', 'dogecoin']

# Timeframes: slug pattern and hours to look ahead
TIMEFRAMES = {
    'hourly': {'hours_ahead': 24, 'interval_hours': 1},
    '15m': {'hours_ahead': 6, 'interval_hours': 0.25},  # 15 min = 0.25 hours
    'daily': {'hours_ahead': 7*24, 'interval_hours': 24},  # 7 days ahead
}


def generate_hourly_slug(asset, target_time):
    """Generate slug for hourly markets like: bitcoin-up-or-down-january-31-3pm-et"""
    et_tz = pytz.timezone('US/Eastern')
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(et_tz)
    else:
        target_time = target_time.astimezone(et_tz)
    
    month = target_time.strftime("%B").lower()
    day = target_time.day
    hour_int = int(target_time.strftime("%I"))
    am_pm = target_time.strftime("%p").lower()
    
    return f"{asset}-up-or-down-{month}-{day}-{hour_int}{am_pm}-et"


def generate_daily_slug(asset, target_date):
    """Generate slug for daily markets like: bitcoin-up-or-down-on-january-31"""
    et_tz = pytz.timezone('US/Eastern')
    if hasattr(target_date, 'astimezone'):
        target_date = target_date.astimezone(et_tz)
    month = target_date.strftime("%B").lower()
    day = target_date.day
    return f"{asset}-up-or-down-on-{month}-{day}"


def generate_15m_slug(asset, target_time):
    """
    Generate slug for 15m markets using Unix timestamp.
    Format: btc-updown-15m-{unix_timestamp}
    Asset mapping: bitcoin->btc, ethereum->eth, solana->sol, xrp->xrp
    """
    # Map full asset names to short codes
    asset_map = {
        'bitcoin': 'btc',
        'ethereum': 'eth', 
        'solana': 'sol',
        'xrp': 'xrp',
        'eth': 'eth',
        'sol': 'sol',
        'btc': 'btc',
    }
    short_asset = asset_map.get(asset.lower(), asset.lower())
    
    # Round to nearest 15 minutes and get Unix timestamp
    minute = (target_time.minute // 15) * 15
    rounded_time = target_time.replace(minute=minute, second=0, microsecond=0)
    unix_ts = int(rounded_time.timestamp())
    
    return f"{short_asset}-updown-15m-{unix_ts}"


def get_orderbook(token_id):
    """Get best bid/ask from CLOB orderbook"""
    try:
        r = requests.get(f"{CLOB_API}/book", params={'token_id': token_id})
        r.raise_for_status()
        data = r.json()
        
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        best_bid = max(float(b['price']) for b in bids) if bids else 0
        best_ask = min(float(a['price']) for a in asks) if asks else 0
        
        return best_bid, best_ask
    except Exception as e:
        return 0, 0


def process_event(event):
    """Process a single event into market data"""
    markets_data = []
    
    for market in event.get('markets', []):
        if not market.get('active') or market.get('closed'):
            continue
            
        try:
            # Parse token IDs
            clob_token_ids = eval(market.get('clobTokenIds', '[]'))
            outcomes = eval(market.get('outcomes', '[]'))
            
            if len(clob_token_ids) != 2 or len(outcomes) != 2:
                continue
            
            token1, token2 = clob_token_ids
            answer1, answer2 = outcomes
            
            # Get orderbook data
            best_bid_1, best_ask_1 = get_orderbook(token1)
            best_bid_2, best_ask_2 = get_orderbook(token2)
            
            # Use the first token's orderbook for primary pricing
            best_bid = best_bid_1
            best_ask = best_ask_1
            spread = best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0
            
            # Get series info for timeframe
            series = event.get('series', [{}])[0] if event.get('series') else {}
            recurrence = series.get('recurrence', 'unknown')
            
            market_data = {
                'question': market.get('question', ''),
                'answer1': answer1,
                'answer2': answer2,
                'spread': round(spread, 4),
                'rewards_daily_rate': 0,  # Crypto markets typically don't have rewards
                'gm_reward_per_100': 0,
                'sm_reward_per_100': 0,
                'bid_reward_per_100': 0,
                'ask_reward_per_100': 0,
                'volatility_sum': 0,
                'volatilty/reward': '0',
                'min_size': market.get('orderMinSize', 5),
                '1_hour': 0,
                '3_hour': 0,
                '6_hour': 0,
                '12_hour': 0,
                '24_hour': 0,
                '7_day': 0,
                '30_day': 0,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'volatility_price': round((best_bid + best_ask) / 2, 4) if best_bid and best_ask else 0.5,
                'max_spread': 10,  # Crypto markets can have wider spreads
                'tick_size': market.get('orderPriceMinTickSize', 0.001),
                'neg_risk': market.get('negRisk', False),
                'market_slug': market.get('slug', ''),
                'token1': str(token1),
                'token2': str(token2),
                'condition_id': market.get('conditionId', ''),
                'trade_size': 25,
                'max_size': 100,
                'param_type': 'default',
                'multiplier': '',
                # Extra crypto-specific fields
                'series_slug': series.get('slug', ''),
                'recurrence': recurrence,
                'end_date': market.get('endDate', ''),
                'volume_24hr': market.get('volume24hr', 0),
            }
            
            markets_data.append(market_data)
            
        except Exception as e:
            print(f"Error processing market {market.get('question', 'unknown')}: {e}")
            continue
    
    return markets_data


def fetch_event_by_slug(slug):
    """Fetch a single event by its slug"""
    try:
        r = requests.get(f"{GAMMA_API}/events", params={'slug': slug})
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        return None


def update_crypto_markets():
    """Main function to update crypto markets by generating slugs for upcoming events"""
    print(f"\n{datetime.datetime.now(pytz.utc)}: Starting crypto markets update...")
    
    all_markets = []
    now = datetime.datetime.now(pytz.utc)
    
    # Generate slugs for hourly markets (next 24 hours)
    print("  Fetching hourly markets...")
    for asset in ['bitcoin', 'solana', 'xrp']:
        for hours_ahead in range(0, 24):
            target_time = now + datetime.timedelta(hours=hours_ahead)
            # Round to the hour
            target_time = target_time.replace(minute=0, second=0, microsecond=0)
            
            slug = generate_hourly_slug(asset, target_time)
            event = fetch_event_by_slug(slug)
            
            if event:
                markets = process_event(event)
                for m in markets:
                    m['recurrence'] = 'hourly'
                all_markets.extend(markets)
            
            time.sleep(0.1)  # Rate limiting
    
    print(f"    Found {len([m for m in all_markets if m.get('recurrence') == 'hourly'])} hourly markets")
    
    # Generate slugs for 15m markets (next 6 hours) 
    print("  Fetching 15m markets...")
    for asset in ['xrp', 'eth', 'sol']:
        for minutes_ahead in range(0, 360, 15):  # Every 15 min for 6 hours
            target_time = now + datetime.timedelta(minutes=minutes_ahead)
            # Round to nearest 15 minutes
            minute = (target_time.minute // 15) * 15
            target_time = target_time.replace(minute=minute, second=0, microsecond=0)
            
            slug = generate_15m_slug(asset, target_time)
            event = fetch_event_by_slug(slug)
            
            if event:
                markets = process_event(event)
                for m in markets:
                    m['recurrence'] = '15m'
                all_markets.extend(markets)
            
            time.sleep(0.1)
    
    print(f"    Found {len([m for m in all_markets if m.get('recurrence') == '15m'])} 15m markets")
    
    # Generate slugs for daily markets (next 7 days)
    print("  Fetching daily markets...")
    for asset in ['xrp', 'dogecoin']:
        for days_ahead in range(0, 7):
            target_date = now + datetime.timedelta(days=days_ahead)
            
            slug = generate_daily_slug(asset, target_date)
            event = fetch_event_by_slug(slug)
            
            if event:
                markets = process_event(event)
                for m in markets:
                    m['recurrence'] = 'daily'
                all_markets.extend(markets)
            
            time.sleep(0.1)
    
    print(f"    Found {len([m for m in all_markets if m.get('recurrence') == 'daily'])} daily markets")
    
    # Remove duplicates by condition_id
    seen = set()
    unique_markets = []
    for m in all_markets:
        if m['condition_id'] not in seen:
            seen.add(m['condition_id'])
            unique_markets.append(m)
    
    print(f"\n  Total unique markets: {len(unique_markets)}")
    
    if len(unique_markets) > 0:
        # Sort by recurrence (hourly first) then by end_date
        recurrence_order = {'hourly': 0, '15m': 1, 'daily': 2}
        unique_markets.sort(key=lambda x: (
            recurrence_order.get(x.get('recurrence', 'unknown'), 99),
            x.get('end_date', '')
        ))
        
        save_to_json(unique_markets, 'crypto_markets.json')
        print(f"  Saved to config/crypto_markets.json")
        
        # Print summary
        print("\n  Summary by timeframe:")
        for tf in ['hourly', '15m', 'daily']:
            count = len([m for m in unique_markets if m.get('recurrence') == tf])
            print(f"    {tf}: {count} markets")
    else:
        print("  No markets found, not saving.")
    
    return unique_markets


if __name__ == "__main__":
    while True:
        try:
            update_crypto_markets()
        except Exception as e:
            print(f"Error in update loop: {e}")
        
        print(f"\n{datetime.datetime.now(pytz.utc)}: Sleeping for 30 minutes...")
        time.sleep(60 * 30)  # Every 30 minutes
