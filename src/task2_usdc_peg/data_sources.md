# Data Sources for Task 2: USDC Peg Deviation Analysis

## Overview
This document describes the data sources used to analyze USDC/USDT peg deviations across DEX (Uniswap V3) and CEX (Bybit) venues for Q3 2025 (July 1 - September 30).

## 1. Uniswap V3 USDC/USDT Swaps

**Source**: The Graph Protocol (Decentralized Gateway)
**API Endpoint**: `https://gateway.thegraph.com/api/[api-key]/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV`

### Pool Details
- **Pool Address**: `0x3416cf6c708da44db2624d63ea0aaef7113527c6`
- **Fee Tier**: 0.01% (1 basis point)
- **Network**: Ethereum Mainnet

### GraphQL Query
The script fetches swap events using pagination:
```graphql
query PoolSwaps {
  swaps(
    first: 1000
    orderBy: id
    orderDirection: asc
    where: {
      pool: "0x3416cf6c708da44db2624d63ea0aaef7113527c6"
      timestamp_gte: [start_timestamp]
      timestamp_lt: [end_timestamp]
    }
  ) {
    id
    timestamp
    amount0
    amount1
    amountUSD
    sqrtPriceX96
    token0 { id symbol decimals }
    token1 { id symbol decimals }
  }
}
```

### Data Processing
- Fetches data day-by-day with automatic pagination
- Token0 = USDC (6 decimals)
- Token1 = USDT (6 decimals)
- Price calculation: USDT per USDC from `amount0` and `amount1`
- Validates prices and volumes before storing

### Reproduction Steps
1. Obtain a free API key from [The Graph](https://thegraph.com/)
2. Update `GRAPH_URL` in `src/task2_usdc_peg/fetch_uniswap_v3.py` with your key
3. Run: `python src/task2_usdc_peg/fetch_uniswap_v3.py`
4. Data saved to `temp/uniswap_raw_data.parquet`

## 2. Bybit USDC/USDT Spot Trades

**Source**: Bybit Historical Trade Data (Public Archives)

### Data Files
- `USDCUSDT-2025-07.csv` (July 2025)
- `USDCUSDT-2025-08.csv` (August 2025)
- `USDCUSDT-2025-09.csv` (September 2025)

### Download Instructions
1. Visit Bybit's public data portal: https://public.bybit.com/trading/
2. Navigate to spot trade archives
3. Download monthly CSVs for USDCUSDT pair
4. Place files in project root

### Data Format
```
tradeTime,price,qty,side,tradeId
1719792000000,0.9998,1200.50,Buy,123456789
```
- `tradeTime`: Unix timestamp in milliseconds
- `price`: USDT per USDC
- `qty`: Trade quantity in USDC
- `side`: Buy or Sell

## 3. Analysis Parameters

**Timeframe**: 2025-07-01 00:00:00 UTC to 2025-09-30 23:59:59 UTC

**Peg Band**: ±0.1% around 1.0000
- Lower bound: 0.9990
- Upper bound: 1.0010

**Outside-Band Definition**: Trades with price < 0.9990 OR price > 1.0010

**Aggregation**: Hourly buckets (UTC)

## 4. Data Quality Checks

### Uniswap V3
- Verify pool address matches official Uniswap interface
- Check token decimals (both USDC and USDT use 6 decimals)
- Validate price range (should be close to 1.0)
- Confirm timestamp coverage spans full Q3 2025

### Bybit
- Verify timestamp parsing (milliseconds → UTC datetime)
- Filter invalid prices (< 0 or > 2)
- Check for gaps in hourly coverage
- Validate volume is non-negative

## 5. Why These Sources?

✅ **Free & Reproducible**: Both sources are publicly accessible
✅ **Authoritative**: Dune queries blockchain directly; Bybit provides official trade history
✅ **Complete Coverage**: Both cover the full Q3 2025 timeframe
✅ **High Quality**: Minimal missing data, consistent formats
