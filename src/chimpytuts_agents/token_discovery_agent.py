"""
Token Discovery Agent
Analyzes new tokens using rugpull risk checks and AI evaluation
"""

import anthropic
import os
import time
from termcolor import cprint
from dotenv import load_dotenv
from .utils.token_discovery_utils import get_new_listings, check_rugpull_risk_rpc
from src.config import MAX_TOKENS_TO_BE_MONITORED
from .prompts.token_discorver_prompt import TOKEN_EVALUATION_PROMPT  # Added this import

load_dotenv()

class TokenDiscoveryAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
        self.analyzed_tokens = []
        cprint("Token Discovery Agent initialized", "cyan")

    def analyze_tokens(self):
        """Main discovery and analysis process"""
        try:
            # Get new listings
            cprint("\n🔍 Fetching new token listings...", "cyan")
            new_tokens = get_new_listings()
            if not new_tokens:
                cprint("No new tokens found", "yellow")
                return []
                
            cprint(f"Found {len(new_tokens)} new tokens", "cyan")

            # Analyze each token
            for token in new_tokens:
                try:
                    cprint(f"\n📊 Analyzing token: {token}", "yellow")
                    
                    # Get risk analysis with retry
                    max_retries = 3
                    risk_analysis = None
                    
                    for attempt in range(max_retries):
                        try:
                            risk_analysis = check_rugpull_risk_rpc(token)
                            if risk_analysis:
                                break
                            time.sleep(2)  # Wait 2 seconds between retries
                        except Exception as e:
                            cprint(f"Attempt {attempt + 1} failed: {str(e)}", "yellow")
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                            else:
                                raise
                    
                    if not risk_analysis:
                        cprint(f"❌ Failed to get risk analysis for {token} after {max_retries} attempts", "red")
                        continue

                    # Get AI evaluation
                    try:
                        formatted_analysis = self.format_risk_analysis(risk_analysis)
                        final_prompt = TOKEN_EVALUATION_PROMPT.format(
                            risk_analysis=formatted_analysis
                        )
                        
                        # Debug print the complete prompt
                        cprint("\n🤖 Sending prompt to Claude:", "cyan")
                        cprint("-" * 80, "cyan")
                  #      cprint(final_prompt, "white")
                        cprint("-" * 80, "cyan")
                        
                        message = self.client.messages.create(
                            model="claude-3-sonnet-20240229",
                            max_tokens=1000,
                            temperature=0.7,
                            messages=[{
                                "role": "user",
                                "content": final_prompt
                            }]
                        )
                        
                        # Parse score and analysis from the message content
                        response_text = message.content[0].text.strip()
                        cprint("\n🤖 Claude Response:", "cyan")
                        cprint(response_text, "white")
                        response_lines = response_text.split('\n')
                        
                        try:
                            # Try to extract the score from the first line
                            score = int(''.join(filter(str.isdigit, response_lines[0])))
                            if score > 100:  # Sanity check
                                score = 100
                        except (ValueError, IndexError):
                            cprint("❌ Could not parse score from AI response", "red")
                            cprint(f"Response was: {response_lines[0] if response_lines else 'Empty response'}", "yellow")
                            score = 0
                            
                        analysis = '\n'.join(response_lines[1:]) if len(response_lines) > 1 else "No analysis provided"
                        
                        self.analyzed_tokens.append({
                            'address': token,
                            'score': score,
                            'analysis': analysis,
                            'risk_analysis': risk_analysis
                        })
                        
                        cprint(f"Token Score: {score}/100", "green" if score > 70 else "yellow" if score > 50 else "red")
                        
                    except Exception as e:
                        cprint(f"❌ Error getting AI evaluation: {str(e)}", "red")
                        cprint(f"Full response: {message.content if 'message' in locals() else 'No response'}", "yellow")
                        continue
                        
                except Exception as e:
                    cprint(f"❌ Error analyzing token {token}: {str(e)}", "red")
                    continue

            # Sort tokens by score and get top ones
            self.analyzed_tokens.sort(key=lambda x: x['score'], reverse=True)
            top_tokens = self.analyzed_tokens[:MAX_TOKENS_TO_BE_MONITORED]

            # Update MONITORED_TOKENS in config
            if top_tokens:
                new_monitored = [token['address'] for token in top_tokens]
                self.update_monitored_tokens(new_monitored)
                
                # Print summary of selected tokens
                cprint("\n🌟 Selected Tokens for Monitoring:", "green")
                for token in top_tokens:
                    cprint(f"\nToken: {token['address']}", "cyan")
                    cprint(f"Score: {token['score']}/100", "green" if token['score'] > 70 else "yellow")
                    cprint("Analysis:", "white")
                    cprint(token['analysis'], "white")

            return top_tokens

        except Exception as e:
            cprint(f"❌ Error in token analysis Agent: {str(e)}", "red")
            return []

    def update_monitored_tokens(self, new_tokens):
        """Update the MONITORED_TOKENS list in config.py"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.py')
            
            # Read with utf-8 encoding
            with open(config_path, 'r', encoding='utf-8') as file:
                config_content = file.read()

            # Find the MONITORED_TOKENS section and update it
            start_marker = "MONITORED_TOKENS = ["
            end_marker = "]"
            
            start_idx = config_content.find(start_marker)
            end_idx = config_content.find(end_marker, start_idx) + 1
            
            if start_idx != -1 and end_idx != -1:
                # Create new tokens string without emojis
                new_tokens_str = "MONITORED_TOKENS = [\n"
                for token in new_tokens:
                    new_tokens_str += f"    '{token}',    # New discovered token\n"
                new_tokens_str += "]"
                
                new_config = config_content[:start_idx] + new_tokens_str + config_content[end_idx:]
                
                # Write with utf-8 encoding
                with open(config_path, 'w', encoding='utf-8') as file:
                    file.write(new_config)
                    
                cprint("✅ Successfully updated MONITORED_TOKENS in config.py", "green")
            else:
                cprint("❌ Could not find MONITORED_TOKENS in config.py", "red")

        except Exception as e:
            cprint(f"❌ Error updating config.py: {str(e)}", "red")

    def format_risk_analysis(self, analysis):
        return f"""
SECURITY METRICS:
• Risk Level: {analysis['basic_info']['risk_level']}/10
• Token Type: {analysis['basic_info']['token_type']}
• Transfer Fee: {analysis['basic_info']['transfer_fee']}%
• Max Transfer Fee: {analysis['basic_info']['max_transfer_fee']}
• Freeze Authority: {analysis['basic_info']['freeze_authority']}
• Update Authority: {analysis['basic_info']['update_authority']}
• Mint Authority: {analysis['basic_info'].get('mint_authority', False)}
• Liquidity Lock: {analysis['basic_info']['liquidity_lock_percentage']}% (${analysis['basic_info']['liquidity_lock_usd']:,.2f})
• Supply Concentration: {analysis['basic_info']['supply_concentration']:.1f}%
• Is Rugpull: {analysis['basic_info']['is_rugpull']}

MARKET DATA:
• Current Price: ${analysis['market_data']['price']:,.12f}
• Market Cap: ${analysis['market_data']['market_cap']:,.2f}
• Total Supply: {analysis['market_data']['total_supply']:,.0f}
• Circulating Supply: {analysis['market_data']['circulating_supply']:,.0f}
• Creation Date: {analysis['market_data']['creation_date']}
• Token Age: {analysis['market_data']['token_age_days']} days

30M TRADING ACTIVITY:
• Price Change: {analysis['trading_activity_30m']['price_change']:+.2f}%
• Buys: {analysis['trading_activity_30m']['buys']}
• Sells: {analysis['trading_activity_30m']['sells']}
• Buy Volume: ${analysis['trading_activity_30m']['buy_volume']:,.2f}
• Sell Volume: ${analysis['trading_activity_30m']['sell_volume']:,.2f}
• Unique Wallets: {analysis['trading_activity_30m']['unique_wallets']}
"""

def main():
    agent = TokenDiscoveryAgent()
    agent.analyze_tokens()

if __name__ == "__main__":
    main() 