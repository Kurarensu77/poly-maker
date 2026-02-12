import pandas as pd
from py_clob_client.headers.headers import create_level_2_headers
from py_clob_client.clob_types import RequestArgs

import requests
import json
import os

from dotenv import load_dotenv
load_dotenv()

from src.utils.utils import load_json, save_to_json

def get_markets_df():
    """Load markets from full_markets.json, fallback to markets.json if not found"""
    data = load_json('full_markets.json')
    if not data:
        # Fallback to markets.json if full_markets.json doesn't exist yet
        data = load_json('markets.json')
        if isinstance(data, dict) and 'markets' in data:
            data = data['markets']
    if not data:
        return pd.DataFrame()
    markets_df = pd.DataFrame(data)
    markets_df = markets_df[['question', 'answer1', 'answer2', 'token1', 'token2']]
    markets_df['token1'] = markets_df['token1'].astype(str)
    markets_df['token2'] = markets_df['token2'].astype(str)
    return markets_df

def get_selected_df():
    """Load selected markets from markets.json"""
    data = load_json('markets.json')
    if isinstance(data, dict) and 'markets' in data:
        return pd.DataFrame(data['markets'])
    return pd.DataFrame(data) if data else pd.DataFrame()

def get_all_orders(client):
    orders = client.client.get_orders()
    orders_df = pd.DataFrame(orders)

    if len(orders_df) > 0:
        orders_df['order_size'] = orders_df['original_size'].astype('float') - orders_df['size_matched'].astype('float')
        orders_df = orders_df[['asset_id', 'order_size', 'side', 'price']]

        orders_df = orders_df.rename(columns={'side': 'order_side', 'price': 'order_price'})
        return orders_df
    else:
        return pd.DataFrame()
    
def get_all_positions(client):
    try:
        positions = client.get_all_positions()
        positions = positions[['asset', 'size', 'avgPrice', 'curPrice', 'percentPnl']]
        positions = positions.rename(columns={'size': 'position_size'})
        return positions
    except:
        return pd.DataFrame()
    
def combine_dfs(orders_df, positions, markets_df, selected_df):
    # Handle empty dataframes - ensure required columns exist
    if orders_df.empty:
        orders_df = pd.DataFrame(columns=['asset_id', 'order_size', 'order_side', 'order_price'])
    if positions.empty:
        positions = pd.DataFrame(columns=['asset', 'position_size', 'avgPrice', 'curPrice', 'percentPnl'])
    
    merged_df = orders_df.merge(positions, left_on=['asset_id'], right_on=['asset'], how='outer')
    merged_df['asset_id'] = merged_df['asset_id'].combine_first(merged_df['asset'])
    merged_df = merged_df.drop(columns='asset', axis=1, errors='ignore')

    # Try to match asset_id with token1 first, then token2
    merge_token1 = merged_df.merge(markets_df, left_on='asset_id', right_on='token1', how='left')
    merge_token1['merged_with'] = 'token1'
    
    # For rows that didn't match token1, try token2
    unmatched = merge_token1[merge_token1['question'].isna()][['asset_id', 'order_size', 'order_side', 'order_price', 'position_size', 'avgPrice', 'curPrice']]
    matched = merge_token1[merge_token1['question'].notna()]
    
    if len(unmatched) > 0:
        merge_token2 = unmatched.merge(markets_df, left_on='asset_id', right_on='token2', how='left')
        merge_token2['merged_with'] = 'token2'
        combined_df = pd.concat([matched, merge_token2])
    else:
        combined_df = matched

    combined_df['answer'] = combined_df.apply(
        lambda row: row['answer1'] if row['merged_with'] == 'token1' else (row['answer2'] if pd.notna(row.get('answer2')) else 'Unknown'), axis=1
    )

    # Fill missing question with asset_id for unmatched markets
    combined_df['question'] = combined_df['question'].fillna(combined_df['asset_id'])
    
    combined_df = combined_df[['question', 'answer', 'order_size', 'order_side', 'order_price', 'position_size', 'avgPrice', 'curPrice']]
    combined_df['order_side'] = combined_df['order_side'].fillna('')
    combined_df = combined_df.fillna(0)

    combined_df['marketInSelected'] = combined_df['question'].isin(selected_df['question'])
    combined_df = combined_df.sort_values('question')
    combined_df = combined_df.sort_values('marketInSelected')
    return combined_df

def get_earnings(client):
    args = RequestArgs(method='GET', request_path='/rewards/user/markets')
    l2Headers = create_level_2_headers(client.signer, client.creds, args)
    url = "https://polymarket.com/api/rewards/markets"

    cursor = ''
    markets = []

    params = {
        "l2Headers": json.dumps(l2Headers),
        "orderBy": "earnings",
        "position": "DESC",
        "makerAddress": os.getenv('BROWSER_ADDRESS'),
        "authenticationType": "eoa",
        "nextCursor": cursor,
        "requestPath": "/rewards/user/markets"
    }

    r = requests.get(url,  params=params)
    results = r.json()

    data = pd.DataFrame(results['data'])
    data['earnings'] = data['earnings'].apply(lambda x: x[0]['earnings'])

    data = data[data['earnings'] > 0].reset_index(drop=True)
    data = data[['question', 'earnings', 'earning_percentage']]
    return data



def update_stats_once(client):
    selected_df = get_selected_df()
    markets_df = get_markets_df()
    print("Loaded config files...")

    orders_df = get_all_orders(client)
    print("Got Orders...")
    positions = get_all_positions(client)
    print("Got Positions...")

    if len(positions) > 0 or len(orders_df) > 0:
        combined_df = combine_dfs(orders_df, positions, markets_df, selected_df)
        earnings = get_earnings(client.client)
        print("Got Earnings...")
        combined_df = combined_df.merge(earnings, on='question', how='left')

        combined_df = combined_df.fillna(0)
        combined_df = combined_df.round(2)

        combined_df = combined_df.sort_values('earnings', ascending=False)
        combined_df = combined_df[['question', 'answer', 'order_size', 'position_size', 'marketInSelected', 'earnings', 'earning_percentage']]
        
        # Save to JSON instead of Google Sheets
        save_to_json(combined_df, 'account_summary.json')
    else:
        print("Position or order is empty")