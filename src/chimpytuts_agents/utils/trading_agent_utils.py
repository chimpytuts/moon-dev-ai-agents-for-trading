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

RUG_CHECK_URL = "https://api.rugcheck.xyz"	

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

def get_highest_liquidity_market(token_address):
    """
    Get the market address with highest base price for a given token using Rugcheck API
    
    Args:
        token_address (str): Token address to check
        
    Returns:
        str: Market address with highest liquidity or None if not found
    """
    try:
        rugcheck_url = f"{RUG_CHECK_URL}/v1/tokens/{token_address}/report"
        rugcheck_response = requests.get(rugcheck_url)
        
        if rugcheck_response.status_code != 200:
            cprint(f"❌ Failed to get rugcheck report: HTTP {rugcheck_response.status_code}", "red")
            return None
            
        rugcheck_data = rugcheck_response.json()
        
        if 'markets' not in rugcheck_data:
            cprint("❌ No markets data found", "red")
            return None
            
        highest_base_price = 0
        market_address = None
        
        # Find the Raydium market with highest base price
        for market in rugcheck_data['markets']:
            if market.get('marketType') == 'raydium' and 'lp' in market:
                base_price = float(market['lp'].get('basePrice', 0))
                if base_price > highest_base_price:
                    highest_base_price = base_price
                    market_address = market.get('pubkey')
        
        if market_address:
            cprint(f"✅ Found market with highest liquidity: {market_address}", "green")
        else:
            cprint("❌ No valid market found", "red")
            
        return market_address

    except Exception as e:
        cprint(f"❌ Error getting market address: {str(e)}", "red")
        return None

def get_pair_analytics(pair_address):
    """
    Fetch and process trading analytics for a pair from DexScreener API
    
    Args:
        pair_address (str): The pair address to analyze
        
    Returns:
        dict: Processed trading metrics or None if failed
    """
    try:
        # Make API request to DexScreener
        dexscreener_url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}"
        response = requests.get(dexscreener_url)
        
        if response.status_code != 200:
            cprint(f"❌ Failed to get pair data: HTTP {response.status_code}", "red")
            return None
            
        data = response.json()
        pair_data = data.get('pairs', [{}])[0]  # Get first pair from pairs array
        
        if not pair_data:
            cprint("❌ No pair data found", "red")
            return None
            
        # Extract relevant metrics
        analytics = {
            # Basic pair info
            'dex': pair_data.get('dexId'),
            'base_token': {
                'address': pair_data.get('baseToken', {}).get('address'),
                'symbol': pair_data.get('baseToken', {}).get('symbol'),
                'name': pair_data.get('baseToken', {}).get('name')
            },
            'quote_token': {
                'address': pair_data.get('quoteToken', {}).get('address'),
                'symbol': pair_data.get('quoteToken', {}).get('symbol')
            },
            
            # Price data
            'price_usd': float(pair_data.get('priceUsd', 0)),
            'price_native': float(pair_data.get('priceNative', 0)),
            
            # Price changes
            'price_change': {
                '5m': pair_data.get('priceChange', {}).get('m5', 0),
                '1h': pair_data.get('priceChange', {}).get('h1', 0),
                '6h': pair_data.get('priceChange', {}).get('h6', 0),
                '24h': pair_data.get('priceChange', {}).get('h24', 0)
            },
            
            # Trading activity
            'transactions': {
                '5m': {
                    'buys': pair_data.get('txns', {}).get('m5', {}).get('buys', 0),
                    'sells': pair_data.get('txns', {}).get('m5', {}).get('sells', 0)
                },
                '1h': {
                    'buys': pair_data.get('txns', {}).get('h1', {}).get('buys', 0),
                    'sells': pair_data.get('txns', {}).get('h1', {}).get('sells', 0)
                },
                '6h': {
                    'buys': pair_data.get('txns', {}).get('h6', {}).get('buys', 0),
                    'sells': pair_data.get('txns', {}).get('h6', {}).get('sells', 0)
                },
                '24h': {
                    'buys': pair_data.get('txns', {}).get('h24', {}).get('buys', 0),
                    'sells': pair_data.get('txns', {}).get('h24', {}).get('sells', 0)
                }
            },
            
            # Volume data
            'volume': {
                '5m': pair_data.get('volume', {}).get('m5', 0),
                '1h': pair_data.get('volume', {}).get('h1', 0),
                '6h': pair_data.get('volume', {}).get('h6', 0),
                '24h': pair_data.get('volume', {}).get('h24', 0)
            },
            
            # Liquidity metrics
            'liquidity': {
                'usd': pair_data.get('liquidity', {}).get('usd', 0),
                'base': pair_data.get('liquidity', {}).get('base', 0),
                'quote': pair_data.get('liquidity', {}).get('quote', 0)
            },
            
            # Market metrics
            'market_cap': pair_data.get('marketCap', 0),
            'fdv': pair_data.get('fdv', 0),
            
            # Creation time
            'created_at': pair_data.get('pairCreatedAt', 0),
            
            # Social links
            'social_links': [social.get('url') for social in pair_data.get('info', {}).get('socials', [])]
        }
        
        cprint(f"✅ Successfully fetched pair analytics for {pair_address[:8]}", "green")
        return analytics

    except Exception as e:
        cprint(f"❌ Error getting pair analytics: {str(e)}", "red")
        return None
