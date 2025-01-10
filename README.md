# 🤖 AI AGENTS FOR TRADING

<p align="center">
  <a href="https://www.moondev.com/"><img src="moondev.png" width="300" alt="Moon Dev"></a>
</p>

This project explores the potential of [artificial financial intelligence](https://www.afi.xyz) - a focused implementation of AI for trading and investing research.

⭐️ [first full concise documentation video (watch here)](https://www.youtube.com/watch?v=So_LQVKa55c)

📀 follow all updates here on youtube: https://www.youtube.com/playlist?list=PLXrNVMjRZUJg4M4uz52iGd1LhXXGVbIFz

**⚠️ IMPORTANT: This is an experimental project. There are NO guarantees of profitability. Trading involves substantial risk of loss.**

## 🎯 Vision
We're researching AI agents for trading that will eventually leverage [AFI](https://www.afi.xyz). With 4 years of experience training humans through our [bootcamp](https://algotradecamp.com), we're exploring where AI agents might complement human trading operations, and later replace trading human operations. This is experimental research, not a profitable trading solution.

## 🧠 Hypothesis
AI agents will be able to build a better quant portfolio than humans. i've spent the last 4 years building quant systems & training others to do so. 2025 is about replicating that success but with ai agents doing it instead of me. in 2026 i will release a paper of my findings after a full year of testing ai agents in quant vs the last 4 years of humans.

## 💡 Concept
AI agents might help address common trading challenges:
- Emotional reactions
- Ego-driven decisions
- Inconsistent execution
- Fatigue effects
- Impatience
- Fear & Greed cycles

While we use the RBI framework for strategy research, we're exploring AI agents as potential tools. We're in early stages with LLM technology, investigating possibilities in the trading space.

*There is no token associated with this project and there never will be. any token launched is not affiliated with this project, moon dev will never dm you. be careful. don't send funds anywhere*

## Video Updates & Training
all the video updates are consolidated in the below playlist on youtube
📀 https://www.youtube.com/playlist?list=PLXrNVMjRZUJg4M4uz52iGd1LhXXGVbIFz

## ⚠️ Critical Disclaimers

*There is no token associated with this project and there never will be. any token launched is not affiliated with this project, moon dev will never dm you. be careful. don't send funds anywhere*

**PLEASE READ CAREFULLY:**

1. This is an experimental research project, NOT a trading system
2. There are NO plug-and-play solutions for guaranteed profits
3. We do NOT provide trading strategies
4. Success depends entirely on YOUR:
   - Trading strategy
   - Risk management
   - Market research
   - Testing and validation
   - Overall trading approach

5. NO AI agent can guarantee profitable trading
6. You MUST develop and validate your own trading approach
7. Trading involves substantial risk of loss
8. Past performance does not indicate future results

## 👂 Looking for Updates?
Project updates will be posted in discord, join here: [moondev.com](http://moondev.com) 


## 🔗 Links
- Free Algo Trading Roadmap: [moondev.com](https://moondev.com)
- Algo Trading Education: [algotradecamp.com](https://algotradecamp.com)
- Business Contact [moon@algotradecamp.com](mailto:moon@algotradecamp.com)


## Live Agents
- Trading Agent (`trading_agent.py`): Example agent that analyzes token data via LLM to make basic trade decisions
- Strategy Agent (`strategy_agent.py`): Manages and executes trading strategies placed in the strategies folder
- Risk Agent (`risk_agent.py`): Monitors and manages portfolio risk, enforcing position limits and PnL thresholds
- Copy Agent (`copy_agent.py`): monitors copy bot for potential trades
- Whale Agent (`whale_agent.py`): monitors whale activity and announces when a whale enters the market
- Sentiment Agent (`sentiment_agent.py`): analyzes Twitter sentiment for crypto tokens with voice announcements
- Focus Agent (`focus_agent.py`): randomly samples audio during coding sessions to maintain productivity, providing focus scores and voice alerts when focus drops (~$10/month, perfect for voice-to-code workflows)

## 🚀 Project Progress & Roadmap
### Phase 1: Foundation & Basic Trading ✅
- [x] Basic project structure
- [x] Environment setup
- [x] Token data collection
- [x] Basic trading functions
- [x] Market data API integration (OI, Liquidations, Funding)
- [x] Risk management agent with PnL limits
- [x] Risk agent minimum balance protection (1/8/25)
- [x] CopyBot portfolio analyzer (1/8/25)

### Phase 2: Advanced Features 🚀
- [ ] Portfolio optimization
- [ ] Advanced risk management
- [ ] Machine learning integration
- [x] Sentiment analysis with voice announcements
- [ ] Backtesting framework
- [ ] Performance analytics

### Shipped Features 📦

- [x] 1/10 - built a coin gecko agent conversation between 2 ai agents and all of coin geckos data
- [x] 1/10 - added a focus agent that will take random samples of my voice to ensure im always locked in. my kpi is 200 ai uses per day which is hard when i yap so this is the solution.
- [x] 1/9 - Added Sentiment Analysis Agent with voice announcements and historical tracking
            - Monitors Twitter sentiment for major tokens
            - Tracks sentiment changes over time
            - Announces significant sentiment shifts
         - updated the whale agent as well to work better
- [x] 1/8 - Added minimum balance protection to Risk Agent with configurable AI consultation
            - Completed CopyBot portfolio analyzer with position sizing
            - V0 of the whale agent launched
- [x] 1/7 - CopyBot Agent: Added AI agent to analyze copybot portfolio and decide on whether it should take a position on their account 
- [x] 1/6 - Market Data API: Added comprehensive API for liquidations, funding rates, open interest, and copybot data
- [x] 1/5 - created a documentation training video with a full walkthrough of this github (releasing jan 7th)
- [x] 1/4 - strategy_agent.py: an ai agent that has last say on any strategy placed in strategies folder
- [x] 1/3 - risk_agent.py: built out an ai agent to manage risk
- [x] 1/2 - trading_agent.py: built the first trading agent 
- [x] 1/1 - first lines of code written

## 🚀 Quick Start Guide

1. ⭐ **Star the Repo**
   - Click the star button to save it to your GitHub favorites

2. 🍴 **Fork the Repo**
   - Fork to your GitHub account to get your own copy
   - This lets you make changes and track updates

3. 💻 **Open in Your IDE**
   - Clone to your local machine
   - Recommended: Use [Cursor](https://www.cursor.com/) or [Windsurfer](https://codeium.com/) for AI-enabled coding

4. 🔑 **Set Environment Variables**
   - Check `.env.example` for required variables
   - Create a copy of above and name it `.env` file with your keys:
     - Anthropic API key
     - Other trading API keys
   - ⚠️ Never commit or share your API keys!

5. 🤖 **Customize Agent Prompts**
   - Navigate to `/agents` folder
   - Modify LLM prompts to fit your needs
   - Each agent has configurable parameters

6. 📈 **Implement Your Strategies**
   - Add your strategies to `/strategies` folder
   - Remember: Out-of-box code is NOT profitable
   - Thorough testing required before live trading

7. 🏃‍♂️ **Run the System**
   - Execute via `main.py`
   - Toggle agents on/off as needed
   - Monitor logs for performance

---
*Built with love by Moon Dev - Pioneering the future of AI-powered trading*


## 📜 Detailed Disclaimer
The content presented is for educational and informational purposes only and does not constitute financial advice. All trading involves risk and may not be suitable for all investors. You should carefully consider your investment objectives, level of experience, and risk appetite before investing.

Past performance is not indicative of future results. There is no guarantee that any trading strategy or algorithm discussed will result in profits or will not incur losses.

**CFTC Disclaimer:** Commodity Futures Trading Commission (CFTC) regulations require disclosure of the risks associated with trading commodities and derivatives. There is a substantial risk of loss in trading and investing.

I am not a licensed financial advisor or a registered broker-dealer. Content & code is based on personal research perspectives and should not be relied upon as a guarantee of success in trading.