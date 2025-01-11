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
BIRDEYE_API_KEY = "27b5181b36a34e91b2b81fc63bd9dfb6"

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
