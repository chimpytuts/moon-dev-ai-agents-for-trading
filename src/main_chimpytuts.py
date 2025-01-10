"""
🌙 Moon Dev's AI Trading System
Main entry point for running trading agents
"""

import os
import sys
from termcolor import cprint
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
from config import *

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import agents
from src.agents.chimpytuts_agents.trading_agent import TradingAgent
from src.agents.chimpytuts_agents.risk_agent import RiskAgent
from src.agents.chimpytuts_agents.token_discovery_agent import TokenDiscoveryAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.copybot_agent import CopyBotAgent
from src.agents.sentiment_agent import SentimentAgent

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': True,      # Risk management agent
    'trading': False,   # LLM trading agent
    "token_discovery": True, # Token discovery agent
}

def run_agents():
    """Run all active agents in sequence"""
    try:
        # Initialize active agents
        trading_agent = TradingAgent() if ACTIVE_AGENTS['trading'] else None
        risk_agent = RiskAgent() if ACTIVE_AGENTS['risk'] else None
        token_discovery_agent = TokenDiscoveryAgent() if ACTIVE_AGENTS['token_discovery'] else None

        while True:
            try:
                if token_discovery_agent:
                    cprint("\n🔍 Running Token Discovery...", "cyan")
                    token_discovery_agent.analyze_tokens()
                # Run Risk Management
                if risk_agent:
                    cprint("\n🛡️ Running Risk Management...", "cyan")
                    risk_agent.should_override_limit()

                # Sleep until next cycle
                next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
                cprint(f"\n😴 Sleeping until {next_run.strftime('%H:%M:%S')}", "cyan")
                time.sleep(60 * SLEEP_BETWEEN_RUNS_MINUTES)

            except Exception as e:
                cprint(f"\n❌ Error running agents: {str(e)}", "red")
                cprint("🔄 Continuing to next cycle...", "yellow")
                time.sleep(60)  # Sleep for 1 minute on error before retrying

    except KeyboardInterrupt:
        cprint("\n👋 Gracefully shutting down...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Error in main loop: {str(e)}", "red")
        raise

if __name__ == "__main__":
    cprint("\n🌙 Moon Dev AI Agent Trading System Starting...", "white", "on_blue")
    cprint("\n📊 Active Agents:", "white", "on_blue")
    for agent, active in ACTIVE_AGENTS.items():
        status = "✅ ON" if active else "❌ OFF"
        cprint(f"  • {agent.title()}: {status}", "white", "on_blue")
    print("\n")
    
    run_agents()
