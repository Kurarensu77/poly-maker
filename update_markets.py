import time
import pandas as pd
import json
import os
from src.updater.updater_utils import get_clob_client
from src.updater.find_markets import get_all_markets, get_all_results, get_markets, add_volatility_to_df
from src.utils.utils import load_json, save_to_json
import traceback

# Initialize client
client = get_clob_client()


def load_selected_markets():
    """Load selected markets from config/markets.json"""
    data = load_json('markets.json')
    if isinstance(data, dict) and 'markets' in data:
        return pd.DataFrame(data.get('markets', []))
    return pd.DataFrame(data) if data else pd.DataFrame()

def sort_df(df):
    # Calculate the mean and standard deviation for each column
    mean_gm = df['gm_reward_per_100'].mean()
    std_gm = df['gm_reward_per_100'].std()
    
    mean_volatility = df['volatility_sum'].mean()
    std_volatility = df['volatility_sum'].std()
    
    # Standardize the columns
    df['std_gm_reward_per_100'] = (df['gm_reward_per_100'] - mean_gm) / std_gm
    df['std_volatility_sum'] = (df['volatility_sum'] - mean_volatility) / std_volatility
    
    # Define a custom scoring function for best_bid and best_ask
    def proximity_score(value):
        if 0.1 <= value <= 0.25:
            return (0.25 - value) / 0.15
        elif 0.75 <= value <= 0.9:
            return (value - 0.75) / 0.15
        else:
            return 0
    
    df['bid_score'] = df['best_bid'].apply(proximity_score)
    df['ask_score'] = df['best_ask'].apply(proximity_score)
    
    # Create a composite score (higher is better for rewards, lower is better for volatility, with proximity scores)
    df['composite_score'] = (
        df['std_gm_reward_per_100'] - 
        df['std_volatility_sum'] + 
        df['bid_score'] + 
        df['ask_score']
    )
    
    # Sort by the composite score in descending order
    sorted_df = df.sort_values(by='composite_score', ascending=False)
    
    # Drop the intermediate columns used for calculation
    sorted_df = sorted_df.drop(columns=['std_gm_reward_per_100', 'std_volatility_sum', 'bid_score', 'ask_score', 'composite_score'])
    
    return sorted_df

def fetch_and_process_data():
    global client
    
    client = get_clob_client()
    sel_df = load_selected_markets()

    all_df = get_all_markets(client)
    print("Got all Markets")
    all_results = get_all_results(all_df, client)
    print("Got all Results")
    m_data, all_markets = get_markets(all_results, sel_df, maker_reward=0.75)
    print("Got all orderbook")

    print(f'{pd.to_datetime("now")}: Fetched all markets data of length {len(all_markets)}.')
    new_df = add_volatility_to_df(all_markets)
    new_df['volatility_sum'] =  new_df['24_hour'] + new_df['7_day'] + new_df['14_day']
    
    new_df = new_df.sort_values('volatility_sum', ascending=True)
    new_df['volatilty/reward'] = ((new_df['gm_reward_per_100'] / new_df['volatility_sum']).round(2)).astype(str)

    new_df = new_df[['question', 'answer1', 'answer2', 'spread', 'rewards_daily_rate', 'gm_reward_per_100', 'sm_reward_per_100', 'bid_reward_per_100', 'ask_reward_per_100',  'volatility_sum', 'volatilty/reward', 'min_size', '1_hour', '3_hour', '6_hour', '12_hour', '24_hour', '7_day', '30_day',  
                     'best_bid', 'best_ask', 'volatility_price', 'max_spread', 'tick_size',  
                     'neg_risk',  'market_slug', 'token1', 'token2', 'condition_id']]

    # Add default trading parameters so markets can be copied directly to markets.json
    new_df['trade_size'] = 25
    new_df['max_size'] = 100
    new_df['param_type'] = 'default'
    new_df['multiplier'] = ''

    
    volatility_df = new_df.copy()
    volatility_df = volatility_df[new_df['volatility_sum'] < 20]
    volatility_df = volatility_df.sort_values('gm_reward_per_100', ascending=False)
   
    new_df = new_df.sort_values('gm_reward_per_100', ascending=False)
    

    print(f'{pd.to_datetime("now")}: Fetched select market of length {len(new_df)}.')

    if len(new_df) > 50:
        # Save to JSON files instead of Google Sheets
        save_to_json(new_df, 'all_markets.json')
        save_to_json(volatility_df, 'volatility_markets.json')
        save_to_json(m_data, 'full_markets.json')
    else:
        print(f'{pd.to_datetime("now")}: Not saving because of length {len(new_df)}.')

if __name__ == "__main__":
    while True:
        try:
            fetch_and_process_data()
            time.sleep(60 * 60)  # Sleep for an hour
        except Exception as e:
            traceback.print_exc()
            print(str(e))
