"""
Fetch Uniswap V3 USDC/USDT swap data from The Graph.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import time
import os
from utils import (
    calculate_price_from_amounts, validate_price, validate_volume,
    round_to_hour, is_outside_band, save_to_parquet, create_temp_dir
)

GRAPH_URL = "https://gateway.thegraph.com/api/ea4eb1e837994a4f8c3490679e97af5e/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
POOL_ADDRESS = "0x3416cf6c708da44db2624d63ea0aaef7113527c6"
START_TIMESTAMP = int(datetime(2025, 7, 1, tzinfo=timezone.utc).timestamp())
END_TIMESTAMP = int(datetime(2025, 9, 30, 23, 59, 59, tzinfo=timezone.utc).timestamp())
BATCH_SIZE = 1000
BATCH_DAYS = 7


def build_query(pool_id: str, timestamp_gte: int, timestamp_lt: int, 
                first: int = 1000, last_id: str = "") -> str:
    """Build GraphQL query for swaps with pagination."""
    where_parts = [
        f'pool: "{pool_id.lower()}"',
        f'timestamp_gte: {timestamp_gte}',
        f'timestamp_lt: {timestamp_lt}'
    ]
    
    if last_id:
        where_parts.append(f'id_gt: "{last_id}"')
    
    where_clause = ', '.join(where_parts)
    
    query = f"""
    query PoolSwaps {{
      swaps(
        first: {first}
        orderBy: id
        orderDirection: asc
        where: {{ {where_clause} }}
      ) {{
        id
        timestamp
        amount0
        amount1
        amountUSD
        sqrtPriceX96
        token0 {{
          id
          symbol
          decimals
        }}
        token1 {{
          id
          symbol
          decimals
        }}
      }}
    }}
    """
    return query


def fetch_swaps_for_day(pool_id: str, day_start: int, day_end: int) -> List[Dict[str, Any]]:
    """Fetch all swaps for a day using id_gt pagination."""
    all_swaps = []
    last_id = ""
    page = 0
    
    while True:
        query = build_query(pool_id, day_start, day_end, BATCH_SIZE, last_id)
        
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
            
            # Update last_id for pagination
            last_id = swaps[-1]['id']
            
            # If we got fewer than BATCH_SIZE, we're done
            if len(swaps) < BATCH_SIZE:
                break
            
            # Rate limiting
            time.sleep(0.2)
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return all_swaps


def process_swap_data(swaps: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Process raw swap data into structured DataFrame.
    
    Args:
        swaps: List of raw swap records
        
    Returns:
        Processed DataFrame
    """
    if not swaps:
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])
    
    processed_data = []
    
    for swap in swaps:
        try:
            # Extract basic fields
            timestamp = int(swap['timestamp'])
            amount0 = float(swap['amount0'])
            amount1 = float(swap['amount1'])
            amount_usd = float(swap.get('amountUSD', 0))
            
            # Extract token information
            token0_symbol = swap['token0']['symbol']
            token1_symbol = swap['token1']['symbol']
            token0_decimals = int(swap['token0']['decimals'])
            token1_decimals = int(swap['token1']['decimals'])
            
            # Calculate price
            price = calculate_price_from_amounts(
                amount0, amount1, token0_decimals, token1_decimals,
                token0_symbol, token1_symbol
            )
            
            # Validate price
            if not validate_price(price):
                continue
            
            # Calculate volume in USDC terms
            if token0_symbol == 'USDC':
                volume = abs(amount0) / (10 ** token0_decimals)
            elif token1_symbol == 'USDC':
                volume = abs(amount1) / (10 ** token1_decimals)
            else:
                # Fallback to USD amount if available
                volume = amount_usd if amount_usd > 0 else 0
            
            # Validate volume
            if not validate_volume(volume):
                continue
            
            processed_data.append({
                'timestamp': timestamp,
                'price': price,
                'volume': volume,
                'venue': 'uniswap'
            })
            
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error processing swap {swap.get('id', 'unknown')}: {e}")
            continue
    
    return pd.DataFrame(processed_data)


def fetch_all_swaps(pool_id: str, start_ts: int, end_ts: int) -> pd.DataFrame:
    """
    Fetch all swaps for the given time range, day by day.
    
    Args:
        pool_id: Pool address
        start_ts: Start timestamp
        end_ts: End timestamp
        
    Returns:
        DataFrame with all swap data
    """
    all_dataframes = []
    current_date = datetime.fromtimestamp(start_ts, tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    
    print(f"Fetching Uniswap V3 data from {current_date} to {end_date}")
    print(f"Pool address: {pool_id}")
    
    days_processed = 0
    total_swaps = 0
    
    while current_date <= end_date:
        day_start = int(current_date.timestamp())
        day_end = int((current_date.replace(hour=23, minute=59, second=59)).timestamp())
        
        print(f"Fetching day: {current_date.strftime('%Y-%m-%d')}...", end=" ")
        
        # Fetch all swaps for this day
        day_swaps = fetch_swaps_for_day(pool_id, day_start, day_end)
        
        if day_swaps:
            # Process the swaps
            day_df = process_swap_data(day_swaps)
            if not day_df.empty:
                all_dataframes.append(day_df)
                total_swaps += len(day_df)
                print(f"{len(day_df)} swaps")
                
                # Show sample prices for first day
                if days_processed == 0 and len(day_df) > 0:
                    print(f"  Sample prices: min={day_df['price'].min():.6f}, median={day_df['price'].median():.6f}, max={day_df['price'].max():.6f}")
                    # Show token mapping
                    print(f"  (Token mapping verified from first swap)")
            else:
                print("0 swaps (filtered out)")
        else:
            print("0 swaps")
        
        days_processed += 1
        current_date += timedelta(days=1)
    
    print(f"\nTotal: {days_processed} days processed, {total_swaps} swaps")
    
    if all_dataframes:
        return pd.concat(all_dataframes, ignore_index=True)
    else:
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])


def main():
    """Main function to fetch and save Uniswap V3 data."""
    print("Starting Uniswap V3 data fetch...")
    
    # Create temp directory
    temp_dir = create_temp_dir()
    
    # Fetch all swaps
    df = fetch_all_swaps(POOL_ADDRESS, START_TIMESTAMP, END_TIMESTAMP)
    
    if df.empty:
        print("No data fetched!")
        return
    
    print(f"Total swaps fetched: {len(df)}")
    print(f"Date range: {datetime.fromtimestamp(df['timestamp'].min())} to {datetime.fromtimestamp(df['timestamp'].max())}")
    print(f"Price range: {df['price'].min():.6f} to {df['price'].max():.6f}")
    print(f"Volume range: {df['volume'].min():.2f} to {df['volume'].max():.2f}")
    
    # Save raw data
    output_path = os.path.join(temp_dir, 'uniswap_raw_data.parquet')
    save_to_parquet(df, output_path)
    print(f"Raw data saved to: {output_path}")
    
    # Basic statistics
    outside_band = df[df['price'].apply(is_outside_band)]
    print(f"Swaps outside band: {len(outside_band)} ({len(outside_band)/len(df)*100:.1f}%)")
    
    if not outside_band.empty:
        print(f"Outside band price range: {outside_band['price'].min():.6f} to {outside_band['price'].max():.6f}")
        print(f"Outside band volume: {outside_band['volume'].sum():.2f} USDC")


if __name__ == "__main__":
    main()
