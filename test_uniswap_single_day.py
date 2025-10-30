"""
Test Uniswap fetch for a single day (July 15, 2025)
"""

import sys
sys.path.append('src/task2_usdc_peg')

from datetime import datetime, timezone
from fetch_uniswap_v3 import fetch_swaps_for_day, process_swap_data

# Test for July 15, 2025
test_date = datetime(2025, 7, 15, tzinfo=timezone.utc)
day_start = int(test_date.timestamp())
day_end = int(test_date.replace(hour=23, minute=59, second=59).timestamp())

print(f"Testing Uniswap fetch for {test_date.strftime('%Y-%m-%d')}")
print(f"Timestamp range: {day_start} to {day_end}")
print(f"Pool: 0x3416cf6c708da44db2624d63ea0aaef7113527c6")
print()

# Fetch swaps
swaps = fetch_swaps_for_day("0x3416cf6c708da44db2624d63ea0aaef7113527c6", day_start, day_end)

print(f"Raw swaps fetched: {len(swaps)}")

if swaps:
    # Show first swap details
    first_swap = swaps[0]
    print(f"\nFirst swap details:")
    print(f"  ID: {first_swap['id']}")
    print(f"  Timestamp: {first_swap['timestamp']}")
    print(f"  Token0: {first_swap['token0']['symbol']} ({first_swap['token0']['decimals']} decimals)")
    print(f"  Token1: {first_swap['token1']['symbol']} ({first_swap['token1']['decimals']} decimals)")
    print(f"  Amount0: {first_swap['amount0']}")
    print(f"  Amount1: {first_swap['amount1']}")
    print(f"  sqrtPriceX96: {first_swap.get('sqrtPriceX96', 'N/A')}")
    
    # Process the data
    df = process_swap_data(swaps)
    print(f"\nProcessed swaps: {len(df)}")
    
    if not df.empty:
        print(f"\nPrice statistics:")
        print(f"  Min: {df['price'].min():.6f}")
        print(f"  Median: {df['price'].median():.6f}")
        print(f"  Max: {df['price'].max():.6f}")
        print(f"  Mean: {df['price'].mean():.6f}")
        
        print(f"\nVolume statistics:")
        print(f"  Total: ${df['volume'].sum():,.2f}")
        print(f"  Mean: ${df['volume'].mean():,.2f}")
        
        # Show 10 sample prices
        print(f"\n10 sample computed prices:")
        for i, row in df.head(10).iterrows():
            print(f"  {i+1}. Price: {row['price']:.6f}, Volume: ${row['volume']:.2f}")
else:
    print("\n⚠️  No swaps found - this could mean:")
    print("  1. The date is in the future (July 2025 hasn't happened yet!)")
    print("  2. The pool address is incorrect")
    print("  3. The subgraph doesn't have data for this date")
    print("  4. Network/API issues")

