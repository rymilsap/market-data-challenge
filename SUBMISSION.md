# DEX–CEX Market Analysis Challenge - Submission

> **Note:** I learned a tremendous amount during this challenge, particularly around working with production blockchain data APIs and handling large-scale financial datasets. I've done my best to ensure the data sources are correct and the methodology is sound, but I'm open to feedback on my approach.

---

## Challenge Overview

This challenge has two parts:

**Task 1 – Hedged LP on Uniswap**  
Theoretical derivation of a delta-neutral hedge for an LP position.

**Task 2 – USDC Peg Deviation (Hourly)**  
Empirical comparison of price deviations across DEX vs CEX venues.

---

## Task 1 — Hedged LP on Uniswap

### Challenge Prompt

You open a 50/50 USD-value LP position in an ETH/USDT Uniswap V2 pool.

- Compute the amount of ETH to short on a CEX perpetual to make the LP delta-neutral.
- List additional costs that affect the hedge.
- Re-derive the hedge if the same liquidity is provided in a V3 pool within ±10% of the spot price.

**Deliverable** → short memo explaining hedge logic, costs, and V3 trade-offs.

### My Approach

**Tech/Tools:** Python 3.9, NumPy for sensitivity checks, Markdown memo.

**Step 1 – V2 hedge:** At entry, a 50/50 V2 pool holds ≈ V/(2P) ETH.  
→ Short that amount to neutralize delta.

**Step 2 – V3 hedge:** Derived delta from liquidity L and sqrt-price formulas:

```
ΔETH = L × (1/√P₀ - 1/√Phigh)
Local delta ≈ L / (2P^1.5)
```

**Step 3 – Validation:** Built `hedge_v2_v3.py` to test scenarios (e.g., $100k position at $2k ETH) and verify the math.

**Step 4 – Memo:** Discussed funding rates, borrow costs, rebalance frequency, gas fees, and range exit risk for V3.

**Deliverables:**

- `src/task1_hedged_lp/memo_task1.md` - Executive memo
- `src/task1_hedged_lp/formulas.md` - Mathematical derivations
- `src/task1_hedged_lp/hedge_v2_v3.py` - Python validation script

---

## Task 2 — USDC Peg Deviation: DEX vs CEX (Hourly)

### Challenge Prompt

Compare hourly USDC/USDT trades (July 1 – Sept 30, 2025 UTC).

- **DEX:** Uniswap V3 0.01% pool `0x3416cf6c708da44db2624d63ea0aaef7113527c6` (Ethereum)
- **CEX:** Bybit spot USDC/USDT
- **Band:** Outside ±0.1% around 1.0000 USDT/USDC

For each hour, aggregate total volume traded outside the band and report min/max prices per venue.

**Deliverables** → CSV (one row per hour) and a Jupyter notebook showing data source and calculations.

### My Approach

#### Tech Stack

- Python 3.9 + pandas, numpy, requests, decimal
- Jupyter Notebook for analysis and plots
- The Graph (GraphQL) for Uniswap on-chain data
- Bybit CSV archives for CEX spot trades
- Git for version control

#### Phase 1 – Bybit (CEX)

1. Downloaded 3 monthly CSV files (July–Sept 2025, ~5.3M rows total)
2. Parsed `tradeTime` (ms → UTC), computed price and volume in USDC
3. Filtered trades where price < 0.999 or > 1.001
4. Grouped by hour → `groupby('hour').agg(sum, min, max)`

**Result:** 6 hours outside band, ≈ $7.6M volume

#### Phase 2 – Uniswap (DEX)

1. Used The Graph v3 subgraph (Gateway API with new subgraph ID)
2. Implemented day-by-day pagination using `id_gt` cursor:

```python
while True:
    query = build_query(day_start, last_id)
    res = requests.post(GRAPH_URL, json={'query': query})
    swaps = res.json()['data']['swaps']
    if len(swaps) < 1000: break
    last_id = swaps[-1]['id']
```

3. Calculated price = |amount1| / |amount0| after decimal normalization (USDC = 6, USDT = 6)
4. Verified data accuracy and range stability
5. Processed validated hourly aggregates

**Result:** 100 hours outside band, ≈ $606M volume

#### Phase 3 – Aggregation

1. Combined DEX and CEX frames → 2,208 hours (July 1 – Sept 30)
2. Filled missing hours with zero volume and blank min/max
3. Wrote `aggregate_outside_band.py` to export final CSV:

```csv
time,uniswap_volume,bybit_volume,
uniswap_min_price,uniswap_max_price,
bybit_min_price,bybit_max_price
```

#### Phase 4 – Analysis & Visualization

Used Matplotlib/Seaborn in `task2_usdc_peg.ipynb` to plot:

- Hourly outside-band volumes
- Scatter of price deviations

**Insight:** DEX volume outside band ≈ 80× larger than CEX ($606M vs $7.6M)

### Technical Challenges Solved

1. **Graph endpoint deprecation** → migrated to new Gateway + subgraph ID
2. **Pagination + rate limits** → batch fetch with delay/backoff
3. **Decimal precision** → used `Decimal()` for tight band comparisons
4. **Token pair reversal** → detected USDC/USDT ordering per swap
5. **Data validation** → sanity checks for price (0.5–2.0) and positive volume

---

## Results Summary

### Key Statistics

| Venue          | Hours outside band | Volume outside band |
| -------------- | ------------------ | ------------------- |
| **Uniswap V3** | 100 hrs            | **$606M**           |
| **Bybit Spot** | 6 hrs              | **$7.6M**           |

**Total hours analyzed:** 2,208 (92 days × 24h)  
**Outside-band activity:** 103 hours  
**Finding:** DEX experienced greater peg stress and higher volatility than CEX

### Time Investment

- **Task 1:** ~2 hours (theory + derivations)
- **Task 2:** ~8 hours (data engineering + analysis)
- **Total:** ~10 hours

---

## Deliverables

✅ **Task 1:**

- `src/task1_hedged_lp/memo_task1.md` - Executive memo
- `src/task1_hedged_lp/formulas.md` - Mathematical derivations
- `src/task1_hedged_lp/hedge_v2_v3.py` - Validation script

✅ **Task 2:**

- `outputs/usdc_peg_outside_band_hourly.csv` - 2,208 hourly rows with required columns
- `notebooks/task2_usdc_peg.ipynb` - Analysis notebook with visualizations
- `src/task2_usdc_peg/` - Complete data pipeline (fetch, aggregate, utils)

---

## Reproduction Instructions

```bash
# Install dependencies
pip install -r requirements.txt

# Task 1: Run hedge calculator
python src/task1_hedged_lp/hedge_v2_v3.py

# Task 2: View analysis (data already processed)
jupyter notebook notebooks/task2_usdc_peg.ipynb
```

**Data sources documented in:** `src/task2_usdc_peg/data_sources.md`

---

## Data Quality Note

The finding that Uniswap V3 had significantly higher outside-band volume ($606M) compared to Bybit ($7.6M) warrants consideration:

**Why this might be accurate:**

- DEXs can experience more price volatility due to lower liquidity depth and fragmented liquidity across multiple pools
- Uniswap V3's concentrated liquidity model can lead to sharper price movements during low liquidity periods
- CEX market makers actively maintain tight spreads on stablecoin pairs
- Arbitrage bots may react slower on-chain vs CEX

**Potential data considerations:**

- The Uniswap data includes ALL swaps (even small ones) while Bybit might have minimum trade sizes
- Different trading patterns: DEX users might trade through larger price slippage for privacy/non-custodial reasons
- The 0.01% fee tier pool is the most liquid, but there are other USDC/USDT pools that weren't analyzed

I've validated the data processing logic and filtering criteria, but the magnitude of the difference is notable and could benefit from peer review.

---

_Submission Date: November 2025_
