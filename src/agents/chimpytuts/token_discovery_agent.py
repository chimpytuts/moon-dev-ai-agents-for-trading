"""
Token Discovery Agent
Analyzes new tokens using rugpull risk checks and AI evaluation
"""

import anthropic
import os
from termcolor import cprint
from dotenv import load_dotenv
from src import nice_funcs as n
from src.config import MAX_TOKENS_TO_BE_MONITORED, MONITORED_TOKENS

load_dotenv()

TOKEN_EVALUATION_PROMPT = """
You are a Token Analysis Expert. Based on the provided token analysis data, score this token's potential from 0-100, balancing both safety and profit potential.

CURRENT TOKEN ANALYSIS:
{risk_analysis}

RISK SCORING SYSTEM:
Risk Level Breakdown (0-10 points):
• Supply concentration >50%: +3 points
• Update Authority not safe: +1 point
• Freeze Authority enabled: +1 point
• Mint Authority enabled: +1 point
• Transfer Fee >0%: +1 point
• Liquidity not locked or <50%: +2 points
• LOW LIQUIDITY WARNING: If locked value < $30,000: +1 point

Risk Categories:
• 0-3: Low Risk (Safest)
• 4-6: Medium Risk
• 7-10: High Risk (Dangerous)

CRITICAL SAFETY REQUIREMENTS (ALL must be met for high score):
1. Transfer Fee MUST BE 0%
2. Freeze Authority MUST BE false
3. Update Authority MUST BE either:
   - false (no authority)
   - OR exactly "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM"
4. Liquidity Lock MUST MEET BOTH:
   - Percentage MUST BE >50%
   - USD Value MUST BE >$30,000 (STRICT REQUIREMENT)
5. Supply Concentration MUST BE <50%

SCORING GUIDELINES:
High scores (80-100) REQUIRES:
• Risk level 0-3
• Liquidity STRICTLY >$30,000
• Active trading volume
• Growing unique wallets
• Reasonable market cap for growth

Medium scores (50-79) if:
• Risk level 4-6
• Decent liquidity but below $30,000
• Some trading activity
• Growth potential exists

Low scores (0-49) if ANY of:
• Risk level 7-10
• Poor liquidity (<$15,000)
• Low trading activity
• High risk indicators
• ANY critical safety requirement not met

IMPORTANT: A token with liquidity below $30,000 CANNOT receive a score above 79, regardless of other factors.

Provide your evaluation in this format:
1. First line must be a score from 0-100 (weighted security and profit potential)
   • Security Score Component (60% of total):
     - Risk level impact (0-3: excellent, 4-6: moderate, 7-10: poor)
     - Safety requirements met/failed
     - Liquidity security assessment
     - Supply concentration safety
     - Authority settings safety

   • Profit Potential Component (40% of total):
     - Market cap growth potential
     - Trading metrics strength (buys vs sells)
     - Volume and wallet trends
     - Supply and age factors
     - Price action momentum

2. Detailed analysis must include:
   a) SECURITY ASSESSMENT (60%):
      - Exact risk level (X/10) with breakdown of risk factors
      - Liquidity analysis (EXACT $ value and %)
      - List of any failed safety requirements
      
   b) PROFIT POTENTIAL ASSESSMENT (40%):
      - Market cap analysis and growth projection
      - 30m trading metrics evaluation:
        • Buy/Sell ratio significance
        • Volume trend analysis
        • Wallet growth assessment
      - Token age and supply impact
      
   c) FINAL RECOMMENDATION:
      - Clear buy/avoid decision
      - Entry point suggestion if buy
      - Specific reasons based on weighted security (60%) and profit (40%) metrics
      - Key risks and growth catalysts

Example scoring:
• Perfect security (60/60) + Strong profit metrics (35/40) = 95
• Good security (50/60) + Good profit metrics (30/40) = 80
• Medium security (40/60) + Great profit metrics (38/40) = 78
• Poor security (30/60) + Amazing profit metrics (40/40) = 70
• Failed critical safety = Automatic score below 40 regardless of profit potential
"""

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
            new_tokens = n.get_new_listings()
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
                            risk_analysis = n.check_rugpull_risk_rpc(token)
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
                        cprint(final_prompt, "white")
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
            cprint(f"❌ Error in token analysis: {str(e)}", "red")
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