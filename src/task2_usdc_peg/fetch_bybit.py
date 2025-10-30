"""
Fetch Bybit USDC/USDT spot trade data.

This module queries the Bybit public REST API for USDC/USDT spot trades
and processes the data for peg deviation analysis.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import time
import os
from utils import (
    validate_price, validate_volume, round_to_hour, is_outside_band,
    save_to_parquet, create_temp_dir
)

# Configuration
BYBIT_BASE_URL = "https://api.bybit.com"
SYMBOL = "USDCUSDT"
START_TIMESTAMP = int(datetime(2025, 7, 1, tzinfo=timezone.utc).timestamp())
END_TIMESTAMP = int(datetime(2025, 9, 30, 23, 59, 59, tzinfo=timezone.utc).timestamp())
BATCH_SIZE = 1000  # Number of trades per request
RATE_LIMIT_DELAY = 0.1  # Seconds between requests


def fetch_trades_batch(start_time_ms: int, end_time_ms: int, 
                      limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch a batch of trades from Bybit API.
    
    Args:
        start_time_ms: Start timestamp in milliseconds
        end_time_ms: End timestamp in milliseconds
        limit: Maximum number of trades to fetch
        
    Returns:
        List of trade records
    """
    url = f"{BYBIT_BASE_URL}/v5/market/recent-trade"
    
    params = {
        'category': 'spot',
        'symbol': SYMBOL,
        'limit': limit,
        'startTime': start_time_ms,
        'endTime': end_time_ms
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data.get('retCode') != 0:
            print(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
            return []
        
        return data.get('result', {}).get('list', [])
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def process_trade_data(trades: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Process raw trade data into structured DataFrame.
    
    Args:
        trades: List of raw trade records
        
    Returns:
        Processed DataFrame
    """
    if not trades:
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])
    
    processed_data = []
    
    for trade in trades:
        try:
            # Extract fields
            timestamp_ms = int(trade['time'])
            timestamp = timestamp_ms // 1000  # Convert to seconds
            
            price = float(trade['price'])
            volume = float(trade['size'])  # Size is in USDC terms for USDCUSDT
            
            # Validate data
            if not validate_price(price) or not validate_volume(volume):
                continue
            
            processed_data.append({
                'timestamp': timestamp,
                'price': price,
                'volume': volume,
                'venue': 'bybit'
            })
            
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error processing trade: {e}")
            continue
    
    return pd.DataFrame(processed_data)


def fetch_all_trades(start_ts: int, end_ts: int) -> pd.DataFrame:
    """
    Fetch all trades for the given time range.
    
    Args:
        start_ts: Start timestamp in seconds
        end_ts: End timestamp in seconds
        
    Returns:
        DataFrame with all trade data
    """
    all_trades = []
    current_ts = start_ts
    batch_days = 1  # Fetch 1 day at a time to avoid rate limits
    
    print(f"Fetching Bybit data from {datetime.fromtimestamp(start_ts)} to {datetime.fromtimestamp(end_ts)}")
    
    while current_ts < end_ts:
        # Calculate batch end timestamp
        batch_end_ts = min(current_ts + (batch_days * 24 * 3600), end_ts)
        
        print(f"Fetching batch: {datetime.fromtimestamp(current_ts)} to {datetime.fromtimestamp(batch_end_ts)}")
        
        # Convert to milliseconds for API
        start_time_ms = current_ts * 1000
        end_time_ms = batch_end_ts * 1000
        
        # Fetch trades for this batch
        batch_trades = fetch_trades_batch(start_time_ms, end_time_ms, BATCH_SIZE)
        
        if not batch_trades:
            print("No trades found in this batch")
            current_ts = batch_end_ts
            continue
        
        # Process batch data
        batch_df = process_trade_data(batch_trades)
        if not batch_df.empty:
            all_trades.append(batch_df)
            print(f"Processed {len(batch_df)} trades in this batch")
        
        # Move to next batch
        current_ts = batch_end_ts
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
    
    if all_trades:
        return pd.concat(all_trades, ignore_index=True)
    else:
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])


def fetch_trades_by_hour(start_ts: int, end_ts: int) -> pd.DataFrame:
    """
    Alternative method: fetch trades hour by hour to ensure completeness.
    
    Args:
        start_ts: Start timestamp in seconds
        end_ts: End timestamp in seconds
        
    Returns:
        DataFrame with all trade data
    """
    all_trades = []
    current_ts = start_ts
    
    print(f"Fetching Bybit data hour by hour from {datetime.fromtimestamp(start_ts)} to {datetime.fromtimestamp(end_ts)}")
    
    while current_ts < end_ts:
        # Calculate hour end timestamp
        hour_end_ts = min(current_ts + 3600, end_ts)
        
        # Convert to milliseconds for API
        start_time_ms = current_ts * 1000
        end_time_ms = hour_end_ts * 1000
        
        # Fetch trades for this hour
        hour_trades = fetch_trades_batch(start_time_ms, end_time_ms, BATCH_SIZE)
        
        if hour_trades:
            # Process hour data
            hour_df = process_trade_data(hour_trades)
            if not hour_df.empty:
                all_trades.append(hour_df)
                print(f"Processed {len(hour_df)} trades for hour {datetime.fromtimestamp(current_ts)}")
        
        # Move to next hour
        current_ts = hour_end_ts
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
    
    if all_trades:
        return pd.concat(all_trades, ignore_index=True)
    else:
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])


def main():
    """Main function to fetch and save Bybit data."""
    print("Starting Bybit data fetch...")
    
    # Create temp directory
    temp_dir = create_temp_dir()
    
    # Try hourly fetch first (more reliable)
    print("Attempting hourly fetch...")
    df = fetch_trades_by_hour(START_TIMESTAMP, END_TIMESTAMP)
    
    if df.empty:
        print("Hourly fetch failed, trying daily batches...")
        df = fetch_all_trades(START_TIMESTAMP, END_TIMESTAMP)
    
    if df.empty:
        print("No data fetched!")
        return
    
    print(f"Total trades fetched: {len(df)}")
    print(f"Date range: {datetime.fromtimestamp(df['timestamp'].min())} to {datetime.fromtimestamp(df['timestamp'].max())}")
    print(f"Price range: {df['price'].min():.6f} to {df['price'].max():.6f}")
    print(f"Volume range: {df['volume'].min():.2f} to {df['volume'].max():.2f}")
    
    # Save raw data
    output_path = os.path.join(temp_dir, 'bybit_raw_data.parquet')
    save_to_parquet(df, output_path)
    print(f"Raw data saved to: {output_path}")
    
    # Basic statistics
    outside_band = df[df['price'].apply(is_outside_band)]
    print(f"Trades outside band: {len(outside_band)} ({len(outside_band)/len(df)*100:.1f}%)")
    
    if not outside_band.empty:
        print(f"Outside band price range: {outside_band['price'].min():.6f} to {outside_band['price'].max():.6f}")
        print(f"Outside band volume: {outside_band['volume'].sum():.2f} USDC")


if __name__ == "__main__":
    main()

