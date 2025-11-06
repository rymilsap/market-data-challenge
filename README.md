# DEX-CEX Market Analysis Challenge

A comprehensive analysis of decentralized and centralized exchange market dynamics, focusing on hedged liquidity provision and USDC peg deviation patterns.

## Project Overview

This repository contains two main analytical tasks:

1. **Task 1 - Hedged LP on Uniswap**: Derive and explain delta-neutral hedging strategies for Uniswap V2 and V3 liquidity provision
2. **Task 2 - USDC Peg Deviation**: Analyze hourly volume patterns outside ±0.1% band for USDC/USDT across Uniswap V3 and Bybit

## Quick Start

### Task 1: Run Hedge Calculator
```bash
python src/task1_hedged_lp/hedge_v2_v3.py
```

### Task 2: Reproduce Full Analysis

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Obtain Bybit historical data:**

Download from Bybit's public archives and place in project root:
- `USDCUSDT-2025-07.csv`
- `USDCUSDT-2025-08.csv`
- `USDCUSDT-2025-09.csv`

**3. Configure The Graph API:**

- Get a free API key from [The Graph](https://thegraph.com/)
- Update `GRAPH_URL` in `src/task2_usdc_peg/fetch_uniswap_v3.py` with your key

**4. Run data processing pipeline:**
```bash
python src/task2_usdc_peg/fetch_uniswap_v3.py
python src/task2_usdc_peg/fetch_bybit.py
python src/task2_usdc_peg/aggregate_outside_band.py
```

**5. View analysis:**
```bash
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

- **Uniswap V3**: The Graph Protocol (decentralized GraphQL API)
- **Bybit**: Historical trade archives (public CSVs)
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

## Key Findings

**Task 1:** Derived delta-neutral hedging formulas for Uniswap V2 (50/50) and V3 (±10% concentrated liquidity), accounting for funding costs, impermanent loss, gas/opex, and rebalancing triggers.

**Task 2:** Analyzed 2,208 hours (July-Sept 2025):
- **103 hours** with outside-band (±0.1%) activity
- **Uniswap V3:** $606M volume outside band (100 hours)
- **Bybit:** $7.6M volume outside band (6 hours)
- Finding: DEX showed significantly more peg stress than CEX

## Submission

This repository fulfills all requirements for the DEX-CEX Market Analysis Challenge:

✅ **Task 1**: Hedged LP memo with entry hedge, cost analysis, and V3 extension  
✅ **Task 2**: CSV output with required columns (time, volumes, min/max prices per venue)  
✅ **Task 2**: Jupyter notebook documenting data sources and calculations

**Required CSV Format:**
```
time,uniswap_volume,uniswap_min_price,uniswap_max_price,bybit_volume,bybit_min_price,bybit_max_price
```
- 2,208 hourly rows covering full timeframe
- Outside-band trades only (< 0.999 or > 1.001 USDT per USDC)
- Zero volumes with blank min/max when no outside-band activity
