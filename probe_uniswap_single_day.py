"""
Probe Uniswap V3 for a single day (July 15, 2025) with proper pagination and price calculation.
"""

import requests
from decimal import Decimal, getcontext
from datetime import datetime, timezone

getcontext().prec = 28

# Configuration
GRAPH_URL = "https://api.thegraph.com/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
POOL_ADDRESS = "0x3416cf6c708da44db2624d63ea0aaef7113527c6"  # USDC/USDT 0.01%

# Test date: July 15, 2025
TEST_DATE = datetime(2025, 7, 15, tzinfo=timezone.utc)
TS_START = int(TEST_DATE.timestamp())
TS_END = int(TEST_DATE.replace(hour=23, minute=59, second=59).timestamp())

print("=" * 80)
print(f"UNISWAP V3 PROBE: July 15, 2025")
print("=" * 80)
print(f"Pool: {POOL_ADDRESS}")
print(f"Time range: {TS_START} to {TS_END}")
print(f"Date: {TEST_DATE}")
print()

def build_query(pool, ts_start, ts_end, last_id=""):
    """Build GraphQL query with proper pagination."""
    where_parts = [
        f'pool: "{pool.lower()}"',
        f'timestamp_gte: {ts_start}',
        f'timestamp_lt: {ts_end}'
    ]
    if last_id:
        where_parts.append(f'id_gt: "{last_id}"')
    
    where_clause = ', '.join(where_parts)
    
    return f"""
    query PoolSwaps {{
      swaps(
        first: 1000
        orderBy: id
        orderDirection: asc
        where: {{ {where_clause} }}
      ) {{
        id
        timestamp
        amount0
        amount1
        sqrtPriceX96
        token0 {{ id symbol decimals }}
        token1 {{ id symbol decimals }}
      }}
    }}
    """

def price_from_amounts(amount0, amount1, dec0, dec1, sym0, sym1):
    """Calculate USDT per USDC from trade amounts."""
    a0 = Decimal(str(amount0))
    a1 = Decimal(str(amount1))
    
    # Normalize by decimals
    norm_a0 = abs(a0) / (Decimal(10) ** dec0)
    norm_a1 = abs(a1) / (Decimal(10) ** dec1)
    
    # Determine which is USDC and which is USDT
    if sym0 == 'USDC' and sym1 == 'USDT':
        # price = USDT / USDC
        if norm_a0 == 0:
            return None
        return norm_a1 / norm_a0
    elif sym0 == 'USDT' and sym1 == 'USDC':
        # price = USDT / USDC (inverted)
        if norm_a1 == 0:
            return None
        return norm_a0 / norm_a1
    else:
        return None

def price_from_sqrtprice(sqrt_price_x96, dec0, dec1, sym0, sym1):
    """Calculate price from sqrtPriceX96."""
    Q96 = Decimal(2) ** 96
    sqrt_p = Decimal(str(sqrt_price_x96)) / Q96
    
    # Price of token1 in terms of token0
    price_1_per_0 = (sqrt_p ** 2) * (Decimal(10) ** (dec1 - dec0))
    
    # Convert to USDT per USDC
    if sym0 == 'USDC' and sym1 == 'USDT':
        return price_1_per_0  # Already USDT per USDC
    elif sym0 == 'USDT' and sym1 == 'USDC':
        return Decimal(1) / price_1_per_0  # Invert to get USDT per USDC
    else:
        return None

# Fetch swaps with pagination
all_swaps = []
last_id = ""
page = 0

print("Fetching swaps with pagination...")
while True:
    query = build_query(POOL_ADDRESS, TS_START, TS_END, last_id)
    
    try:
        response = requests.post(GRAPH_URL, json={'query': query}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL errors: {data['errors']}")
            break
        
        swaps = data.get('data', {}).get('swaps', [])
        
        if not swaps:
            break
        
        all_swaps.extend(swaps)
        page += 1
        print(f"  Page {page}: {len(swaps)} swaps (total: {len(all_swaps)})")
        
        if len(swaps) < 1000:
            break
        
        last_id = swaps[-1]['id']
        
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"\nTotal swaps fetched: {len(all_swaps)}")

if len(all_swaps) == 0:
    print("\n❌ NO SWAPS FOUND!")
    print("Possible issues:")
    print("  1. Wrong endpoint or pool address")
    print("  2. Date is outside available data range")
    print("  3. API access issues")
else:
    print(f"\n✅ SUCCESS! Fetched {len(all_swaps)} swaps")
    
    # Show first swap details
    first_swap = all_swaps[0]
    print(f"\nFirst swap:")
    print(f"  ID: {first_swap['id']}")
    print(f"  Timestamp: {first_swap['timestamp']}")
    print(f"  Token0: {first_swap['token0']['symbol']} (decimals: {first_swap['token0']['decimals']})")
    print(f"  Token1: {first_swap['token1']['symbol']} (decimals: {first_swap['token1']['decimals']})")
    print(f"  Amount0: {first_swap['amount0']}")
    print(f"  Amount1: {first_swap['amount1']}")
    print(f"  sqrtPriceX96: {first_swap['sqrtPriceX96']}")
    
    # Calculate prices for first 10 swaps
    print(f"\n10 Sample Price Calculations:")
    print("-" * 80)
    print(f"{'#':<4} {'From Amounts':<15} {'From SqrtPrice':<15} {'Diff':<10} {'Tokens':<20}")
    print("-" * 80)
    
    for i, swap in enumerate(all_swaps[:10]):
        sym0 = swap['token0']['symbol']
        sym1 = swap['token1']['symbol']
        dec0 = int(swap['token0']['decimals'])
        dec1 = int(swap['token1']['decimals'])
        
        price_amt = price_from_amounts(
            swap['amount0'], swap['amount1'], dec0, dec1, sym0, sym1
        )
        
        price_sqrt = price_from_sqrtprice(
            swap['sqrtPriceX96'], dec0, dec1, sym0, sym1
        )
        
        if price_amt and price_sqrt:
            diff = abs(price_amt - price_sqrt)
            print(f"{i+1:<4} {float(price_amt):<15.6f} {float(price_sqrt):<15.6f} {float(diff):<10.6f} {sym0}/{sym1}")
    
    # Statistics
    print(f"\n" + "=" * 80)
    print("PRICE STATISTICS")
    print("=" * 80)
    
    prices = []
    for swap in all_swaps:
        sym0 = swap['token0']['symbol']
        sym1 = swap['token1']['symbol']
        dec0 = int(swap['token0']['decimals'])
        dec1 = int(swap['token1']['decimals'])
        
        price = price_from_amounts(
            swap['amount0'], swap['amount1'], dec0, dec1, sym0, sym1
        )
        
        if price and 0.5 < price < 2.0:  # Sanity check
            prices.append(float(price))
    
    if prices:
        prices.sort()
        print(f"Valid prices: {len(prices)} / {len(all_swaps)}")
        print(f"Min: {min(prices):.6f}")
        print(f"Median: {prices[len(prices)//2]:.6f}")
        print(f"Max: {max(prices):.6f}")
        print(f"Mean: {sum(prices)/len(prices):.6f}")
        
        # Check outside band
        BAND_LOWER = 0.9990
        BAND_UPPER = 1.0010
        
        outside = [p for p in prices if p < BAND_LOWER or p > BAND_UPPER]
        print(f"\nOutside ±0.1% band: {len(outside)} ({len(outside)/len(prices)*100:.2f}%)")
        
        if outside:
            print(f"Outside range: {min(outside):.6f} to {max(outside):.6f}")

print("\n" + "=" * 80)
print("PROBE COMPLETE")
print("=" * 80)

