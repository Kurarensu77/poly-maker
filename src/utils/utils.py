import json
import pandas as pd
import os

# Config directory - relative to project root
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')


def pretty_print(txt, dic):
    print("\n", txt, json.dumps(dic, indent=4))


def load_json(filename):
    """
    Load JSON file from config directory.
    
    Args:
        filename (str): Name of the JSON file
        
    Returns:
        dict or list: Parsed JSON data, or empty list if file not found
    """
    filepath = os.path.join(CONFIG_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []


def save_to_json(data, filename):
    """
    Save data to JSON file in config directory.
    
    Args:
        data (DataFrame or list): Data to save
        filename (str): Name of the JSON file
    """
    filepath = os.path.join(CONFIG_DIR, filename)
    if isinstance(data, pd.DataFrame):
        records = data.to_dict(orient='records')
    else:
        records = data
    
    with open(filepath, 'w') as f:
        json.dump(records, f, indent=2)
    print(f"Saved {len(records)} records to {filepath}")


def load_config():
    """
    Load market config and hyperparameters from JSON files.
    
    Returns:
        tuple: (markets_df, hyperparams_dict)
    """
    # Load markets
    markets_data = load_json('markets.json')
    if isinstance(markets_data, dict) and 'markets' in markets_data:
        df = pd.DataFrame(markets_data['markets'])
    else:
        df = pd.DataFrame(markets_data) if markets_data else pd.DataFrame()
    df = df[df['question'] != ""].reset_index(drop=True) if len(df) > 0 else df
    
    # Load hyperparameters
    hyperparams = load_json('params.json')
    
    return df, hyperparams
