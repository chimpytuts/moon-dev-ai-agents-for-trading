import anthropic
import os
import pandas as pd
import json
from termcolor import colored, cprint
from dotenv import load_dotenv
from src import config
from src import nice_funcs as n
from .utils.trading_agent_utils import collect_all_tokens
from datetime import datetime, timedelta
import time
from src.config import *
from src.agents.base_agent import BaseAgent
from .prompts.risk_prompt import RISK_OVERRIDE_PROMPT  # Added this import

# Load environment variables
load_dotenv()

class RiskAgent():
    def __init__(self):
        """Initialize Moon Dev's Risk Agent 🛡️"""
        
        api_key = os.getenv("ANTHROPIC_KEY")
        if not api_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        self.client = anthropic.Anthropic(api_key=api_key)
        self.override_active = False
        self.last_override_check = None
        
        # Initialize start balance using portfolio value
        self.start_balance = self.get_portfolio_value()
        print(f"🏦 Initial Portfolio Balance: ${self.start_balance:.2f}")
        
        self.current_value = self.start_balance
        cprint("🛡️ Risk Agent initialized!", "white", "on_blue")
        
    def calculate_start_balance(self):
        """Calculate the start balance based on token holdings and their purchase prices."""
        try:
            # Fetch current holdings using existing function
            holdings = n.fetch_wallet_holdings_og(address)  # Use your existing function
            total_start_balance = 0.0
            excluded_tokens_value = 0.0  # Initialize variable for excluded tokens' USD value

            for index, row in holdings.iterrows():
                token = row['Mint Address']
                amount = row['Amount']
                
                # Skip excluded tokens
                if token in EXCLUDED_TOKENS:
                    if token != SOL_ADDRESS:  # Changed !== to !=
                        excluded_tokens_value += row['USD Value']  # Add USD Value of excluded tokens
                    continue
                
                # Fetch the median price for the token using the change amount
                change_amount = amount  # Assuming you want to use the current amount as the change amount
                median_price = n.get_trade_prices(address, token)  # Use the updated function
                
                if median_price is not None:
                    total_start_balance += amount * median_price
            
            # Add the USD value of excluded tokens to the total start balance
            total_start_balance += excluded_tokens_value
            
            return total_start_balance
        
        except Exception as e:
            cprint(f"❌ Error calculating start balance: {str(e)}", "red")
            return 0.0

    def get_portfolio_value(self):
        """Calculate total portfolio value in USD"""
        total_value = 0.0
        
        try:
            # Get USDC balance first
            usdc_value = n.get_token_balance_usd(config.USDC_ADDRESS)
            total_value += usdc_value
            

            # Get balance of each monitored token
            for token in config.MONITORED_TOKENS:
                if token != config.USDC_ADDRESS:  # Skip USDC as we already counted it
                    token_value = n.get_token_balance_usd(token)
                    total_value += token_value
                    
            return total_value
            
        except Exception as e:
            cprint(f"❌ Error calculating portfolio value: {str(e)}", "white", "on_red")
            return 0.0

    def log_daily_balance(self):
        """Log portfolio value if not logged in past check period"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('src/data', exist_ok=True)
            balance_file = 'src/data/portfolio_balance.csv'
            
            # Check if we already have a recent log
            if os.path.exists(balance_file):
                df = pd.read_csv(balance_file)
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    last_log = df['timestamp'].max()
                    hours_since_log = (datetime.now() - last_log).total_seconds() / 3600
                    
                    if hours_since_log < config.MAX_LOSS_GAIN_CHECK_HOURS:
                        cprint(f"✨ Recent balance log found ({hours_since_log:.1f} hours ago)", "white", "on_blue")
                        return
            else:
                df = pd.DataFrame(columns=['timestamp', 'balance'])
            
            # Get current portfolio value
            current_value = self.get_portfolio_value()
            
            # Add new row
            new_row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance': current_value
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save updated log
            df.to_csv(balance_file, index=False)
            cprint(f"💾 New portfolio balance logged: ${current_value:.2f}", "white", "on_green")
            
        except Exception as e:
            cprint(f"❌ Error logging balance: {str(e)}", "white", "on_red")

    def get_position_data_5m(self, token):
        """Get recent market data for a token"""
        try:           
            # Get 2h of 5m data
            data_5m = n.get_data(token, 0.083, '5m')   # 2 hours = 0.083 days
            
            return {
                '5m': data_5m.to_dict() if data_5m is not None else None
            }
        except Exception as e:
            cprint(f"❌ Error getting data for {token}: {str(e)}", "white", "on_red")
            return None

    def get_position_data_15m(self, token):
        """Get recent market data for a token"""
        try:
            # Get 8h of 15m data
            data_15m = n.get_data(token, 0.33, '15m')  # 8 hours = 0.33 days            
            return {
                '15m': data_15m.to_dict() if data_15m is not None else None,
            }
        except Exception as e:
            cprint(f"❌ Error getting data for {token}: {str(e)}", "white", "on_red")
            return None

    def close_position(self, token):
        """Close a specific position."""
        try:
            cprint(f"💰 Closing position for {token}...", "white", "on_cyan")
            n.chunk_kill(token, slippage)  # Close the position
            cprint(f"✅ Successfully closed position for {token}", "white", "on_green")
        except Exception as e:
            cprint(f"❌ Error closing position for {token}: {str(e)}", "white", "on_red")

    def should_override_limit(self, limit_type):
        """Ask AI if we should override the limit based on recent market data"""
        try:
            # Get current positions first
            positions = n.fetch_wallet_holdings_og(address)
            
            # Filter for tokens that are both in MONITORED_TOKENS and in our positions
            positions = positions[
                positions['Mint Address'].isin(TOKENS_TO_SELL) & 
                ~positions['Mint Address'].isin(EXCLUDED_TOKENS)
            ]
            
            if positions.empty:
                cprint("❌ No monitored positions found to analyze", "white", "on_red")
                return
            # Collect data only for monitored tokens we have positions in
            position_data_5m = {}
            position_data_15m = {}

            for _, row in positions.iterrows():
                token = row['Mint Address']
                current_value = row['USD Value']
                purchase_price = n.get_trade_prices(address, token)  # Assuming you have this data
                amount = row['Amount']
                start_value = amount * purchase_price
                types = ""
                why = ""

                # Calculate loss and gain percentages
                percent_change = ((current_value - start_value) / start_value) * 100
                usd_change = current_value - start_value

                # Log the start of analysis for the token
                cprint(f"🔍 Starting analysis for token: {token}", "white", "on_blue")

                if limit_type == "percentage" and percent_change <= -MAX_LOSS_PERCENT_PER_POSITION:
                    types = "SELL"
                    why = f"Sell position for {token} because the loss exceeds the maximum allowed limit of {MAX_LOSS_PERCENT_PER_POSITION}%. Current loss: {percent_change:.2f}%."
                    cprint(f"\n🛑 MAXIMUM LOSS PERCENTAGE REACHED FOR TOKEN {token}", "white", "on_red")
                    cprint(f"📉 Loss: {percent_change:.2f}% (Limit: {MAX_LOSS_PERCENT_PER_POSITION}%)", "red")
                    
                # Check if we should close the position based on loss thresholds
                if limit_type == "USD" and usd_change <= -MAX_LOSS_USD_PER_POSITION:
                    types = "SELL"
                    why = f"Sell position for {token} because the loss exceeds the maximum allowed limit of ${-MAX_LOSS_USD_PER_POSITION:.2f}. Current loss: ${usd_change:.2f}."
                    cprint(f"\n🛑 MAXIMUM LOSS USD REACHED FOR TOKEN {token}", "white", "on_red")
                    cprint(f"📉 Loss: ${usd_change:.2f} (Limit: ${MAX_LOSS_USD_PER_POSITION})", "red")

                # Check if we should keep the position open based on gain thresholds
                if limit_type == "percentage" and percent_change >= MAX_GAIN_PERCENT_PER_POSITION:
                    types = "SELL"
                    why = f"Consider selling position for {token} because the gain has reached the maximum allowed limit of {MAX_GAIN_PERCENT_PER_POSITION}%. Current gain: +{percent_change:.2f}%."
                    cprint(f"\n🎯 MAXIMUM GAIN PERCENTAGE REACHED FOR TOKEN {token}", "white", "on_red")
                    cprint(f"📈 Gain: {percent_change:.2f}% (Limit: {MAX_GAIN_PERCENT_PER_POSITION}%)", "red")

                if limit_type == "USD" and usd_change >= MAX_GAIN_USD_PER_POSITION:
                    types = "SELL"
                    why = f"Consider selling position for {token} because the gain has reached the maximum allowed limit of ${MAX_GAIN_USD_PER_POSITION:.2f}. Current gain: +${usd_change:.2f}."
                    cprint(f"\n🎯 MAXIMUM GAIN USD REACHED FOR TOKEN {token}", "white", "on_red")
                    cprint(f"📈 Gain: ${usd_change:.2f} (Limit: ${MAX_GAIN_USD_PER_POSITION})", "red")

                # New conditions to keep the position if within the limits
                if limit_type == "percentage" and -MAX_LOSS_PERCENT_PER_POSITION < percent_change < MAX_GAIN_PERCENT_PER_POSITION:
                    types = "KEEP"
                    why = f"Keep position for {token} because the current percentage change is within the allowed limits. Current change: {percent_change:.2f}%. Limits are set to -{MAX_LOSS_PERCENT_PER_POSITION}% (max loss) and +{MAX_GAIN_PERCENT_PER_POSITION}% (max gain)."
                    cprint(f"\n✅ Position for {token} is within the allowed percentage limits.", "white", "on_yellow")

                if limit_type == "USD" and -MAX_LOSS_USD_PER_POSITION < usd_change < MAX_GAIN_USD_PER_POSITION:
                    types = "KEEP"
                    why = f"Keep position for {token} because the current USD change is within the allowed limits. Current change: ${usd_change:.2f}. Limits are set to -${MAX_LOSS_USD_PER_POSITION:.2f} (max loss) and +${MAX_GAIN_USD_PER_POSITION:.2f} (max gain)."
                    cprint(f"\n✅ Position for {token} is within the allowed USD limits.", "white", "on_yellow")
                
                # Format data for AI analysis for each token
                token_data_5m = {
                    'data': self.get_position_data_5m(token)  # Get the raw data
                }
                token_data_15m = {
                    'data': self.get_position_data_15m(token)  # Get the raw data
                }
                 
                position_data_5m[token] = token_data_5m
                position_data_15m[token] = token_data_15m
                # Format prompt for AI analysis
                prompt = RISK_OVERRIDE_PROMPT.format(
                    limit_type=limit_type,
                    position_data_5m=json.dumps({token: token_data_5m}, indent=2),  # Send data for the specific token
                    position_data_15m=json.dumps({token: token_data_15m}, indent=2),  # Send data for the specific token
                    start_value = start_value,
                    current_value = current_value,
                    percent_change = percent_change,
                    usd_change = usd_change,
                    type=types,
                    why=why

                )

                cprint(f"🤖 AI Agent analyzing market data for {token}...", "white", "on_green")
                message = self.client.messages.create(
                    model=config.AI_MODEL,
                    max_tokens=config.AI_MAX_TOKENS,
                    temperature=config.AI_TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Get the response content and ensure it's a string
                response_text = message.content[0].text.strip()
                cprint("\n🧠 Risk Agent Analysis:", "cyan")
                cprint(response_text, "white")

                # Parse the AI's decision from the response
                decision = None
                if "RESPECT_LIMIT" in response_text:
                    decision = "SELL"
                elif "OVERRIDE_LIMIT" in response_text:
                    decision = "KEEP"
        
                if decision == "SELL":
                    cprint(f"\n🛡️ Risk Agent recommends closing position for {token}", "white", "on_red")
                    self.close_position(token)  # Close the position if AI suggests it
                elif decision == "KEEP":
                    cprint(f"\n🤖 Risk Agent suggests keeping position for {token} open", "white", "on_yellow")
                else:
                    cprint(f"\n⚠️ Could not determine clear recommendation from AI. Defaulting to respect limit (SELL)", "white", "on_red")
                    self.close_position(token)  # Default to closing position if unclear

        except Exception as e:
            cprint(f"❌ Error in override check: {str(e)}", "white", "on_red")
            return

    def check_pnl_limits(self):
        """Check if PnL limits have been hit"""
        try:
            self.current_value = self.get_portfolio_value()

            # Check if there are any monitored tokens in the current value
            holdings = n.fetch_wallet_holdings_og(address)  # Fetch current holdings
            monitored_positions = holdings[holdings['Mint Address'].isin(MONITORED_TOKENS)]

            if monitored_positions.empty:
                cprint("❌ No monitored tokens found in current holdings.", "white", "on_red")
                return False  # Return false if no monitored tokens are present

            cprint(f"📊 Full Portfolio Current USD Value: ${self.current_value:.2f}", "white", "on_blue")
            cprint(f"📈 Full Portfolio Start USD Value: ${self.start_balance:.2f}", "white", "on_blue")
            percent_change = ((self.current_value - self.start_balance) / self.start_balance) * 100
            cprint(f"🔄 Portfolio Change: {percent_change:.2f}% since the start", "white", "on_yellow")
            usd_change = self.current_value - self.start_balance
            cprint(f"🔄 UsD Change: {usd_change:.2f} USD since the start", "white", "on_yellow")

            if USE_PERCENTAGE:
                # Calculate percentage change
                if percent_change <= -MAX_LOSS_PERCENT:
                    cprint("\n🛑 MAXIMUM LOSS PERCENTAGE REACHED FOR FULL PORTFOLIO", "white", "on_red")
                    cprint(f"📉 Loss: {percent_change:.2f}% (Limit: {MAX_LOSS_PERCENT}%)", "red")
                    return True
                    
                if percent_change >= MAX_GAIN_PERCENT:
                    cprint("\n🎯 MAXIMUM GAIN PERCENTAGE REACHED FOR FULL PORTFOLIO", "white", "on_green")
                    cprint(f"📈 Gain: {percent_change:.2f}% (Limit: {MAX_GAIN_PERCENT}%)", "green")
                    return True
                       
            else:
                # Calculate USD change
                if usd_change <= -MAX_LOSS_USD:
                    cprint("\n🛑 MAXIMUM LOSS USD REACHED FOR FULL PORTFOLIO", "white", "on_red")
                    cprint(f"📉 Loss: ${abs(usd_change):.2f} (Limit: ${MAX_LOSS_USD:.2f})", "red")
                    return True
                    
                if usd_change >= MAX_GAIN_USD:
                    cprint("\n🎯 MAXIMUM GAIN USD REACHED FOR FULL PORTFOLIO", "white", "on_green")
                    cprint(f"📈 Gain: ${usd_change:.2f} (Limit: ${MAX_GAIN_USD:.2f})", "green")
                    return True
            
            return False
            
        except Exception as e:
            cprint(f"❌ Error checking PnL limits: {e}", "red")
            return False

    def close_all_positions(self):
        """Close all monitored positions except USDC and SOL"""
        try:
            cprint("\n🔄 Closing monitored positions...", "white", "on_cyan")
            
            # Get all positions
            positions = n.fetch_wallet_holdings_og(address)
            
            # Debug print to see what we're working with
            cprint("\n📊 Current positions:", "cyan")
            print(positions)
            cprint("\n🎯 Monitored tokens:", "cyan")
            print(MONITORED_TOKENS)
            
            # Filter for tokens that are both in MONITORED_TOKENS and not in EXCLUDED_TOKENS
            positions = positions[
                positions['Mint Address'].isin(MONITORED_TOKENS) & 
                ~positions['Mint Address'].isin(EXCLUDED_TOKENS)
            ]
            
            if positions.empty:
                cprint("📝 No monitored positions to close", "white", "on_blue")
                return
                
            # Close each monitored position
            for _, row in positions.iterrows():
                token = row['Mint Address']
                value = row['USD Value']
                
                cprint(f"\n💰 Closing position: {token} (${value:.2f})", "white", "on_cyan")
                try:
                    n.chunk_kill(token, slippage)
                    cprint(f"✅ Successfully closed position for {token}", "white", "on_green")
                except Exception as e:
                    cprint(f"❌ Error closing position for {token}: {str(e)}", "white", "on_red")
                    
            cprint("\n✨ All monitored positions closed", "white", "on_green")
            
        except Exception as e:
            cprint(f"❌ Error in close_all_positions: {str(e)}", "white", "on_red")

    def check_risk_limits(self):
        """Check if any risk limits have been breached"""
        try:
            # Get current PnL
            current_pnl = self.get_current_pnl()
            current_balance = self.get_portfolio_value()
            
            print(f"\n💰 Current PnL: ${current_pnl:.2f}")
            print(f"💼 Current Balance: ${current_balance:.2f}")
            print(f"📉 Minimum Balance Limit: ${MINIMUM_BALANCE_USD:.2f}")
            
            # Check minimum balance limit
            if current_balance < MINIMUM_BALANCE_USD:
                print(f"⚠️ ALERT: Current balance ${current_balance:.2f} is below minimum ${MINIMUM_BALANCE_USD:.2f}")
                self.handle_limit_breach("MINIMUM_BALANCE", current_balance)
                return True
            
            # Check PnL limits
            if USE_PERCENTAGE:
                if abs(current_pnl) >= MAX_LOSS_PERCENT:
                    print(f"⚠️ PnL limit reached: {current_pnl}%")
                    self.handle_limit_breach("PNL_PERCENT", current_pnl)
                    return True
            else:
                if abs(current_pnl) >= MAX_LOSS_USD:
                    print(f"⚠️ PnL limit reached: ${current_pnl:.2f}")
                    self.handle_limit_breach("PNL_USD", current_pnl)
                    return True
                    
            print("✅ All risk limits OK")
            return False
            
        except Exception as e:
            print(f"❌ Error checking risk limits: {str(e)}")
            return False
            
    def handle_limit_breach(self, breach_type, current_value):
        """Handle breached risk limits with AI consultation if enabled"""
        try:
            # If AI confirmation is disabled, close positions immediately
            if not USE_AI_CONFIRMATION:
                print(f"\n🚨 {breach_type} limit breached! Closing all positions immediately...")
                print(f"💡 (AI confirmation disabled in config)")
                self.close_all_positions()
                return
                
            # Get all current positions using fetch_wallet_holdings_og
            positions_df = n.fetch_wallet_holdings_og(address)
            
            # Prepare breach context
            if breach_type == "MINIMUM_BALANCE":
                context = f"Current balance (${current_value:.2f}) has fallen below minimum balance limit (${MINIMUM_BALANCE_USD:.2f})"
            elif breach_type == "PNL_USD":
                context = f"Current PnL (${current_value:.2f}) has exceeded USD limit (${MAX_LOSS_USD:.2f})"
            else:
                context = f"Current PnL ({current_value}%) has exceeded percentage limit ({MAX_LOSS_PERCENT}%)"
            
            # Format positions for AI
            positions_str = "\nCurrent Positions:\n"
            for _, row in positions_df.iterrows():
                if row['USD Value'] > 0:
                    positions_str += f"- {row['Mint Address']}: {row['Amount']} (${row['USD Value']:.2f})\n"
                    
            # Get AI recommendation
            prompt = f"""
🚨 RISK LIMIT BREACH ALERT 🚨

{context}

{positions_str}

Should we close all positions immediately? Consider:
1. Market conditions
2. Position sizes
3. Recent price action
4. Risk of further losses

Respond with:
CLOSE_ALL or HOLD_POSITIONS
Then explain your reasoning.
"""
            # Get AI decision
            message = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response = message.content
            if isinstance(response, list):
                response = '\n'.join([item.text if hasattr(item, 'text') else str(item) for item in response])
            
            print("\n🤖 AI Risk Assessment:")
            print("=" * 50)
            print(response)
            print("=" * 50)
            
            # Parse decision
            decision = response.split('\n')[0].strip()
            
            if decision == "CLOSE_ALL":
                print("🚨 AI recommends closing all positions!")
                self.close_all_positions()
            else:
                print("✋ AI recommends holding positions despite breach")
                
        except Exception as e:
            print(f"❌ Error handling limit breach: {str(e)}")
            # Default to closing positions on error
            print("⚠️ Error in AI consultation - defaulting to close all positions")
            self.close_all_positions()

    def get_current_pnl(self):
        """Calculate current PnL based on start balance"""
        try:
            current_value = self.get_portfolio_value()
            print(f"\n💰 Start Balance: ${self.start_balance:.2f}")
            print(f"📊 Current Value: ${current_value:.2f}")
            
            pnl = current_value - self.start_balance
            print(f"📈 Current PnL: ${pnl:.2f}")
            return pnl
            
        except Exception as e:
            print(f"❌ Error calculating PnL: {str(e)}")
            return 0.0