# Task 1: Hedged LP Analysis - Executive Memo

## Entry Hedge Calculation (V2 50/50 Pool)

### Methodology

For a Uniswap V2 50/50 ETH/USDT pool with total notional value V and ETH price P, the pool's inventory exposure is locally equivalent to holding V/(2P) ETH. This creates a positive delta of +V/(2P) ETH units.

**Required Hedge**: Short V/(2P) ETH on CEX perp to achieve local delta neutrality.

### Example Calculation

- Position: $100,000 USD
- ETH Price: $2,000
- Required Short: 25 ETH ($50,000 notional)

## Additional Costs Analysis

### Funding Costs

- **CEX Perp Funding**: Typically 0.01% per 8-hour period (can be positive or negative)
- **Annual Impact**: ~1.37% of hedge notional value
- **Example**: $50,000 hedge = ~$685/year in funding costs

### Borrow Costs (if spot short)

- **Margin Requirements**: 10-20% of position value
- **Interest Rates**: 3-8% annually on borrowed ETH
- **Liquidation Risk**: Price movements beyond margin limits

### LP Economics

- **Fees Earned**: 0.3% (V2) or 0.01% (V3) on trading volume
- **Impermanent Loss**: Unavoidable with price movements
- **Fee vs IL Trade-off**: Higher fees can offset IL in high-volume periods

### Operational Costs

- **Gas Fees**: $20-100 per rebalance (Ethereum mainnet)
- **Price Impact**: 0.1-0.5% slippage on large hedge adjustments
- **Maker/Taker Fees**: 0.1-0.5% on CEX perp trades
- **Adverse Selection**: Front-running risk on large orders

### Re-hedge Triggers

- **Price Threshold**: ±5-10% from entry price
- **Time-based**: Daily/weekly rebalancing
- **Volatility-based**: High volatility periods require more frequent hedging

## V3 ±10% Range Extension

### Key Changes in V3

**Concentrated Liquidity Impact**: V3 positions have higher capital efficiency but different risk profile:

1. **Delta Sensitivity**: V3 delta changes more rapidly near range edges
2. **Range Exit Risk**: Position becomes 100% single-asset if price exits range
3. **Rebalance Policy**: More frequent adjustments needed near edges
4. **Gas Optimization**: Batch multiple operations to reduce costs

### V3 Hedge Mathematics

For V3 with ±10% range around price P₀:

- **ETH Amount**: L × (1/√P₀ - 1/√P_high)
- **USDT Amount**: L × (√P₀ - √P_low)
- **Delta**: L × (1/(2P₀^(3/2)))

**Hedge Size**: L × (1/(2P₀^(3/2))) ETH

### V3-Specific Considerations

- **Proximity to Edges**: Delta increases exponentially as price approaches range bounds
- **Rebalance Cadence**: Near edges requires hourly rebalancing vs daily for center
- **Range Management**: Active monitoring of position concentration
- **Fee Optimization**: Higher fees (0.05-1%) can justify more frequent rebalancing

### Operational Differences

- **Gas Costs**: Higher due to more frequent rebalancing
- **Monitoring**: Real-time price tracking near range edges
- **Liquidity Management**: Dynamic range adjustment based on market conditions
- **Risk Management**: Stop-loss triggers when approaching range bounds

## Risk Assessment

### Market Risks

- **Basis Risk**: CEX perp vs spot price divergence
- **Liquidation Risk**: CEX margin requirements
- **Oracle Risk**: Price feed manipulation or delays
- **Regulatory Risk**: CEX restrictions on perp trading

### Operational Risks

- **Execution Risk**: Slippage on large hedge adjustments
- **Technical Risk**: Smart contract bugs or CEX API failures
- **Gas Risk**: Network congestion affecting rebalance timing
- **Counterparty Risk**: CEX solvency and withdrawal limits

## Conclusion

The hedged LP strategy provides delta neutrality but introduces significant operational complexity and costs. V3 concentrated liquidity amplifies these challenges while offering higher fee potential. Success requires sophisticated risk management, automated rebalancing systems, and careful cost-benefit analysis of hedging frequency.

**Key Success Factors**:

1. Automated monitoring and rebalancing systems
2. Optimized gas usage through batching
3. Careful selection of CEX perp markets
4. Dynamic range management for V3 positions
5. Regular cost-benefit analysis of hedge frequency

