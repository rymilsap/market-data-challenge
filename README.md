# DEX-CEX Market Analysis Challenge

A comprehensive analysis of decentralized and centralized exchange market dynamics, focusing on hedged liquidity provision and USDC peg deviation patterns.

## Project Overview

This repository contains two main analytical tasks:

1. **Task 1 - Hedged LP on Uniswap**: Derive and explain delta-neutral hedging strategies for Uniswap V2 and V3 liquidity provision
2. **Task 2 - USDC Peg Deviation**: Analyze hourly volume patterns outside ±0.1% band for USDC/USDT across Uniswap V3 and Bybit

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run Task 2 data collection and analysis
python -m src.task2_usdc_peg.fetch_uniswap_v3
python -m src.task2_usdc_peg.fetch_bybit
python -m src.task2_usdc_peg.aggregate_outside_band

# View results
jupyter notebook notebooks/task2_usdc_peg.ipynb
```

## Deliverables

### Task 1 - Hedged LP Analysis

- `src/task1_hedged_lp/formulas.md` - Mathematical derivations for V2/V3 hedging
- `src/task1_hedged_lp/hedge_v2_v3.py` - Implementation of hedge calculations
- `src/task1_hedged_lp/memo_task1.md` - Executive summary and cost analysis

### Task 2 - USDC Peg Deviation

- `outputs/usdc_peg_outside_band_hourly.csv` - Hourly volume data outside ±0.1% band
- `notebooks/task2_usdc_peg.ipynb` - Analysis notebook with visualizations

## Data Sources

- **Uniswap V3**: The Graph subgraph (uniswap/uniswap-v3)
- **Bybit**: Public REST API (no authentication required)
- **Timeframe**: July 1, 2025 - September 30, 2025 (UTC)
- **Pool**: Uniswap V3 USDC/USDT 0.01% (0x3416cf6c708da44db2624d63ea0aaef7113527c6)

## Repository Structure

```
dex-cex-market-analysis/
├─ README.md
├─ requirements.txt
├─ src/
│  ├─ task1_hedged_lp/
│  │  ├─ formulas.md
│  │  ├─ hedge_v2_v3.py
│  │  └─ memo_task1.md
│  └─ task2_usdc_peg/
│     ├─ data_sources.md
│     ├─ fetch_uniswap_v3.py
│     ├─ fetch_bybit.py
│     ├─ aggregate_outside_band.py
│     └─ utils.py
├─ notebooks/
│  └─ task2_usdc_peg.ipynb
├─ outputs/
│  └─ usdc_peg_outside_band_hourly.csv
└─ .gitignore
```

## Challenge Details

This project addresses the DEX-CEX Market Analysis Challenge, providing quantitative analysis of market microstructure and hedging strategies in decentralized finance.
