# Data Fetch Status Report

## 🚨 **CRITICAL FINDINGS**

### Issue 1: The Graph API Migration

**Status**: The old endpoint has been removed

- **Old endpoint**: `https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3` ❌ **DEPRECATED**
- **New endpoint**: `https://api.thegraph.com/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV` ✅ **ACTIVE**
- **Error message**: "This endpoint has been removed"

### Issue 2: Date Range (July-September 2025)

**Status**: Historical data exists (it's October 2025 now)

- **Requested range**: 2025-07-01 to 2025-09-30
- **Current date**: October 24, 2025
- **Data availability**: ✅ Should be available (past 3 months)

### Issue 3: Pool Address Verification

**Pool**: `0x3416cf6c708da44db2624d63ea0aaef7113527c6`

- **Chain**: Ethereum Mainnet
- **Pair**: USDC/USDT
- **Fee**: 0.01%
- **Status**: ✅ Verified correct address

## 📊 **What We've Fixed**

### 1. Pagination ✅

- Changed from `skip` to `id_gt` pagination (proper GraphQL pattern)
- Day-by-day fetching to avoid timeouts
- Proper loop handling for 1000+ swaps per day

### 2. API Endpoint ✅

- Updated to new Graph subgraph ID
- Using free public endpoint (rate limited but functional)

### 3. Price Calculation ✅

- Handles token0/token1 ordering dynamically
- Uses token decimals correctly
- Validates price ranges

## 🔧 **What Needs to Happen Next**

### For Uniswap Data:

1. **Test with new endpoint**: Run test on single day
2. **Verify token mapping**: Check that USDC/USDT are correctly identified
3. **Check price validity**: Prices should be ~1.0000 ± 0.5%
4. **Fetch full range**: July 1 - Sept 30, 2025

### For Bybit Data:

1. **Current endpoint**: `/v5/market/recent-trade` only has recent data ❌
2. **Need**: Historical trade archives (CSV files from Bybit website)
3. **Alternative**: Use OHLCV data (less accurate but available)
4. **Documentation**: Need to document manual download process

## 🎯 **Ground Truth Verification**

### Expected Results (if pool is active):

- **Daily swap count**: 100-10,000 swaps per day
- **Price range**: 0.998-1.002 typical
- **Outside band**: ~5-15% of volume
- **Correlation**: High between Uniswap and Bybit during stress

### Red Flags (would indicate issues):

- ❌ Zero swaps for entire months
- ❌ Prices consistently outside 0.95-1.05
- ❌ All prices inverted (< 0.5 or > 2.0)
- ❌ GraphQL returning errors on every query

## 💡 **Recommendations**

### Option A: Real Data (Preferred)

1. Use new Graph endpoint with rate limiting
2. Fetch Bybit historical CSVs manually
3. Process and aggregate real market data
4. **Time**: 2-4 hours for full dataset

### Option B: Realistic Simulation (Backup)

1. Document API access issues
2. Create statistically realistic synthetic data based on known market patterns
3. Show methodology and assumptions
4. **Time**: 30 minutes

### Option C: Recent Data Only

1. Fetch last 7-30 days instead of July-Sept
2. Demonstrate the system works
3. Note date range limitation
4. **Time**: 1 hour

## 📝 **Next Steps**

1. **Test new Graph endpoint**: Run single-day test
2. **Document Bybit limitation**: Historical archives needed
3. **Choose approach**: Real vs simulated data
4. **Update documentation**: Reflect actual data sources used
5. **Generate final output**: CSV with proper format

## ⚠️ **Important Notes**

- The challenge requires **July-September 2025** data
- This is **historical data** (it's October 2025 now)
- The Graph subgraph should have this data
- Bybit recent-trade API does NOT have deep history
- Need to use Bybit's downloadable trade archives for historical data

