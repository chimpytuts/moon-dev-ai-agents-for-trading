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
BIRDEYE_URL = "https://public-api.birdeye.so/defi"
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    raise ValueError("🚨 BIRDEYE_API_KEY not found in environment variables!")

def get_appropriate_timeframes(creation_timestamp):
    """
    Determine appropriate timeframes based on token age
    
    Args:
        creation_timestamp (int): Token creation timestamp
    
    Returns:
        tuple: (timeframes_list, days_back)
    """
    current_time = int(time.time())
    token_age_seconds = current_time - creation_timestamp
    
    # Log token age details
    cprint("\n⏰ Token Age Analysis:", "cyan")
    cprint(f"  • Creation Time: {datetime.fromtimestamp(creation_timestamp)}", "white")
    cprint(f"  • Current Time: {datetime.fromtimestamp(current_time)}", "white")
    cprint(f"  • Age in seconds: {token_age_seconds}", "white")
    cprint(f"  • Age in minutes: {token_age_seconds / 60:.2f}", "white")
    cprint(f"  • Age in hours: {token_age_seconds / 3600:.2f}", "white")
    cprint(f"  • Age in days: {token_age_seconds / (24 * 3600):.2f}", "white")
    
    # Define all possible timeframes with their minimum required age in seconds
    ALL_TIMEFRAMES = [
        ('1m', 60 * 2),           # Need at least 2 minutes
        ('3m', 180 * 2),          # Need at least 6 minutes
        ('5m', 300 * 2),          # Need at least 10 minutes
        ('15m', 900 * 2),         # Need at least 30 minutes
        ('30m', 1800 * 2),        # Need at least 1 hour
        ('1H', 3600 * 2),         # Need at least 2 hours
        ('2H', 7200 * 2),         # Need at least 4 hours
        ('4H', 14400 * 2),        # Need at least 8 hours
        ('6H', 21600 * 2),        # Need at least 12 hours
        ('8H', 28800 * 2),        # Need at least 16 hours
        ('12H', 43200 * 1.5),     # Need at least 18 hours
        ('1D', 86400 * 1.5),      # Need at least 36 hours
        ('3D', 259200 * 1.5),     # Need at least 4.5 days
        ('1W', 604800 * 1.5),     # Need at least 10.5 days
        ('1M', 2592000 * 1.5)     # Need at least 45 days
    ]
    
    # Select timeframes based on token age
    selected_timeframes = []
    for tf, min_age in ALL_TIMEFRAMES:
        if token_age_seconds >= min_age:
            selected_timeframes.append(tf)
            cprint(f"  • Adding {tf} timeframe (requires {min_age/3600:.1f}h, token age: {token_age_seconds/3600:.1f}h)", "cyan")
    
    if not selected_timeframes:  # If token is very new, use smallest timeframes
        selected_timeframes = ['1m', '3m', '5m']
        cprint("  • Token too new, using minimum timeframes", "yellow")
    
    # Calculate days back based on token age
    days_back = min(token_age_seconds / (24 * 3600), DAYSBACK_4_DATA)
    
    return selected_timeframes, days_back

def collect_token_data(token):
    """Collect all relevant data for a token"""
    try:
        # Get pair analytics first
        market_address = get_highest_liquidity_market(token)
        if not market_address:
            return None
            
        pair_data = get_pair_analytics(market_address)
        if not pair_data:
            return None
            
        # Get appropriate timeframes based on token age
        creation_timestamp = int(pair_data.get('created_at', 0)) / 1000
        current_time = int(time.time())
        token_age_seconds = current_time - creation_timestamp
        timeframes, days_back = get_appropriate_timeframes(creation_timestamp)
        
        # Format pair analytics data
        market_data = {
            'pair_analytics': {
                'price_usd': float(pair_data.get('priceUsd', 0)),
                'price_native': float(pair_data.get('priceNative', 0)),
                'price_change': {
                    '5m': pair_data.get('priceChange', {}).get('m5', 0),
                    '1h': pair_data.get('priceChange', {}).get('h1', 0),
                    '6h': pair_data.get('priceChange', {}).get('h6', 0),
                    '24h': pair_data.get('priceChange', {}).get('h24', 0)
                },
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
                'volume': {
                    '5m': pair_data.get('volume', {}).get('m5', 0),
                    '1h': pair_data.get('volume', {}).get('h1', 0),
                    '6h': pair_data.get('volume', {}).get('h6', 0),
                    '24h': pair_data.get('volume', {}).get('h24', 0)
                },
                'liquidity': {
                    'usd': pair_data.get('liquidity', {}).get('usd', 0),
                    'base': pair_data.get('liquidity', {}).get('base', 0),
                    'quote': pair_data.get('liquidity', {}).get('quote', 0)
                },
                'market_cap': pair_data.get('marketCap', 0),
                'fdv': pair_data.get('fdv', 0),
                'created_at': pair_data.get('pairCreatedAt', 0),
                'social_links': [social.get('url') for social in pair_data.get('info', {}).get('socials', [])]
            },
            'ohlcv_data': {}
        }
        
        # Get OHLCV data for each timeframe
        for tf in timeframes:
            time.sleep(3)  # Wait 3 seconds between timeframe requests
            df = get_data(token, days_back, tf, token_age_seconds)
            if df is not None and not df.empty:
                market_data['ohlcv_data'][tf] = {
                    'candles': len(df),
                    'price': {
                        'open': float(df['Open'].iloc[0]),
                        'high': float(df['High'].max()),
                        'low': float(df['Low'].min()),
                        'close': float(df['Close'].iloc[-1]),
                        'change': float((df['Close'].iloc[-1] - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100)
                    },
                    'volume': float(df['Volume'].sum()),
                    'indicators': {
                        'RSI': float(df['RSI'].iloc[-1]) if 'RSI' in df else None,
                        'MA20': float(df['MA20'].iloc[-1]) if 'MA20' in df else None,
                        'MA40': float(df['MA40'].iloc[-1]) if 'MA40' in df else None,
                        'trends': {
                            'above_MA20': bool(df['Price_above_MA20'].iloc[-1]) if 'Price_above_MA20' in df else None,
                            'above_MA40': bool(df['Price_above_MA40'].iloc[-1]) if 'Price_above_MA40' in df else None,
                            'MA20_above_MA40': bool(df['MA20_above_MA40'].iloc[-1]) if 'MA20_above_MA40' in df else None
                        }
                    }
                }
            
        return market_data
            
    except Exception as e:
        cprint(f"❌ Error collecting token data: {str(e)}", "red")
        return None
    
def collect_all_tokens():
    """Collect OHLCV data for all monitored tokens"""
    market_data = {}
    
    cprint("\n🔍 Moon Dev's AI Agent starting market data collection...", "white", "on_blue")
    
    for token in MONITORED_TOKENS:
        data = collect_token_data(token)
        if data is not None:
            market_data[token] = data
        # Add delay between tokens
        time.sleep(2)  # 2 second delay between tokens
            
    cprint("\n✨ Moon Dev's AI Agent completed market data collection!", "white", "on_green")
    
    return market_data

def calculate_timeframe_seconds(timeframe):
    """Convert timeframe string to seconds"""
    units = {
        'm': 60,
        'H': 3600,
        'D': 86400,
        'W': 604800,
        'M': 2592000
    }
    
    number = int(''.join(filter(str.isdigit, timeframe)))
    unit = ''.join(filter(str.isalpha, timeframe))
    
    return number * units[unit]

def get_time_range(timeframe, token_age_seconds):
    """
    Calculate time range to always get 1000 candles or up to token creation
    
    Args:
        timeframe (str): Timeframe like '1m', '5m', '1H' etc
        token_age_seconds (int): Token age in seconds
        
    Returns:
        tuple: (time_from, time_to)
    """
    now = int(time.time())
    timeframe_in_seconds = calculate_timeframe_seconds(timeframe)
    
    # Calculate range for 1000 candles
    range_for_1000_candles = timeframe_in_seconds * 1000
    
    # Use token age as maximum range
    time_range = min(int(token_age_seconds), range_for_1000_candles)
    
    # Round time_from and time_to to the nearest timeframe interval
    time_to = now - (now % timeframe_in_seconds)
    time_from = time_to - time_range
    time_from = time_from - (time_from % timeframe_in_seconds)
    
    cprint(f"\n📊 Time Range for {timeframe}:", "cyan")
    cprint(f"  • Timeframe in seconds: {timeframe_in_seconds}", "white")
    cprint(f"  • Range for 1000 candles: {range_for_1000_candles/3600:.2f} hours", "white")
    cprint(f"  • Token age: {token_age_seconds/3600:.2f} hours", "white")
    cprint(f"  • Selected range: {time_range/3600:.2f} hours", "white")
    cprint(f"  • From: {datetime.fromtimestamp(time_from)}", "white")
    cprint(f"  • To: {datetime.fromtimestamp(time_to)}", "white")
    
    return time_from, time_to

def get_data(address, days_back, timeframe, token_age_seconds):
    """Get OHLCV data with proper time range handling"""
    try:
        # Get appropriate time range for this timeframe
        time_from, time_to = get_time_range(timeframe, token_age_seconds)

        url = f"https://public-api.birdeye.so/defi/ohlcv?address={address}&type={timeframe}&time_from={time_from}&time_to={time_to}"
        headers = {"X-API-KEY": BIRDEYE_API_KEY}
        
        cprint(f"  • API URL: {url}", "white")
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            json_response = response.json()
            items = json_response.get('data', {}).get('items', [])
            
            if not items:
                cprint(f"⚠️ No data returned for {timeframe}", "yellow")
                return pd.DataFrame()

            processed_data = [{
                'Datetime (UTC)': datetime.utcfromtimestamp(item['unixTime']).strftime('%Y-%m-%d %H:%M:%S'),
                'Open': float(item['o'] or 0),
                'High': float(item['h'] or 0),
                'Low': float(item['l'] or 0),
                'Close': float(item['c'] or 0),
                'Volume': float(item['v'] or 0)
            } for item in items]

            df = pd.DataFrame(processed_data)
            
            if df.empty:
                cprint(f"⚠️ Empty DataFrame for {timeframe}", "yellow")
                return pd.DataFrame()
                
            # Remove any rows with dates far in the future
            df['datetime_obj'] = pd.to_datetime(df['Datetime (UTC)'])
            df['datetime_obj'] = df['datetime_obj'].dt.tz_localize('UTC')
            df = df[df['datetime_obj'] <= datetime.now(pytz.utc)]
            df = df.drop('datetime_obj', axis=1)

            # Handle zero or None values
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Calculate indicators with adjusted window sizes based on available data
            data_length = len(df)
            if data_length >= 2:  # Minimum 2 candles required
                # Adjust MA and RSI lengths based on available data
                ma20_length = min(20, data_length - 1)
                ma40_length = min(40, data_length - 1)
                rsi_length = min(14, data_length - 1)
                
                df['MA20'] = ta.sma(df['Close'], length=ma20_length)
                df['RSI'] = ta.rsi(df['Close'], length=rsi_length)
                df['MA40'] = ta.sma(df['Close'], length=ma40_length)

                df['Price_above_MA20'] = df['Close'] > df['MA20']
                df['Price_above_MA40'] = df['Close'] > df['MA40']
                df['MA20_above_MA40'] = df['MA20'] > df['MA40']
                
                cprint(f"✅ Got {len(df)} candles for {timeframe} (MA20: {ma20_length}, MA40: {ma40_length}, RSI: {rsi_length})", "green")
                return df
            else:
                cprint(f"⚠️ Not enough data for {timeframe} (only {data_length} candles)", "yellow")
                return pd.DataFrame()
            
        else:
            cprint(f"❌ API error for {timeframe}: {response.status_code}", "red")
            try:
                error_details = response.json()
                cprint(f"  • Error details: {error_details}", "red")
            except:
                cprint(f"  • Response text: {response.text}", "red")
            return pd.DataFrame()
            
    except Exception as e:
        cprint(f"❌ Error getting data for {timeframe}: {str(e)}", "red")
        return pd.DataFrame()

def get_highest_liquidity_market(token_address, max_retries=3, timeout=10):
    """
    Get the market address with highest base price for a given token using Rugcheck API
    
    Args:
        token_address (str): Token address to check
        max_retries (int): Maximum number of retry attempts
        timeout (int): Timeout in seconds for the API call
        
    Returns:
        str: Market address with highest liquidity or None if not found
    """
    for attempt in range(max_retries):
        try:
            rugcheck_url = f"{RUG_CHECK_URL}/v1/tokens/{token_address}/report"
            rugcheck_response = requests.get(rugcheck_url, timeout=timeout)
            
            if rugcheck_response.status_code != 200:
                cprint(f"❌ Failed to get rugcheck report: HTTP {rugcheck_response.status_code}", "red")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait 1 second before retrying
                    continue
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

        except requests.exceptions.Timeout:
            cprint(f"⚠️ Attempt {attempt + 1}/{max_retries}: Rugcheck API timeout", "yellow")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            cprint("❌ All retry attempts failed", "red")
            return None
        except requests.exceptions.ConnectionError:
            cprint(f"⚠️ Attempt {attempt + 1}/{max_retries}: Connection error to Rugcheck API", "yellow")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            cprint("❌ All retry attempts failed", "red")
            return None
        except Exception as e:
            cprint(f"❌ Error getting market address: {str(e)}", "red")
            return None

def get_pair_analytics(pair_address, max_retries=3, timeout=10):
    """
    Fetch and process trading analytics for a pair from DexScreener API
    
    Args:
        pair_address (str): The pair address to analyze
        max_retries (int): Maximum number of retry attempts
        timeout (int): Timeout in seconds for the API call
        
    Returns:
        dict: Processed trading metrics or None if failed
    """
    for attempt in range(max_retries):
        try:
            dexscreener_url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}"
            response = requests.get(dexscreener_url, timeout=timeout)
            
            if response.status_code != 200:
                cprint(f"❌ Failed to get pair data: HTTP {response.status_code}", "red")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
                
            data = response.json()
            pair_data = data.get('pairs', [{}])[0]
            
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

        except requests.exceptions.Timeout:
            cprint(f"⚠️ Attempt {attempt + 1}/{max_retries}: DexScreener API timeout", "yellow")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            cprint("❌ All retry attempts failed", "red")
            return None
        except requests.exceptions.ConnectionError:
            cprint(f"⚠️ Attempt {attempt + 1}/{max_retries}: Connection error to DexScreener API", "yellow")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            cprint("❌ All retry attempts failed", "red")
            return None
        except Exception as e:
            cprint(f"❌ Error getting pair analytics: {str(e)}", "red")
            return None
