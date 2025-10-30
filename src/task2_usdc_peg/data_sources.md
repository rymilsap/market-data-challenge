# Data Sources Documentation

## Overview

This document outlines the free data sources used for the USDC peg deviation analysis and how to reproduce the data collection process.

## Data Sources

### 1. Uniswap V3 USDC/USDT Pool

- **Source**: The Graph Protocol (uniswap/uniswap-v3 subgraph)
- **Endpoint**: https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3
- **Pool Address**: 0x3416cf6c708da44db2624d63ea0aaef7113527c6
- **Pool Fee**: 0.01%
- **Tokens**: USDC (0xA0b86a33E6441b8c4C8C0d4Ce4a8b4c4d4e4f4g4h) / USDT (0xdAC17F958D2ee523a2206206994597C13D831ec7)

#### GraphQL Query

```graphql
query GetSwaps($poolId: String!, $timestamp_gte: Int!, $timestamp_lte: Int!) {
  swaps(
    where: {
      pool: $poolId
      timestamp_gte: $timestamp_gte
      timestamp_lte: $timestamp_lte
    }
    orderBy: timestamp
    orderDirection: asc
    first: 1000
  ) {
    id
    timestamp
    amount0
    amount1
    amountUSD
    sqrtPriceX96
    token0 {
      symbol
      decimals
    }
    token1 {
      symbol
      decimals
    }
  }
}
```

#### Data Processing

- Calculate price as USDT per USDC from token amounts
- Handle token0/token1 ordering (pool may have USDC as token0 or token1)
- Convert timestamp to UTC hour buckets
- Filter for trades outside ±0.1% band (price < 0.9990 or > 1.0010)

### 2. Bybit USDC/USDT Spot

- **Source**: Bybit Public REST API
- **Endpoint**: https://api.bybit.com/v5/market/recent-trade
- **Symbol**: USDCUSDT
- **Authentication**: None required (public endpoint)

#### API Parameters

```python
params = {
    'category': 'spot',
    'symbol': 'USDCUSDT',
    'limit': 1000,
    'startTime': start_timestamp_ms,
    'endTime': end_timestamp_ms
}
```

#### Data Processing

- Parse trade data from API response
- Convert timestamp from milliseconds to seconds
- Calculate price as USDT per USDC
- Filter for trades outside ±0.1% band
- Aggregate by hour buckets

## Data Collection Process

### 1. Time Range

- **Start**: 2025-07-01 00:00:00 UTC
- **End**: 2025-09-30 23:59:59 UTC
- **Duration**: 92 days
- **Hour Buckets**: 2,208 hours total

### 2. Band Definition

- **Lower Bound**: 0.9990 USDT per USDC
- **Upper Bound**: 1.0010 USDT per USDC
- **Band Width**: ±0.1% around 1.0000

### 3. Data Quality Checks

- **Price Validation**: Ensure prices are within reasonable bounds (0.5 - 2.0)
- **Volume Validation**: Filter out zero or negative volumes
- **Timestamp Validation**: Ensure timestamps are within expected range
- **Token Decimal Handling**: Properly handle USDC (6 decimals) and USDT (6 decimals)

## Alternative Data Sources

### If The Graph is Unavailable

1. **Messari Subgraphs**: Alternative GraphQL endpoints
2. **Flipside Crypto**: Free on-chain data APIs
3. **Alchemy/Infura**: Direct Ethereum node queries
4. **Dune Analytics**: Pre-computed Uniswap data

### If Bybit is Unavailable

1. **Binance API**: Similar public endpoints
2. **Coinbase Pro API**: USDC/USDT spot data
3. **Kraken API**: Alternative CEX data source

## Reproducibility

### Environment Setup

```bash
pip install -r requirements.txt
```

### Data Collection Commands

```bash
# Fetch Uniswap V3 data
python -m src.task2_usdc_peg.fetch_uniswap_v3

# Fetch Bybit data
python -m src.task2_usdc_peg.fetch_bybit

# Aggregate and filter data
python -m src.task2_usdc_peg.aggregate_outside_band
```

### Output Files

- `outputs/usdc_peg_outside_band_hourly.csv`: Final aggregated data
- `temp/uniswap_raw_data.parquet`: Raw Uniswap data
- `temp/bybit_raw_data.parquet`: Raw Bybit data

## Data Schema

### Input Data (Raw)

- **timestamp**: Unix timestamp in seconds
- **price**: USDT per USDC
- **volume**: Volume in USDC terms
- **venue**: 'uniswap' or 'bybit'

### Output Data (Aggregated)

- **time**: ISO8601 hour timestamp (YYYY-MM-DDTHH:00:00Z)
- **uniswap_volume**: Total volume outside band for Uniswap
- **bybit_volume**: Total volume outside band for Bybit
- **uniswap_min_price**: Minimum price outside band for Uniswap
- **uniswap_max_price**: Maximum price outside band for Uniswap
- **bybit_min_price**: Minimum price outside band for Bybit
- **bybit_max_price**: Maximum price outside band for Bybit

## Notes

- All timestamps are in UTC
- Prices are calculated as USDT per USDC (not inverted)
- Volume is denominated in USDC terms
- Missing data (no trades outside band) results in volume=0 and blank min/max prices

