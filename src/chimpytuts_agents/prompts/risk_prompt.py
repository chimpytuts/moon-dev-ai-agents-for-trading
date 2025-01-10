RISK_OVERRIDE_PROMPT = """
Analyze the following market data for this position and determine whether to OVERRIDE the risk limit or RESPECT the limit. Use all the provided information to justify your decision.

**Position Details**:
- Initial Position Value (USD): {start_value}
- Current Position Value (USD): {current_value}
- Percentage Change: {percent_change:.2f}%
- USD Change: {usd_change:.2f}USD
- Suggested Action Type: {type}
- Reason for Suggested Action: {why}
- Recent Market Data (15m): 
{position_data_15m}
- Recent Market Data (5m): 
{position_data_5m}

**Evaluation Criteria**:
1. **Recent Price Action and Momentum**:
   - Analyze the recent price data from both the 15m and 5m timeframes.
   - Use `percent_change` and `usd_change` to identify trends or reversals in momentum.
   - Determine if the data shows strong continuation or reversal signals.

2. **Volume Trends**:
   - Assess the volume data in the 15m and 5m timeframes (`data`) to confirm if it aligns with the price action.
   - Consistent or increasing volume during price changes indicates stronger trends; divergence suggests caution.

3. **Market Conditions**:
   - Evaluate the broader market context (e.g., volatility or stability) based on the data.
   - Identify if external market conditions may impact this position significantly.

4. **Risk/Reward Analysis**:
   - Compare the `initial_position_value_usd` with the `current_position_value_usd`.
   - Assess whether the current value justifies maintaining the position or if the risks outweigh potential rewards.

**Decision Guidelines**:
- For **loss scenarios**:
  - OVERRIDE only if there is strong evidence of a reversal (e.g., price and volume alignment, market stabilization) with >70% confidence.
  - If no strong reversal evidence, RESPECT_LIMIT and clearly explain the rationale.

- For **gain scenarios**:
  - OVERRIDE if the momentum and market data suggest continued upward potential with >60% confidence.
  - If gains appear unsustainable, RESPECT_LIMIT and justify why the position should be closed.

**Response Format**:
1. OVERRIDE: <specific justification based on the data for this position>
2. RESPECT_LIMIT: <specific justification based on the data for this position>
"""