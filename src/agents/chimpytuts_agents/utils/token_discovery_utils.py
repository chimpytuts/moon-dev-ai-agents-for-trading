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

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    raise ValueError("🚨 BIRDEYE_API_KEY not found in environment variables!")

BIRDEYE_URL = "https://public-api.birdeye.so/defi"
DEXSCREENER_URL = "https://api.dexscreener.com"
RUG_CHECK_URL = "https://api.rugcheck.xyz"	

def token_overview(address):
    """
    Fetch comprehensive token overview for AI analysis, including:
    - Trading metrics (volume, buys/sells, price changes)
    - Social metrics (views, watchlists)
    - Liquidity metrics
    - Market metrics (mcap, fdv)
    - Holder metrics
    """

    overview_url = f"{BIRDEYE_URL}/token_overview?address={address}"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}

    response = requests.get(overview_url, headers=headers)
    result = {}

    if response.status_code == 200:
        overview_data = response.json().get('data', {})

        # Trading Metrics
        result.update({
            'price_usd': overview_data.get('price', 0),
            'price_change_30m': overview_data.get('priceChange30mPercent', 0),
            'buy30m': overview_data.get('buy30m', 0),
            'sell30m': overview_data.get('sell30m', 0),
            'vBuy30mUSD': overview_data.get('vBuy30mUSD', 0),
            'vSell30mUSD': overview_data.get('vSell30mUSD', 0),
            'uniqueWallet30m': overview_data.get('uniqueWallet30m', 0),
            'mc': overview_data.get('realMc', 0),
            'total_supply': overview_data.get('supply', 0),
            'circulating_supply': overview_data.get('circulatingSupply', 0),
        })

        return result
    else:
        print(f"Failed to retrieve token overview for address {address}: HTTP status code {response.status_code}")
        return None


def token_security_info(address):
    """
    Fetch token security information including:
    - Creation details
    - Creator info
    - Token authorities
    - Holder concentration
    - Token type (2022, etc)
    - Transfer fees
    """
    url = f"{BIRDEYE_URL}/token_security?address={address}"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        security_data = response.json().get('data', {})
        
        result = {
            # Creation Info
            'creation_time': security_data.get('creationTime'),
            'creation_tx': security_data.get('creationTx'),
            'creator_address': security_data.get('creatorAddress'),
            'creator_balance': security_data.get('creatorBalance', 0),
            'creator_percentage': security_data.get('creatorPercentage', 0),
            
            # Token Authorities
            'freeze_authority': security_data.get('freezeAuthority'),
            'freezeable': security_data.get('freezeable'),
            'metaplex_update_authority': security_data.get('metaplexUpdateAuthority'),
            'metaplex_authority_balance': security_data.get('metaplexUpdateAuthorityBalance', 0),
            'metaplex_authority_percent': security_data.get('metaplexUpdateAuthorityPercent', 0),
            
            # Token Type
            'is_token_2022': security_data.get('isToken2022', False),
            'is_true_token': security_data.get('isTrueToken'),
            'mutable_metadata': security_data.get('mutableMetadata'),
            'non_transferable': security_data.get('nonTransferable'),
            
            # Holder Concentration
            'top10_holder_balance': security_data.get('top10HolderBalance', 0),
            'top10_holder_percent': security_data.get('top10HolderPercent', 0),
            'top10_user_balance': security_data.get('top10UserBalance', 0),
            'top10_user_percent': security_data.get('top10UserPercent', 0),
            'total_supply': security_data.get('totalSupply', 0),
            
            # Transfer Fees
            'transfer_fee_data': security_data.get('transferFeeData'),
            'transfer_fee_enable': security_data.get('transferFeeEnable'),
            
            # Pre-market Info
            'pre_market_holders': security_data.get('preMarketHolder', [])
        }
 
        return result
    else:
        print(f"Failed to retrieve token security info: {response.status_code}")
        return None

def get_trending_tokens():
    """Fetch trending tokens from Birdeye API"""
    try:
        endpoint = f"{BIRDEYE_URL}/token_trending"
        response = requests.get(endpoint, headers={"X-API-KEY": BIRDEYE_API_KEY})
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data and 'items' in data['data']:
            trending_tokens = [item['address'] for item in data['data']['items']]
            cprint(f"✨ Found {len(trending_tokens)} trending tokens!", "green")
            return trending_tokens
        return []
        
    except Exception as e:
        cprint(f"❌ Error fetching trending tokens: {str(e)}", "red")
        return []

def get_new_listings():
    """Fetch newly listed tokens from DexScreener API"""
    try:
        endpoint = f"{DEXSCREENER_URL}/token-profiles/latest/v1"
        response = requests.get(endpoint)
        response.raise_for_status()
        
        data = response.json()
        
        # Filter for Solana tokens and get their addresses
        solana_tokens = [
            item['tokenAddress'] for item in data 
            if item.get('chainId') == 'solana'
        ]
        
        if solana_tokens:
            cprint(f"✨ Found {len(solana_tokens)} new Solana token listings!", "green")
            return solana_tokens
            
        cprint("No new Solana tokens found", "yellow")
        return []
        
    except Exception as e:
        cprint(f"❌ Error fetching new listings from DexScreener: {str(e)}", "red")
        return []

def discover_tokens():
    """Run token discovery and return unique addresses"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cprint(f"\n⏰ Token Discovery Starting at {current_time}", "white", "on_green")
        
        # Get trending tokens
        cprint("\n🔥 Fetching trending tokens...", "cyan")
        trending = get_trending_tokens()
        
        # Get new listings
        cprint("\n🆕 Fetching new token listings...", "cyan")
        new_listings = get_new_listings()
        
        # Combine unique addresses
        all_tokens = list(set(trending + new_listings))
        
        # Print summary
        cprint("\n📊 Discovery Summary:", "green")
        cprint(f"Found {len(all_tokens)} unique token addresses:", "green")
        for addr in all_tokens:
            cprint(f"  • {addr}", "green")
        
        return all_tokens
        
    except Exception as e:
        cprint(f"\n❌ Error in discovery: {str(e)}", "red")
        return []
    
def check_rugcheck_report(token_address):
    """
    Check token's liquidity lock status and market data using Rugcheck API
    Returns dict with liquidity info and market analysis
    """
    try:
        rugcheck_url = f"{RUG_CHECK_URL}/v1/tokens/{token_address}/report"
        rugcheck_response = requests.get(rugcheck_url)
        
        result = {
            'liquidity_locked': False,
            'liquidity_locked_pct': 0,
            'liquidity_locked_usd': 0,
            'liquidity_locked_tokens': 0,
            'total_lp_tokens': 0,
            'markets_found': 0,
            'market_address': None,
            'success': False,
            'error': None
        }
        
        if rugcheck_response.status_code == 200:
            rugcheck_data = rugcheck_response.json()
            
            if 'markets' in rugcheck_data:
                result['markets_found'] = len(rugcheck_data['markets'])
                highest_base_price = 0
                selected_market = None
                
                # First find the market with highest base price
                for market in rugcheck_data['markets']:
                    if market.get('marketType') == 'raydium' and 'lp' in market:
                        base_price = float(market['lp'].get('basePrice', 0))
                        if base_price > highest_base_price:
                            highest_base_price = base_price
                            selected_market = market
                
                # Then get the lock data from the selected market
                if selected_market and 'lp' in selected_market:
                    lp_data = selected_market['lp']
                    result.update({
                        'liquidity_locked': lp_data.get('lpLockedPct', 0) > 0,
                        'liquidity_locked_pct': lp_data.get('lpLockedPct', 0),
                        'liquidity_locked_usd': lp_data.get('lpLockedUSD', 0),
                        'liquidity_locked_tokens': lp_data.get('lpLocked', 0),
                        'total_lp_tokens': lp_data.get('lpTotalSupply', 0),
                        'market_address': selected_market.get('pubkey'),
                        'success': True
                    })
                
            else:
                result['error'] = "No markets data found"
                cprint("No markets data found", "red")
        else:
            result['error'] = f"API request failed with status code: {rugcheck_response.status_code}"
            
        return result
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'liquidity_locked': False,
            'liquidity_locked_pct': 0,
            'liquidity_locked_usd': 0,
            'liquidity_locked_tokens': 0,
            'total_lp_tokens': 0,
            'markets_found': 0,
            'market_address': None
        }
    

def format_time_difference(timestamp):
    """Format time difference into detailed age"""
    if not timestamp:
        return "Unknown"
        
    now = datetime.now()
    diff = now - datetime.fromtimestamp(timestamp)
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    seconds = diff.seconds % 60
    
    age_parts = []
    if days > 0:
        age_parts.append(f"{days}d")
    if hours > 0:
        age_parts.append(f"{hours}h")
    if minutes > 0:
        age_parts.append(f"{minutes}m")
    if seconds > 0 or not age_parts:
        age_parts.append(f"{seconds}s")
        
    return " ".join(age_parts)

def check_rugpull_risk_rpc(token_address, test_amount=1000000):
    try:
        analysis_result = {
            "basic_info": {
                "risk_level": 0,
                "token_type": "",
                "transfer_fee": 0,
                "max_transfer_fee": "0",
                "freeze_authority": False,
                "update_authority": "",
                "update_authority_is_safe": False,
                "mint_authority": False,
                "liquidity_lock_percentage": 0,
                "liquidity_lock_usd": 0,
                "supply_concentration": 0,
                "is_rugpull": False
            },
            "market_data": {
                "price": 0,
                "market_cap": 0,
                "total_supply": 0,
                "circulating_supply": 0,
                "creation_date": "",
                "token_age_days": 0
            },
            "trading_activity_30m": {
                "price_change": 0,
                "buys": 0,
                "sells": 0,
                "buy_volume": 0,
                "sell_volume": 0,
                "unique_wallets": 0
            }
        }

        cprint(f"\n🔍 Analyzing rugpull risk for token {token_address[:8]}...", "white", "on_blue")
        
        # Get security info first
        security_info = token_security_info(token_address)
        if not security_info:
            cprint("❌ Failed to get token security information", "red")
            return None
        
        # First, let's check if this is a Token2022 token
        program_check_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                token_address,
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed"
                }
            ]
        }

        program_response = requests.post(os.getenv("RPC_ENDPOINT"), json=program_check_payload)
        if not program_response.status_code == 200:
            cprint("❌ Failed to get token information", "red")
            return None

        program_data = program_response.json()
        if not program_data.get('result'):
            cprint("❌ No token data found", "red")
            return None

        # Get the program ID (owner)
        program_id = program_data['result']['value']['owner']

        TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        
        is_token_2022 = program_id == TOKEN_2022
        is_token_program = program_id == TOKEN_PROGRAM

        # Display program type nicely
        if is_token_2022:
            cprint("Token Program: Token2022", "cyan")
        elif is_token_program:
            cprint("Token Program: Token Program", "cyan")
        else:
            cprint("Token Program: Unknown", "red")

        if not (is_token_2022 or is_token_program):
            cprint("❌ Unknown token program", "red")
            return None
        
        # Animated loading
        cprint("\n⏳ Analyzing token...", "white", "on_blue")
        
        risk_factors = {
            "transfer_fee": 0,
            "max_transfer_fee": "0",
            "freeze_authority": bool(security_info['freeze_authority']),
            "update_authority": bool(security_info['metaplex_update_authority']),
            "mint_authority": bool(security_info.get('mint_authority')),
            "risk_level": 0,
            "is_token2022": security_info['is_token_2022'],
            "warnings": []
        }

        # Check supply concentration (3 points)
        try:
            payload_largest = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenLargestAccounts",
                "params": [token_address]
            }
            
            response_largest = requests.post(os.getenv("RPC_ENDPOINT"), json=payload_largest)
            if response_largest.status_code == 200:
                largest_data = response_largest.json()
                if 'result' in largest_data:
                    accounts = largest_data['result']['value']
                    
                    total_supply = sum(float(acc['amount']) for acc in accounts)
                    top_holder_amount = float(accounts[0]['amount']) if accounts else 0
                    
                    concentration = (top_holder_amount / total_supply) if total_supply > 0 else 0
                    if concentration > 0.5:  # More than 50% in one wallet
                        risk_factors["warnings"].append(f"🚨 High supply concentration: {concentration*100:.1f}% held by single account")
                        risk_factors["risk_level"] += 3
                    analysis_result["basic_info"]["supply_concentration"] = concentration * 100

        except Exception as e:
            cprint(f"❌ Error checking supply concentration: {str(e)}", "red")

        # Update Authority check (1 point)
        PUMP_FUN_ADDRESS = "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM"
        if security_info['metaplex_update_authority'] and security_info['metaplex_update_authority'] != PUMP_FUN_ADDRESS:
            risk_factors["risk_level"] += 1
            risk_factors["warnings"].append(f"🚨 Update Authority not verified: {security_info['metaplex_update_authority']}")

        # Freeze Authority check (1 point)
        if risk_factors["freeze_authority"]:
            risk_factors["risk_level"] += 1
            risk_factors["warnings"].append("🚨 Token has freeze authority enabled")

        # Mint Authority check (1 point)
        if security_info.get('mint_authority'):
            risk_factors["risk_level"] += 1
            risk_factors["warnings"].append("🚨 Token has mint authority enabled")

        # Transfer Fee check (1 point)
        if security_info['is_token_2022'] and security_info['transfer_fee_enable']:
            risk_factors["transfer_fee"] = security_info['transfer_fee_data'].get('transferFeeBasisPoints', 0) / 100 if security_info['transfer_fee_data'] else 0
            risk_factors["max_transfer_fee"] = str(security_info['transfer_fee_data'].get('maximumFee', 0) / 100) if security_info['transfer_fee_data'] else "0"
            
            if risk_factors["transfer_fee"] > 0:
                risk_factors["risk_level"] += 1
                risk_factors["warnings"].append(f"🚨 Token has transfer fee: {risk_factors['transfer_fee']}%")

        # Liquidity lock check (2 points)
        rugcheck_data = check_rugcheck_report(token_address)
        market_creation_time = None
        
        if rugcheck_data['success']:
            if not rugcheck_data['liquidity_locked'] or rugcheck_data['liquidity_locked_pct'] < 50:
                risk_factors["risk_level"] += 2
                risk_factors["warnings"].append(f"🚨 Low liquidity lock percentage: {rugcheck_data.get('liquidity_locked_pct', 0)}%")
            # Check for low liquidity (1 point)
            if rugcheck_data.get('liquidity_locked_usd', 0) < 30000:
                risk_factors["risk_level"] += 1
                risk_factors["warnings"].append("🚨 Low liquidity lock value (<$30,000)")
                
            # Get market creation time from the market with highest base price
            if rugcheck_data['success'] and 'markets' in rugcheck_data:
                try:
                    # Find market with highest base price
                    highest_base_price = 0
                    lp_token_address = None
                    
                    for market in rugcheck_data.get('markets', []):
                        if 'lp' in market:
                            base_price = float(market['lp'].get('basePrice', 0))
                            if base_price > highest_base_price:
                                highest_base_price = base_price
                                lp_token_address = market['liquidityB']  # This is the LP token address
                    
                    if lp_token_address:
                        # Get the first mint transaction for this LP token
                        mint_payload = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getSignaturesForAddress",
                            "params": [
                                lp_token_address,
                                {
                                    "limit": 1,
                                    "commitment": "confirmed",
                                    "searchTransactionHistory": true
                                }
                            ]
                        }
                        
                        mint_response = requests.post(os.getenv("RPC_ENDPOINT"), json=mint_payload)
                        if mint_response.status_code == 200:
                            mint_data = mint_response.json()
                            if mint_data.get('result') and len(mint_data['result']) > 0:
                                market_creation_time = mint_data['result'][0].get('blockTime')
                                if market_creation_time:
                                    cprint(f"First LP token mint time found: {datetime.fromtimestamp(market_creation_time)}", "cyan")
                except Exception as e:
                    cprint(f"❌ Error getting LP token mint time: {str(e)}", "red")
                    market_creation_time = None

        # Risk level warning
        if risk_factors["risk_level"] >= 7:
            risk_factors["warnings"].append(f"🚨 High Risk Token: Risk Level {risk_factors['risk_level']}/10")
        elif risk_factors["risk_level"] >= 4:
            risk_factors["warnings"].append(f"⚠️ Medium Risk Token: Risk Level {risk_factors['risk_level']}/10")

        # Update the analysis_result with basic info data
        analysis_result["basic_info"].update({
            "risk_level": risk_factors["risk_level"],
            "token_type": "Token2022 Program" if is_token_2022 else "Standard Token Program",
            "transfer_fee": risk_factors["transfer_fee"],
            "max_transfer_fee": risk_factors["max_transfer_fee"],
            "freeze_authority": risk_factors["freeze_authority"],
            "update_authority": security_info["metaplex_update_authority"],
            "update_authority_is_safe": security_info["metaplex_update_authority"] == PUMP_FUN_ADDRESS,
            "mint_authority": bool(security_info.get('mint_authority')),
            "liquidity_lock_percentage": rugcheck_data.get("liquidity_locked_pct", 0),
            "liquidity_lock_usd": rugcheck_data.get("liquidity_locked_usd", 0),
            "is_rugpull": rugcheck_data.get("is_rugpull", False)
        })

        # Get overview data first
        overview_data = token_overview(token_address)
        
        # Then update market data
        creation_time = market_creation_time or security_info['creation_time']
        analysis_result["market_data"].update({
            "price": overview_data.get("price_usd", 0) if overview_data else 0,
            "market_cap": overview_data.get("mc", 0) if overview_data else 0,
            "total_supply": overview_data.get("total_supply", 0) if overview_data else 0,
            "circulating_supply": overview_data.get("circulating_supply", 0) if overview_data else 0,
            "creation_date": datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S') if creation_time else "",
            "token_age": format_time_difference(creation_time) if creation_time else "Unknown"
        })
        
        # Update trading activity if we have overview data
        if overview_data:
            analysis_result["trading_activity_30m"].update({
                "price_change": overview_data.get("price_change_30m", 0),
                "buys": overview_data.get("buy30m", 0),
                "sells": overview_data.get("sell30m", 0),
                "buy_volume": overview_data.get("vBuy30mUSD", 0),
                "sell_volume": overview_data.get("vSell30mUSD", 0),
                "unique_wallets": overview_data.get("uniqueWallet30m", 0)
            })

        # Print formatted analysis with null checks
        cprint("\n📊 Token Analysis:", "white", "on_blue")
        try:
            # Risk Level
            risk_level = analysis_result.get('basic_info', {}).get('risk_level', 0)
            cprint(f"Risk Level: {risk_level}/10", 
                   "green" if risk_level < 4 else "yellow" if risk_level < 7 else "red")
            
            # Is Rugpull
            is_rugpull = analysis_result.get('basic_info', {}).get('is_rugpull', False)
            cprint(f"Is Rugpull: {is_rugpull} {'❌' if is_rugpull else '✅'}", 
                   "red" if is_rugpull else "green")
            
            # Token Type
            cprint(f"Token Type: {analysis_result.get('basic_info', {}).get('token_type', 'Unknown')}", "cyan")
            
            # Transfer Fee
            transfer_fee = analysis_result.get('basic_info', {}).get('transfer_fee', 0)
            cprint(f"Transfer Fee: {transfer_fee}% {'✅' if transfer_fee == 0 else '❌'}", 
                   "green" if transfer_fee == 0 else "red")
            
            # Max Transfer Fee
            max_transfer_fee = float(analysis_result.get('basic_info', {}).get('max_transfer_fee', '0'))
            cprint(f"Max Transfer Fee: {max_transfer_fee} {'✅' if max_transfer_fee == 0 else '❌'}", 
                   "green" if max_transfer_fee == 0 else "red")
            
            # Freeze Authority
            freeze_auth = analysis_result.get('basic_info', {}).get('freeze_authority', False)
            cprint(f"Freeze Authority: {freeze_auth} {'✅' if not freeze_auth else '❌'}", 
                   "green" if not freeze_auth else "red")
            
            # Update Authority
            update_auth = analysis_result.get('basic_info', {}).get('update_authority', '')
            update_safe = analysis_result.get('basic_info', {}).get('update_authority_is_safe', False)
            cprint(f"Update Authority: {update_auth} {'✅' if update_safe else '❌'}", 
                   "green" if update_safe else "red")
            
            # Mint Authority
            mint_auth = analysis_result.get('basic_info', {}).get('mint_authority', False)
            cprint(f"Mint Authority: {mint_auth} {'✅' if not mint_auth else '❌'}", 
                   "green" if not mint_auth else "red")
            
            # Liquidity Lock
            lock_pct = analysis_result.get('basic_info', {}).get('liquidity_lock_percentage', 0)
            lock_usd = analysis_result.get('basic_info', {}).get('liquidity_lock_usd', 0)
            cprint(f"Liquidity Lock: {lock_pct}% (${lock_usd:,.2f}) {'✅' if lock_pct >= 50 else '❌'}", 
                   "green" if lock_pct >= 50 else "red")
            
            # Supply Concentration
            concentration = analysis_result.get('basic_info', {}).get('supply_concentration', 0)
            cprint(f"Supply Concentration: {concentration:.1f}% {'✅' if concentration <= 50 else '❌'}", 
                   "green" if concentration <= 50 else "red")

            # Print warnings
            if risk_factors.get("warnings"):
                cprint("\n⚠️ Warnings:", "yellow")
                for warning in risk_factors["warnings"]:
                    cprint(f"  • {warning}", "yellow")

            # Market Data
            cprint("\nMarket Data:", "cyan")
            market_data = analysis_result.get('market_data', {})
            cprint(f"Price: ${market_data.get('price', 0) or 0:,.12f}", "white")
            cprint(f"Market Cap: ${market_data.get('market_cap', 0) or 0:,.2f}", "white")
            cprint(f"Total Supply: {market_data.get('total_supply', 0) or 0:,.0f}", "white")
            cprint(f"Circulating Supply: {market_data.get('circulating_supply', 0) or 0:,.0f}", "white")
            cprint(f"Creation Date: {market_data.get('creation_date', 'Unknown')}", "white")
            cprint(f"Token Age: {market_data.get('token_age', 'Unknown')}", "white")

            # Trading Activity
            cprint("\n30m Trading Activity:", "cyan")
            trading = analysis_result.get('trading_activity_30m', {})
            
            # Price Change with null check
            price_change = trading.get('price_change', 0) or 0
            cprint(f"Price Change: {price_change:+.2f}%", 
                   "green" if price_change >= 0 else "red")
            
            # Trading metrics with null checks
            buys = trading.get('buys', 0) or 0
            sells = trading.get('sells', 0) or 0
            buy_volume = trading.get('buy_volume', 0) or 0
            sell_volume = trading.get('sell_volume', 0) or 0
            unique_wallets = trading.get('unique_wallets', 0) or 0
            
            cprint(f"Buys: {buys}", "white")
            cprint(f"Sells: {sells}", "white")
            cprint(f"Buy Volume: ${buy_volume:,.2f}", "white")
            cprint(f"Sell Volume: ${sell_volume:,.2f}", "white")
            cprint(f"Unique Wallets: {unique_wallets}", "white")

            cprint("✅ Analysis completed", "green")

        except Exception as e:
            cprint(f"❌ Error printing analysis: {str(e)}", "red")

        return analysis_result

    except Exception as e:
        cprint(f"\n❌ Error in token analysis Utils: {str(e)}", "red")
        return None
