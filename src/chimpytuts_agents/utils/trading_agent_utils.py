from src.config import *
import requests
import pandas as pd
import pprint
import re as reggie
import sys
import os
import time
import json
import numpy as np
import datetime
import pandas_ta as ta
from datetime import datetime, timedelta
from termcolor import colored, cprint
import solders
from dotenv import load_dotenv
import shutil
import atexit
import pytz
from solders.pubkey import Pubkey

BIRDEYE_URL = "https://public-api.birdeye.so/defi"
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    raise ValueError("🚨 BIRDEYE_API_KEY not found in environment variables!")

def token_overview_since_creation(address, creation_timestamp):
    """
    Fetch token overview data from Birdeye, filtered based on creation time
    
    Args:
        address (str): Token address
        creation_timestamp (int): Unix timestamp of token creation
    
    Returns:
        dict: Filtered overview data or None if failed
    """
    try:
        # Make API request to Birdeye
        overview_url = f"{BIRDEYE_URL}/token_overview?address={address}"
        headers = {"X-API-KEY": BIRDEYE_API_KEY}
        
        response = requests.get(overview_url, headers=headers)
        if response.status_code != 200:
            cprint(f"❌ Failed to retrieve token overview: HTTP {response.status_code}", "red")
            return None

        overview_data = response.json().get('data', {})
        
        # Calculate how many hours old the token is
        current_time = int(time.time())
        hours_since_creation = (current_time - creation_timestamp) / 3600

        # Define available time windows in hours
        time_windows = [0.5, 1, 2, 4, 6, 8, 12, 24]
        
        # Find which metrics we should keep based on token age
        valid_windows = [w for w in time_windows if w <= hours_since_creation]
        
        if not valid_windows:
            cprint("⚠️ Token too new for historical metrics", "yellow")
            return {
                'price_usd': overview_data.get('price', 0),
                'mc': overview_data.get('realMc', 0),
                'total_supply': overview_data.get('supply', 0),
                'circulating_supply': overview_data.get('circulatingSupply', 0),
            }

        # Create filtered data with base metrics
        filtered_data = {
            'price_usd': overview_data.get('price', 0),
            'mc': overview_data.get('realMc', 0),
            'total_supply': overview_data.get('supply', 0),
            'circulating_supply': overview_data.get('circulatingSupply', 0),
        }

        # Map time windows to their metric suffixes
        window_suffixes = {
            0.5: '30m',
            1: '1h',
            2: '2h',
            4: '4h',
            6: '6h',
            8: '8h',
            12: '12h',
            24: '24h'
        }

        # Keep only metrics for valid time windows
        for window in valid_windows:
            suffix = window_suffixes[window]
            
            # Trading metrics
            filtered_data[f'buy{suffix}'] = overview_data.get(f'buy{suffix}', 0)
            filtered_data[f'sell{suffix}'] = overview_data.get(f'sell{suffix}', 0)
            filtered_data[f'vBuy{suffix}USD'] = overview_data.get(f'vBuy{suffix}USD', 0)
            filtered_data[f'vSell{suffix}USD'] = overview_data.get(f'vSell{suffix}USD', 0)
            filtered_data[f'uniqueWallet{suffix}'] = overview_data.get(f'uniqueWallet{suffix}', 0)
            filtered_data[f'price_change_{suffix}'] = overview_data.get(f'priceChange{suffix}Percent', 0)

        cprint(f"✅ Retrieved metrics for time windows: {[window_suffixes[w] for w in valid_windows]}", "green")
        return filtered_data

    except Exception as e:
        cprint(f"❌ Error in token_overview_since_creation: {str(e)}", "red")
        return None

def collect_token_data(token, days_back=DAYSBACK_4_DATA, timeframe=DATA_TIMEFRAME):
    """Collect OHLCV data for a single token"""
    cprint(f"\n🤖 Moon Dev's AI Agent fetching data for {token}...", "white", "on_blue")
    
    try:
        # Get data from Birdeye
        data = get_data(token, days_back, timeframe)
        
        if data is None or data.empty:
            cprint(f"❌ Moon Dev's AI Agent couldn't fetch data for {token}", "white", "on_red")
            return None
            
        cprint(f"📊 Moon Dev's AI Agent processed {len(data)} candles for analysis", "white", "on_blue")
        
        # Save data if configured
        if SAVE_OHLCV_DATA:
            save_path = f"data/{token}_latest.csv"
        else:
            save_path = f"temp_data/{token}_latest.csv"
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save to CSV
        data.to_csv(save_path)
        cprint(f"💾 Moon Dev's AI Agent cached data for {token[:4]}", "white", "on_green")
        
        return data
        
    except Exception as e:
        cprint(f"❌ Moon Dev's AI Agent encountered an error: {str(e)}", "white", "on_red")
        return None

def collect_all_tokens():
    """Collect OHLCV data for all monitored tokens"""
    market_data = {}
    
    cprint("\n🔍 Moon Dev's AI Agent starting market data collection...", "white", "on_blue")
    
    for token in MONITORED_TOKENS:
        data = collect_token_data(token)
        if data is not None:
            market_data[token] = data
            
    cprint("\n✨ Moon Dev's AI Agent completed market data collection!", "white", "on_green")
    
    return market_data

def get_time_range(days_back):

    now = datetime.now()
    ten_days_earlier = now - timedelta(days=days_back)
    time_to = int(now.timestamp())
    time_from = int(ten_days_earlier.timestamp())
    #print(time_from, time_to)

    return time_from, time_to

def get_data(address, days_back_4_data, timeframe):
    time_from, time_to = get_time_range(days_back_4_data)
    # Check temp data first
    # temp_file = f"temp_data/{address}_latest.csv"
    # if os.path.exists(temp_file):
    #    print(f"📂 Moon Dev found cached data for {address[:4]}")
    #    return pd.read_csv(temp_file)

    url = f"https://public-api.birdeye.so/defi/ohlcv?address={address}&type={timeframe}&time_from={time_from}&time_to={time_to}"

    headers = {"X-API-KEY": BIRDEYE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        json_response = response.json()
        items = json_response.get('data', {}).get('items', [])


        processed_data = [{
            'Datetime (UTC)': datetime.utcfromtimestamp(item['unixTime']).strftime('%Y-%m-%d %H:%M:%S'),
            'Open': item['o'],
            'High': item['h'],
            'Low': item['l'],
            'Close': item['c'],
            'Volume': item['v']
        } for item in items]

        df = pd.DataFrame(processed_data)
        # Remove any rows with dates far in the future
        current_date = datetime.now(pytz.utc)  # Ensure current date is in UTC

        # Localize the fetched data to UTC
        df['datetime_obj'] = pd.to_datetime(df['Datetime (UTC)'])
        df['datetime_obj'] = df['datetime_obj'].dt.tz_localize('UTC')

        # Now filter based on the current date
        df = df[df['datetime_obj'] <= current_date]
        df = df.drop('datetime_obj', axis=1)

        # Pad if needed
        if len(df) < 40:
            print(f"🌙 MoonDev Alert: Padding data to ensure minimum 40 rows for analysis! 🚀")
            rows_to_add = 40 - len(df)
            first_row_replicated = pd.concat([df.iloc[0:1]] * rows_to_add, ignore_index=True)
            df = pd.concat([first_row_replicated, df], ignore_index=True)

        print(f"📊 MoonDev's Data Analysis Ready! Processing {len(df)} candles... 🎯")

        # Always save to temp for current run
        # df.to_csv(temp_file)
        # print(f"🔄 Moon Dev cached data for {address[:4]}")

        # Calculate indicators
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA40'] = ta.sma(df['Close'], length=40)

        df['Price_above_MA20'] = df['Close'] > df['MA20']
        df['Price_above_MA40'] = df['Close'] > df['MA40']
        df['MA20_above_MA40'] = df['MA20'] > df['MA40']

        return df
    else:
        print(f"❌ MoonDev Error: Failed to fetch data for address {address}. Status code: {response.status_code}")
        if response.status_code == 401:
            print("🔑 Check your BIRDEYE_API_KEY in .env file!")
        return pd.DataFrame()
