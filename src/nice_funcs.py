"""
🌙 Moon Dev's Nice Functions - A collection of utility functions for trading
Built with love by Moon Dev 🚀
"""

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

# Load environment variables
load_dotenv()

# Get API keys from environment
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    raise ValueError("🚨 BIRDEYE_API_KEY not found in environment variables!")

sample_address = "2yXTyarttn2pTZ6cwt4DqmrRuBw1G7pmFv9oT6MStdKP"

BASE_URL = "https://public-api.birdeye.so/defi"

# Create temp directory and register cleanup
os.makedirs('temp_data', exist_ok=True)

def cleanup_temp_data():
    if os.path.exists('temp_data'):
        print("🧹 Moon Dev cleaning up temporary data...")
        shutil.rmtree('temp_data')

atexit.register(cleanup_temp_data)

# Custom function to print JSON in a human-readable format
def print_pretty_json(data):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)

# Function to print JSON in a human-readable format - assuming you already have it as print_pretty_json
# Helper function to find URLs in text
def find_urls(string):
    # Regex to extract URLs
    return reggie.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)

# UPDATED TO RMEOVE THE OTHER ONE so now we can just use this filter instead of filtering twice
def token_overview(address):
    """
    Fetch comprehensive token overview for AI analysis, including:
    - Trading metrics (volume, buys/sells, price changes)
    - Social metrics (views, watchlists)
    - Liquidity metrics
    - Market metrics (mcap, fdv)
    - Holder metrics
    """

    overview_url = f"{BASE_URL}/token_overview?address={address}"
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
    url = f"{BASE_URL}/token_security?address={address}"
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

def token_creation_info(address):

    '''
    output sampel =

    Token Creation Info:
{   'decimals': 9,
    'owner': 'AGWdoU4j4MGJTkSor7ZSkNiF8oPe15754hsuLmwcEyzC',
    'slot': 242801308,
    'tokenAddress': '9dQi5nMznCAcgDPUMDPkRqG8bshMFnzCmcyzD8afjGJm',
    'txHash': 'ZJGoayaNDf2dLzknCjjaE9QjqxocA94pcegiF1oLsGZ841EMWBEc7TnDKLvCnE8cCVfkvoTNYCdMyhrWFFwPX6R'}
    '''
    # API endpoint for getting token creation information
    url = f"{BASE_URL}/token_creation_info?address={address}"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}

    # Sending a GET request to the API
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Parse the JSON response
        creation_data = response.json()['data']
        print_pretty_json(creation_data)
    else:
        print("Failed to retrieve token creation info:", response.status_code)

def market_buy(token, amount, slippage):
    import requests
    import sys
    import json
    import base64
    from solders.keypair import Keypair
    from solders.transaction import VersionedTransaction
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts

    KEY = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
    if not KEY:
        raise ValueError("🚨 SOLANA_PRIVATE_KEY not found in environment variables!")
    #print('key success')
    SLIPPAGE = slippage # 5000 is 50%, 500 is 5% and 50 is .5%

    QUOTE_TOKEN = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # usdc

    http_client = Client(os.getenv("RPC_ENDPOINT"))
    #print('http client success')
    if not http_client:
        raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")

    quote = requests.get(f'https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={SLIPPAGE}').json()
    #print(quote)

    txRes = requests.post('https://quote-api.jup.ag/v6/swap',
                          headers={"Content-Type": "application/json"},
                          data=json.dumps({
                              "quoteResponse": quote,
                              "userPublicKey": str(KEY.pubkey()),
                              "prioritizationFeeLamports": PRIORITY_FEE  # or replace 'auto' with your specific lamport value
                          })).json()
    #print(txRes)
    swapTx = base64.b64decode(txRes['swapTransaction'])
    #print(swapTx)
    tx1 = VersionedTransaction.from_bytes(swapTx)
    tx = VersionedTransaction(tx1.message, [KEY])
    txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
    print(f"https://solscan.io/tx/{str(txId)}")

def market_sell(QUOTE_TOKEN, amount, slippage):
    import requests
    import sys
    import json
    import base64
    from solders.keypair import Keypair
    from solders.transaction import VersionedTransaction
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts

    KEY = Keypair.from_base58_string(os.getenv("SOLANA_PRIVATE_KEY"))
    if not KEY:
        raise ValueError("🚨 SOLANA_PRIVATE_KEY not found in environment variables!")
    #print('key success')
    SLIPPAGE = slippage  # 5000 is 50%, 500 is 5% and 50 is .5%

    # token would be usdc for sell orders cause we are selling
    token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC

    http_client = Client(os.getenv("RPC_ENDPOINT"))
    if not http_client:
        raise ValueError("🚨 RPC_ENDPOINT not found in environment variables!")
    print('http client success')

    quote = requests.get(f'https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={SLIPPAGE}').json()
    #print(quote)
    txRes = requests.post('https://quote-api.jup.ag/v6/swap',
                          headers={"Content-Type": "application/json"},
                          data=json.dumps({
                              "quoteResponse": quote,
                              "userPublicKey": str(KEY.pubkey()),
                              "prioritizationFeeLamports": PRIORITY_FEE
                          })).json()
    #print(txRes)
    swapTx = base64.b64decode(txRes['swapTransaction'])
    #print(swapTx)
    tx1 = VersionedTransaction.from_bytes(swapTx)
    #print(tx1)
    tx = VersionedTransaction(tx1.message, [KEY])
    #print(tx)
    txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
    print(f"https://solscan.io/tx/{str(txId)}")

def get_time_range():

    now = datetime.now()
    ten_days_earlier = now - timedelta(days=10)
    time_to = int(now.timestamp())
    time_from = int(ten_days_earlier.timestamp())
    #print(time_from, time_to)

    return time_from, time_to

import math
def round_down(value, decimals):
    factor = 10 ** decimals
    return math.floor(value * factor) / factor

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

def fetch_wallet_holdings_og(address):

    API_KEY = BIRDEYE_API_KEY  # Assume this is your API key; replace it with the actual one

    # Initialize an empty DataFrame
    df = pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])

    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={address}"
    headers = {"x-chain": "solana", "X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_response = response.json()

        if 'data' in json_response and 'items' in json_response['data']:
            df = pd.DataFrame(json_response['data']['items'])
            df = df[['address', 'uiAmount', 'valueUsd']]
            df = df.rename(columns={'address': 'Mint Address', 'uiAmount': 'Amount', 'valueUsd': 'USD Value'})
            df = df.dropna()
            df = df[df['USD Value'] > 0.05]
        else:
            cprint("No data available in the response.", 'white', 'on_red')

    else:
        cprint(f"Failed to retrieve token list for {address}.", 'white', 'on_magenta')

    # Print the DataFrame if it's not empty
    if not df.empty:
        print(df)
        # Assuming cprint is a function you have for printing in color
        cprint(f'** Total USD balance is {df["USD Value"].sum()}', 'white', 'on_green')
        # Save the filtered DataFrame to a CSV file
        # TOKEN_PER_ADDY_CSV = 'filtered_wallet_holdings.csv'  # Define your CSV file name
        # df.to_csv(TOKEN_PER_ADDY_CSV, index=False)
    else:
        # If the DataFrame is empty, print a message or handle it as needed
        cprint("No wallet holdings to display.", 'white', 'on_red')

    return df

def fetch_wallet_token_single(address, token_mint_address):

    df = fetch_wallet_holdings_og(address)

    # filter by token mint address
    df = df[df['Mint Address'] == token_mint_address]

    return df

def token_price(address):
    url = f"https://public-api.birdeye.so/defi/price?address={address}"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}
    response = requests.get(url, headers=headers)
    price_data = response.json()

    print(price_data)

    if price_data['success']:
        return price_data['data']['value']
    else:
        return None
    
def get_position(token_mint_address):
    """
    Fetches the balance of a specific token given its mint address from a DataFrame.

    Parameters:
    - dataframe: A pandas DataFrame containing token balances with columns ['Mint Address', 'Amount'].
    - token_mint_address: The mint address of the token to find the balance for.

    Returns:
    - The balance of the specified token if found, otherwise a message indicating the token is not in the wallet.
    """
    dataframe = fetch_wallet_token_single(address, token_mint_address)

    #dataframe = pd.read_csv('data/token_per_addy.csv')

    print('-----------------')
    #print(dataframe)

    #print(dataframe)

    # Check if the DataFrame is empty
    if dataframe.empty:
        print("The DataFrame is empty. No positions to show.")
        return 0  # Indicating no balance found

    # Ensure 'Mint Address' column is treated as string for reliable comparison
    dataframe['Mint Address'] = dataframe['Mint Address'].astype(str)

    # Check if the token mint address exists in the DataFrame
    if dataframe['Mint Address'].isin([token_mint_address]).any():
        # Get the balance for the specified token
        balance = dataframe.loc[dataframe['Mint Address'] == token_mint_address, 'Amount'].iloc[0]
        #print(f"Balance for {token_mint_address[-4:]} token: {balance}")
        return balance
    else:
        # If the token mint address is not found in the DataFrame, return a message indicating so
        print("Token mint address not found in the wallet.")
        return 0  # Indicating no balance found

def get_decimals(token_mint_address):
    import requests
    import base64
    import json
    # Solana Mainnet RPC endpoint
    url = "https://api.mainnet-beta.solana.com/"
    headers = {"Content-Type": "application/json"}

    # Request payload to fetch account information
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            token_mint_address,
            {
                "encoding": "jsonParsed"
            }
        ]
    })

    # Make the request to Solana RPC
    response = requests.post(url, headers=headers, data=payload)
    response_json = response.json()

    # Parse the response to extract the number of decimals
    decimals = response_json['result']['value']['data']['parsed']['info']['decimals']
    #print(f"Decimals for {token_mint_address[-4:]} token: {decimals}")

    return decimals

def pnl_close(token_mint_address):

    ''' this will check to see if price is > sell 1, sell 2, sell 3 and sell accordingly '''

    print(f'checking pnl close to see if its time to exit for {token_mint_address[:4]}...')
    # check solana balance


    # if time is on the 5 minute do the balance check, if not grab from data/current_position.csv
    balance = get_position(token_mint_address)

    # save to data/current_position.csv w/ pandas

    # get current price of token
    price = token_price(token_mint_address)

    usd_value = balance * price

    tp = sell_at_multiple * USDC_SIZE
    sl = ((1+stop_loss_percentage) * USDC_SIZE)
    sell_size = balance
    decimals = 0
    decimals = get_decimals(token_mint_address)
    #print(f'for {token_mint_address[-4:]} decimals is {decimals}')

    sell_size = int(sell_size * 10 **decimals)

    #print(f'bal: {balance} price: {price} usdVal: {usd_value} TP: {tp} sell size: {sell_size} decimals: {decimals}')

    while usd_value > tp:


        cprint(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so closing...', 'white', 'on_green')
        try:

            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(2)
            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(2)
            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(15)

        except:
            cprint('order error.. trying again', 'white', 'on_red')
            time.sleep(2)

        balance = get_position(token_mint_address)
        price = token_price(token_mint_address)
        usd_value = balance * price
        tp = sell_at_multiple * USDC_SIZE
        sell_size = balance
        sell_size = int(sell_size * 10 **decimals)
        print(f'USD Value is {usd_value} | TP is {tp} ')


    else:
        #print(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so not closing...')
        hi = 'hi'
        #time.sleep(10)

    # while usd_value < sl but bigger than .05

    if usd_value != 0:
        #print(f'for {token_mint_address[-4:]} value is {usd_value} and sl is {sl} so not closing...')

        while usd_value < sl and usd_value > 0:

            sell_size = balance
            sell_size = int(sell_size * 10 **decimals)

            cprint(f'for {token_mint_address[:4]} value is {usd_value} and sl is {sl} so closing as a loss...', 'white', 'on_blue')

            #print(f'for {token_mint_address[-4:]} value is {usd_value} and tp is {tp} so closing...')
            try:

                market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
                time.sleep(1)
                market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
                time.sleep(1)
                market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
                time.sleep(15)

            except:
                cprint('order error.. trying again', 'white', 'on_red')
                # time.sleep(7)

            balance = get_position(token_mint_address)
            price = token_price(token_mint_address)
            usd_value = balance * price
            tp = sell_at_multiple * USDC_SIZE
            sl = ((1+stop_loss_percentage) * USDC_SIZE)
            sell_size = balance

            sell_size = int(sell_size * 10 **decimals)
            print(f'balance is {balance} and price is {price} and usd_value is {usd_value} and tp is {tp} and sell_size is {sell_size} decimals is {decimals}')

            # break the loop if usd_value is 0
            if usd_value == 0:
                print(f'successfully closed {token_mint_address[:4]} usd_value is {usd_value} so breaking loop AFTER putting it on my dont_overtrade.txt...')
                with open('dont_overtrade.txt', 'a') as file:
                    file.write(token_mint_address + '\n')
                break

        else:
            print(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so not closing...')
            #time.sleep(10)
    else:
        print(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so not closing...')

def chunk_kill(token_mint_address, slippage):
    """Kill a position in chunks"""
    cprint(f"\n🔪 Moon Dev's AI Agent initiating position exit...", "white", "on_cyan")
    
    try:
        # Get current position using address from config
        df = fetch_wallet_token_single(address, token_mint_address)
        if df.empty:
            cprint("❌ No position found to exit", "white", "on_red")
            return
            
        # Get current token amount and value
        token_amount = float(df['Amount'].iloc[0])
        current_usd_value = float(df['USD Value'].iloc[0])
        
        # Get token decimals
        decimals = get_decimals(token_mint_address)
        
        cprint(f"📊 Initial position: {token_amount:.2f} tokens (${current_usd_value:.2f})", "white", "on_cyan")
        
        while current_usd_value > 0.1:  # Keep going until position is essentially zero
            # Calculate chunk size based on current position
            chunk_size = token_amount / 3  # Split remaining into 3 chunks
            cprint(f"\n🔄 Splitting remaining position into chunks of {chunk_size:.2f} tokens", "white", "on_cyan")
            
            # Execute sell orders in chunks
            for i in range(3):
                try:
                    cprint(f"\n💫 Executing sell chunk {i+1}/3...", "white", "on_cyan")
                    sell_size = int(chunk_size * 10**decimals)
                    market_sell(token_mint_address, sell_size, slippage)
                    cprint(f"✅ Sell chunk {i+1}/3 complete", "white", "on_green")
                    time.sleep(2)  # Small delay between chunks
                except Exception as e:
                    cprint(f"❌ Error in sell chunk: {str(e)}", "white", "on_red")
            
            # Check remaining position
            time.sleep(5)  # Wait for blockchain to update
            df = fetch_wallet_token_single(address, token_mint_address)
            if df.empty:
                cprint("\n✨ Position successfully closed!", "white", "on_green")
                return
                
            # Update position size for next iteration
            token_amount = float(df['Amount'].iloc[0])
            current_usd_value = float(df['USD Value'].iloc[0])
            cprint(f"\n📊 Remaining position: {token_amount:.2f} tokens (${current_usd_value:.2f})", "white", "on_cyan")
            
            if current_usd_value > 0.1:
                cprint("🔄 Position still open - continuing to close...", "white", "on_cyan")
                time.sleep(2)
            
        cprint("\n✨ Position successfully closed!", "white", "on_green")
        
    except Exception as e:
        cprint(f"❌ Error during position exit: {str(e)}", "white", "on_red")

def sell_token(token_mint_address, amount, slippage):
    """Sell a token"""
    try:
        cprint(f"📉 Selling {amount:.2f} tokens...", "white", "on_cyan")
        # Your existing sell logic here
        print(f"just made an order {token_mint_address[:4]} selling {int(amount)} ...")
    except Exception as e:
        cprint(f"❌ Error selling token: {str(e)}", "white", "on_red")

def kill_switch(token_mint_address):

    ''' this function closes the position in full

    if the usd_size > 10k then it will chunk in 10k orders
    '''

    # if time is on the 5 minute do the balance check, if not grab from data/current_position.csv
    balance = get_position(token_mint_address)

    # get current price of token
    price = token_price(token_mint_address)
    price = float(price)

    usd_value = balance * price

    if usd_value < 10000:
        sell_size = balance
    else:
        sell_size = 10000/price

    tp = sell_at_multiple * USDC_SIZE

    # round to 2 decimals
    sell_size = round_down(sell_size, 2)
    decimals = 0
    decimals = get_decimals(token_mint_address)
    sell_size = int(sell_size * 10 **decimals)

    #print(f'bal: {balance} price: {price} usdVal: {usd_value} TP: {tp} sell size: {sell_size} decimals: {decimals}')

    while usd_value > 0:


# 100 selling 70% ...... selling 30 left
        #print(f'for {token_mint_address[-4:]} closing position cause exit all positions is set to {EXIT_ALL_POSITIONS} and value is {usd_value} and tp is {tp} so closing...')
        try:

            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
            time.sleep(1)
            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
            time.sleep(1)
            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
            time.sleep(15)

        except:
            cprint('order error.. trying again', 'white', 'on_red')
            # time.sleep(7)

        balance = get_position(token_mint_address)
        price = token_price(token_mint_address)
        usd_value = balance * price
        tp = sell_at_multiple * USDC_SIZE

        if usd_value < 10000:
            sell_size = balance
        else:
            sell_size = 10000/price

        # down downwards to 2 decimals
        sell_size = round_down(sell_size, 2)

        decimals = 0
        decimals = get_decimals(token_mint_address)
        #print(f'xxxxxxxxx for {token_mint_address[-4:]} decimals is {decimals}')
        sell_size = int(sell_size * 10 **decimals)
        print(f'balance is {balance} and usd_value is {usd_value} EXIT ALL POSITIONS TRUE and sell_size is {sell_size} decimals is {decimals}')


    else:
        print(f'for {token_mint_address[:4]} value is {usd_value} ')
        #time.sleep(10)

    print('closing position in full...')

def close_all_positions():

    # get all positions
    open_positions = fetch_wallet_holdings_og(address)

    # loop through all positions and close them getting the mint address from Mint Address column
    for index, row in open_positions.iterrows():
        token_mint_address = row['Mint Address']

        # Check if the current token mint address is the USDC contract address
        cprint(f'this is the token mint address {token_mint_address} this is don not trade list {dont_trade_list}', 'white', 'on_magenta')
        if token_mint_address in dont_trade_list:
            print(f'Skipping kill switch for USDC contract at {token_mint_address}')
            continue  # Skip the rest of the loop for this iteration

        print(f'Closing position for {token_mint_address}...')
        kill_switch(token_mint_address)

def delete_dont_overtrade_file():
    if os.path.exists('dont_overtrade.txt'):
        os.remove('dont_overtrade.txt')
        print('dont_overtrade.txt has been deleted')
    else:
        print('The file does not exist')

def supply_demand_zones(token_address, timeframe, limit):

    print('starting moons supply and demand zone calculations..')

    sd_df = pd.DataFrame()

    time_from, time_to = get_time_range()

    df = get_data(token_address, time_from, time_to, timeframe)

    # only keep the data for as many bars as limit says
    df = df[-limit:]
    #print(df)
    #time.sleep(100)

    # Calculate support and resistance, excluding the last two rows for the calculation
    if len(df) > 2:  # Check if DataFrame has more than 2 rows to avoid errors
        df['support'] = df[:-2]['Close'].min()
        df['resis'] = df[:-2]['Close'].max()
    else:  # If DataFrame has 2 or fewer rows, use the available 'close' prices for calculation
        df['support'] = df['Close'].min()
        df['resis'] = df['Close'].max()

    supp = df.iloc[-1]['support']
    resis = df.iloc[-1]['resis']
    #print(f'this is moons support for 1h {supp_1h} this is resis: {resis_1h}')

    df['supp_lo'] = df[:-2]['Low'].min()
    supp_lo = df.iloc[-1]['supp_lo']

    df['res_hi'] = df[:-2]['High'].max()
    res_hi = df.iloc[-1]['res_hi']

    #print(df)


    sd_df[f'dz'] = [supp_lo, supp]
    sd_df[f'sz'] = [res_hi, resis]

    print('here are moons supply and demand zones')
    #print(sd_df)

    return sd_df

def elegant_entry(symbol, buy_under):

    pos = get_position(symbol)
    price = token_price(symbol)
    pos_usd = pos * price
    size_needed = usd_size - pos_usd
    if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
    else: chunk_size = size_needed

    chunk_size = int(chunk_size * 10**6)
    chunk_size = str(chunk_size)

    print(f'chunk_size: {chunk_size}')

    if pos_usd > (.97 * usd_size):
        print('position filled')
        time.sleep(10)

    # add debug prints for next while
    print(f'position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}')
    print(f'buy_under: {buy_under}')
    while pos_usd < (.97 * usd_size) and (price < buy_under):

        print(f'position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}')

        try:

            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                # cprint green background black text
                cprint(f'chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev', 'white', 'on_blue')
                time.sleep(1)

            time.sleep(tx_sleep)

            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price
            size_needed = usd_size - pos_usd
            if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
            else: chunk_size = size_needed
            chunk_size = int(chunk_size * 10**6)
            chunk_size = str(chunk_size)

        except:

            try:
                cprint(f'trying again to make the order in 30 seconds.....', 'light_blue', 'on_light_magenta')
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    # cprint green background black text
                    cprint(f'chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev', 'white', 'on_blue')
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price
                size_needed = usd_size - pos_usd
                if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
                else: chunk_size = size_needed
                chunk_size = int(chunk_size * 10**6)
                chunk_size = str(chunk_size)


            except:
                cprint(f'Final Error in the buy, restart needed', 'white', 'on_red')
                time.sleep(10)
                break

        pos = get_position(symbol)
        price = token_price(symbol)
        pos_usd = pos * price
        size_needed = usd_size - pos_usd
        if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
        else: chunk_size = size_needed
        chunk_size = int(chunk_size * 10**6)
        chunk_size = str(chunk_size)

# like the elegant entry but for breakout so its looking for price > BREAKOUT_PRICE
def breakout_entry(symbol, BREAKOUT_PRICE):

    pos = get_position(symbol)
    price = token_price(symbol)
    price = float(price)
    pos_usd = pos * price
    size_needed = usd_size - pos_usd
    if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
    else: chunk_size = size_needed

    chunk_size = int(chunk_size * 10**6)
    chunk_size = str(chunk_size)

    print(f'chunk_size: {chunk_size}')

    if pos_usd > (.97 * usd_size):
        print('position filled')
        time.sleep(10)

    # add debug prints for next while
    print(f'position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}')
    print(f'breakoutpurce: {BREAKOUT_PRICE}')
    while pos_usd < (.97 * usd_size) and (price > BREAKOUT_PRICE):

        print(f'position: {round(pos,2)} price: {round(price,8)} pos_usd: ${round(pos_usd,2)}')

        # for i in range(orders_per_open):
        #     market_buy(symbol, chunk_size, slippage)
        #     # cprint green background black text
        #     cprint(f'chunk buy submitted of {symbol[-4:]} sz: {chunk_size} you my dawg moon dev', 'white', 'on_blue')
        #     time.sleep(1)

        # time.sleep(tx_sleep)

        # pos = get_position(symbol)
        # price = token_price(symbol)
        # pos_usd = pos * price
        # size_needed = usd_size - pos_usd
        # if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
        # else: chunk_size = size_needed
        # chunk_size = int(chunk_size * 10**6)
        # chunk_size = str(chunk_size)

        try:

            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                # cprint green background black text
                cprint(f'chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev', 'white', 'on_blue')
                time.sleep(1)

            time.sleep(tx_sleep)

            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price
            size_needed = usd_size - pos_usd
            if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
            else: chunk_size = size_needed
            chunk_size = int(chunk_size * 10**6)
            chunk_size = str(chunk_size)

        except:

            try:
                cprint(f'trying again to make the order in 30 seconds.....', 'light_blue', 'on_light_magenta')
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    # cprint green background black text
                    cprint(f'chunk buy submitted of {symbol[:4]} sz: {chunk_size} you my dawg moon dev', 'white', 'on_blue')
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price
                size_needed = usd_size - pos_usd
                if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
                else: chunk_size = size_needed
                chunk_size = int(chunk_size * 10**6)
                chunk_size = str(chunk_size)


            except:
                cprint(f'Final Error in the buy, restart needed', 'white', 'on_red')
                time.sleep(10)
                break

        pos = get_position(symbol)
        price = token_price(symbol)
        pos_usd = pos * price
        size_needed = usd_size - pos_usd
        if size_needed > max_usd_order_size: chunk_size = max_usd_order_size
        else: chunk_size = size_needed
        chunk_size = int(chunk_size * 10**6)
        chunk_size = str(chunk_size)

def ai_entry(symbol, amount):
    """AI agent entry function for Moon Dev's trading system 🤖"""
    cprint("🤖 Moon Dev's AI Trading Agent initiating position entry...", "white", "on_blue")
    
    # amount passed in is the target allocation (up to 30% of usd_size)
    target_size = amount  # This could be up to $3 (30% of $10)
    
    pos = get_position(symbol)
    price = token_price(symbol)
    pos_usd = pos * price
    
    cprint(f"🎯 Target allocation: ${target_size:.2f} USD (max 30% of ${usd_size})", "white", "on_blue")
    cprint(f"📊 Current position: ${pos_usd:.2f} USD", "white", "on_blue")
    
    # Check if we're already at or above target
    if pos_usd >= (target_size * 0.97):
        cprint("✋ Position already at or above target size!", "white", "on_blue")
        return
        
    # Calculate how much more we need to buy
    size_needed = target_size - pos_usd
    if size_needed <= 0:
        cprint("🛑 No additional size needed", "white", "on_blue")
        return
        
    # For order execution, we'll chunk into max_usd_order_size pieces
    if size_needed > max_usd_order_size: 
        chunk_size = max_usd_order_size
    else: 
        chunk_size = size_needed

    chunk_size = int(chunk_size * 10**6)
    chunk_size = str(chunk_size)
    
    cprint(f"💫 Entry chunk size: {chunk_size} (chunking ${size_needed:.2f} into ${max_usd_order_size:.2f} orders)", "white", "on_blue")

    while pos_usd < (target_size * 0.97):
        cprint(f"🤖 AI Agent executing entry for {symbol[:8]}...", "white", "on_blue")
        print(f"Position: {round(pos,2)} | Price: {round(price,8)} | USD Value: ${round(pos_usd,2)}")

        try:
            for i in range(orders_per_open):
                market_buy(symbol, chunk_size, slippage)
                cprint(f"🚀 AI Agent placed order {i+1}/{orders_per_open} for {symbol[:8]}", "white", "on_blue")
                time.sleep(1)

            time.sleep(tx_sleep)
            
            # Update position info
            pos = get_position(symbol)
            price = token_price(symbol)
            pos_usd = pos * price
            
            # Break if we're at or above target
            if pos_usd >= (target_size * 0.97):
                break
                
            # Recalculate needed size
            size_needed = target_size - pos_usd
            if size_needed <= 0:
                break
                
            # Determine next chunk size
            if size_needed > max_usd_order_size: 
                chunk_size = max_usd_order_size
            else: 
                chunk_size = size_needed
            chunk_size = int(chunk_size * 10**6)
            chunk_size = str(chunk_size)

        except Exception as e:
            try:
                cprint("🔄 AI Agent retrying order in 30 seconds...", "white", "on_blue")
                time.sleep(30)
                for i in range(orders_per_open):
                    market_buy(symbol, chunk_size, slippage)
                    cprint(f"🚀 AI Agent retry order {i+1}/{orders_per_open} for {symbol[:8]}", "white", "on_blue")
                    time.sleep(1)

                time.sleep(tx_sleep)
                pos = get_position(symbol)
                price = token_price(symbol)
                pos_usd = pos * price
                
                if pos_usd >= (target_size * 0.97):
                    break
                    
                size_needed = target_size - pos_usd
                if size_needed <= 0:
                    break
                    
                if size_needed > max_usd_order_size: 
                    chunk_size = max_usd_order_size
                else: 
                    chunk_size = size_needed
                chunk_size = int(chunk_size * 10**6)
                chunk_size = str(chunk_size)

            except:
                cprint("❌ AI Agent encountered critical error, manual intervention needed", "white", "on_red")
                return

    cprint("✨ AI Agent completed position entry", "white", "on_blue")

def get_token_balance_usd(token_mint_address):
    """Get the USD value of a token position for Moon Dev's wallet 🌙"""
    try:
        # Get the position data using existing function
        df = fetch_wallet_token_single(address, token_mint_address)  # Using address from config

        if df.empty:
            print(f"🔍 No position found for {token_mint_address[:8]}")
            return 0.0
            
        # Get the USD Value from the dataframe
        usd_value = df['USD Value'].iloc[0]
        return float(usd_value)
        
    except Exception as e:
        print(f"❌ Error getting token balance: {str(e)}")
        return 0.0

import requests
import numpy as np

def get_trade_prices(trader_address, token_address, offset=0, limit=100, before_time=0, after_time=0):
    """Fetch trades for a given trader and calculate the median price for trades matching the token address."""
    url = f"https://public-api.birdeye.so/trader/txs/seek_by_time?address={trader_address}&offset={offset}&limit={limit}&before_time={before_time}&after_time={after_time}&tx_type=swap"
    headers = {"X-API-KEY": BIRDEYE_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)        
        if response.status_code == 200:
            trades = response.json().get('data', {}).get('items', [])
            matching_prices = []
            
            for trade in trades:                
                # Check if the trade's token address matches the specified token address
                if trade['quote']['address'] == token_address:
                    price = trade['quote'].get('price')
                    amount = trade['quote'].get('amount')
                    change_amount = trade['quote'].get('change_amount')
                    
                    # Ensure price, amount, and change_amount are not None
                    if price is not None and amount is not None and change_amount is not None:
                        if amount == change_amount:
                            matching_prices.append(price)  # Append the price if it exists
            
            if matching_prices:
                # Calculate the median price
                median_price = np.median(matching_prices)
                return median_price
            
            cprint(f"❌ No matching trades found for {trader_address} with token {token_address}.", "red")
            return None
        else:
            cprint(f"❌ Failed to fetch trades for {trader_address}. Status Code: {response.status_code}, Message: {response.json().get('message', 'No message')}", "red")
            return None
            
    except Exception as e:
        cprint(f"❌ Error fetching trades for {trader_address}: {str(e)}", "red")
        return None
    
def get_trending_tokens():
    """Fetch trending tokens from Birdeye API"""
    try:
        endpoint = f"{BASE_URL}/token_trending"
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
        endpoint = "https://api.dexscreener.com/token-profiles/latest/v1"
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
        rugcheck_url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
        rugcheck_response = requests.get(rugcheck_url)
        
        result = {
            'liquidity_locked': False,
            'liquidity_locked_pct': 0,
            'liquidity_locked_usd': 0,
            'liquidity_locked_tokens': 0,
            'total_lp_tokens': 0,
            'markets_found': 0,
            'success': False,
            'error': None
        }
        
        if rugcheck_response.status_code == 200:
            rugcheck_data = rugcheck_response.json()
            
            if 'markets' in rugcheck_data:
                result['markets_found'] = len(rugcheck_data['markets'])
                max_locked_pct = 0
                max_locked_usd = 0
                max_locked_lp = 0
                max_total_lp = 0
                
                for market in rugcheck_data['markets']:
                    if 'lp' in market:
                        lp_data = market['lp']
                        locked_pct = lp_data.get('lpLockedPct', 0)
                        locked_usd = lp_data.get('lpLockedUSD', 0)
                        locked_lp = lp_data.get('lpLocked', 0)
                        total_lp = lp_data.get('lpTotalSupply', 0)
                        
                        if locked_pct > max_locked_pct:
                            max_locked_pct = locked_pct
                            max_locked_usd = locked_usd
                            max_locked_lp = locked_lp
                            max_total_lp = total_lp
                
                result.update({
                    'liquidity_locked': max_locked_pct > 0,
                    'liquidity_locked_pct': max_locked_pct,
                    'liquidity_locked_usd': max_locked_usd,
                    'liquidity_locked_tokens': max_locked_lp,
                    'total_lp_tokens': max_total_lp,
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
            'markets_found': 0
        }
    

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

        # Liquidity lock check (2 points)
        rugcheck_data = check_rugcheck_report(token_address)
        if rugcheck_data['success']:
            if not rugcheck_data['liquidity_locked'] or rugcheck_data['liquidity_locked_pct'] < 50:
                risk_factors["risk_level"] += 2
            # Check for low liquidity (1 point)
            if rugcheck_data.get('liquidity_locked_usd', 0) < 30000:
                risk_factors["risk_level"] += 1
                risk_factors["warnings"].append("🚨 Low liquidity lock value (<$30k)")

        # Update the analysis_result with basic info data
        analysis_result["basic_info"].update({
            "risk_level": risk_factors["risk_level"],
            "token_type": "Token2022 Program" if is_token_2022 else "Standard Token Program",
            "transfer_fee": risk_factors["transfer_fee"],
            "max_transfer_fee": risk_factors["max_transfer_fee"],
            "freeze_authority": risk_factors["freeze_authority"],
            "update_authority": security_info["metaplex_update_authority"],
            "update_authority_is_safe": security_info["metaplex_update_authority"] == PUMP_FUN_ADDRESS,
            "liquidity_lock_percentage": rugcheck_data.get("liquidity_locked_pct", 0),
            "liquidity_lock_usd": rugcheck_data.get("liquidity_locked_usd", 0),
            "is_rugpull": rugcheck_data.get("is_rugpull", False)
        })

        # Get overview data first
        overview_data = token_overview(token_address)
        
        # Then update market data
        analysis_result["market_data"].update({
            "price": overview_data.get("price_usd", 0) if overview_data else 0,
            "market_cap": overview_data.get("mc", 0) if overview_data else 0,
            "total_supply": overview_data.get("total_supply", 0) if overview_data else 0,
            "circulating_supply": overview_data.get("circulating_supply", 0) if overview_data else 0,
            "creation_date": datetime.fromtimestamp(security_info['creation_time']).strftime('%Y-%m-%d %H:%M:%S') if security_info['creation_time'] else "",
            "token_age_days": (datetime.now() - datetime.fromtimestamp(security_info['creation_time'])).days if security_info['creation_time'] else 0
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

        # Print formatted analysis
        cprint("\n📊 Token Analysis:", "white", "on_blue")
        cprint(f"Risk Level: {analysis_result['basic_info']['risk_level']}/10", 
               "green" if analysis_result['basic_info']['risk_level'] < 4 else "yellow" if analysis_result['basic_info']['risk_level'] < 7 else "red")
        cprint(f"Is Rugpull: {analysis_result['basic_info']['is_rugpull']} {'❌' if analysis_result['basic_info']['is_rugpull'] else '✅'}", 
               "red" if analysis_result['basic_info']['is_rugpull'] else "green")
        
        cprint(f"Token Type: {analysis_result['basic_info']['token_type']}", "cyan")
        cprint(f"Transfer Fee: {analysis_result['basic_info']['transfer_fee']}% {'✅' if analysis_result['basic_info']['transfer_fee'] == 0 else '❌'}", 
               "green" if analysis_result['basic_info']['transfer_fee'] == 0 else "red")
        cprint(f"Max Transfer Fee: {analysis_result['basic_info']['max_transfer_fee']} {'✅' if float(analysis_result['basic_info']['max_transfer_fee']) == 0 else '❌'}", 
               "green" if float(analysis_result['basic_info']['max_transfer_fee']) == 0 else "red")
        cprint(f"Freeze Authority: {analysis_result['basic_info']['freeze_authority']} {'✅' if not analysis_result['basic_info']['freeze_authority'] else '❌'}", 
               "green" if not analysis_result['basic_info']['freeze_authority'] else "red")
        cprint(f"Update Authority: {analysis_result['basic_info']['update_authority']} {'✅' if analysis_result['basic_info']['update_authority_is_safe'] else '❌'}", 
               "green" if analysis_result['basic_info']['update_authority_is_safe'] else "red")
        cprint(f"Liquidity Lock: {analysis_result['basic_info']['liquidity_lock_percentage']}% (${analysis_result['basic_info']['liquidity_lock_usd']:,.2f}) {'✅' if analysis_result['basic_info']['liquidity_lock_percentage'] >= 50 else '❌'}", 
               "green" if analysis_result['basic_info']['liquidity_lock_percentage'] >= 50 else "red")
        cprint(f"Supply Concentration: {analysis_result['basic_info']['supply_concentration']:.1f}% {'✅' if analysis_result['basic_info']['supply_concentration'] <= 50 else '❌'}", 
               "green" if analysis_result['basic_info']['supply_concentration'] <= 50 else "red")

        # Print any warnings
        if risk_factors["warnings"]:
            cprint("\n⚠️ Warnings:", "yellow")
            for warning in risk_factors["warnings"]:
                cprint(f"  • {warning}", "yellow")

        cprint("\nMarket Data:", "cyan")
        cprint(f"Price: ${analysis_result['market_data']['price']:,.12f}", "white")
        cprint(f"Market Cap: ${analysis_result['market_data']['market_cap']:,.2f}", "white")
        cprint(f"Total Supply: {analysis_result['market_data']['total_supply']:,.0f}", "white")
        cprint(f"Circulating Supply: {analysis_result['market_data']['circulating_supply']:,.0f}", "white")
        cprint(f"Creation Date: {analysis_result['market_data']['creation_date']}", "white")
        cprint(f"Token Age: {analysis_result['market_data']['token_age_days']} days", "white")

        cprint("\n30m Trading Activity:", "cyan")
        cprint(f"Price Change: {analysis_result['trading_activity_30m']['price_change']:+.2f}%", 
               "green" if analysis_result['trading_activity_30m']['price_change'] >= 0 else "red")
        cprint(f"Buys: {analysis_result['trading_activity_30m']['buys']}", "white")
        cprint(f"Sells: {analysis_result['trading_activity_30m']['sells']}", "white")
        cprint(f"Buy Volume: ${analysis_result['trading_activity_30m']['buy_volume']:,.2f}", "white")
        cprint(f"Sell Volume: ${analysis_result['trading_activity_30m']['sell_volume']:,.2f}", "white")
        cprint(f"Unique Wallets: {analysis_result['trading_activity_30m']['unique_wallets']}", "white")

        cprint("✅ Analysis completed", "green")

        return analysis_result

    except Exception as e:
        cprint(f"\n❌ Error in token analysis: {str(e)}", "red")
        return None
