"""
Token Discovery Agent
Analyzes new and trending tokens using rugpull risk checks and AI evaluation
"""

import anthropic
import os
import pandas as pd
from termcolor import cprint
from dotenv import load_dotenv
from src import nice_funcs as n

load_dotenv()

TOKEN_EVALUATION_PROMPT = """
You are a Token Analysis Expert. Evaluate the provided token data and risk analysis to score its potential.

Token Analysis Data:
{token_data}

Risk Analysis Results:
{risk_analysis}

Provide your evaluation in this format:
1. First line must be a score from 0-100
2. Then explain your reasoning, including:
   - Risk factor analysis
   - Token program evaluation
   - Authority settings assessment
   - Trading capabilities
   - Supply distribution
   - Overall safety rating

Focus on:
- Token program type and implementation
- Risk level and specific concerns
- Authority settings and their implications
- Trading functionality (buy/sell capability)
- Supply concentration risks
"""

class TokenDiscoveryAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
        self.tokens_df = pd.DataFrame(columns=['token', 'score', 'analysis', 'risk_level'])
        cprint("Token Discovery Agent initialized", "cyan")

    def discover_new_tokens(self):
        """Get new and trending tokens"""
        new_tokens = n.get_new_listings()
        trending_tokens = n.get_trending_tokens()
        return list(set(new_tokens + trending_tokens))

    def analyze_token(self, token_address):
        """Analyze a single token"""
        try:
            # Get risk analysis
            risk_analysis = n.check_rugpull_risk_rpc(token_address)
            if not risk_analysis:
                return None

            # Get AI evaluation
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": TOKEN_EVALUATION_PROMPT.format(
                        token_data=token_address,
                        risk_analysis=risk_analysis
                    )
                }]
            )

            # Parse response
            response = message.content
            lines = response.split('\n')
            score = int(lines[0].strip()) if lines else 0
            analysis = '\n'.join(lines[1:]) if len(lines) > 1 else "No analysis provided"

            # Add to DataFrame
            self.tokens_df = pd.concat([
                self.tokens_df,
                pd.DataFrame([{
                    'token': token_address,
                    'score': score,
                    'analysis': analysis,
                    'risk_level': risk_analysis['risk_level']
                }])
            ], ignore_index=True)

            return {
                'token': token_address,
                'score': score,
                'analysis': analysis,
                'risk_level': risk_analysis['risk_level']
            }

        except Exception as e:
            cprint(f"Error analyzing token {token_address}: {str(e)}", "red")
            return None

    def run_discovery(self):
        """Main discovery process"""
        cprint("\nStarting token discovery process...", "cyan")
        
        # Get tokens to analyze
        tokens = self.discover_new_tokens()
        cprint(f"Found {len(tokens)} tokens to analyze", "cyan")

        # Analyze each token
        results = []
        for token in tokens:
            cprint(f"\nAnalyzing token: {token[:8]}...", "yellow")
            result = self.analyze_token(token)
            if result:
                results.append(result)

        # Sort by score
        self.tokens_df = self.tokens_df.sort_values('score', ascending=False)

        # Print summary
        cprint("\nToken Analysis Summary:", "green")
        for _, row in self.tokens_df.iterrows():
            score_color = "green" if row['score'] >= 70 else "yellow" if row['score'] >= 50 else "red"
            cprint(f"\nToken: {row['token'][:8]}", score_color)
            cprint(f"Score: {row['score']}/100", score_color)
            cprint(f"Risk Level: {row['risk_level']}/20", score_color)
            cprint("Analysis:", score_color)
            cprint(row['analysis'], score_color)

        return results

def main():
    agent = TokenDiscoveryAgent()
    agent.run_discovery()

if __name__ == "__main__":
    main() 