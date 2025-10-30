"""
Process Bybit historical CSV files for USDC/USDT trading data.

This module processes the downloaded Bybit trade archives for USDC/USDT
and prepares them for peg deviation analysis.
"""

import pandas as pd
import os
from datetime import datetime, timezone
import sys

def process_bybit_csv(csv_path: str, start_date: str = '2025-07-01', end_date: str = '2025-09-30') -> pd.DataFrame:
    """
    Process Bybit CSV file and extract relevant data.
    
    Args:
        csv_path: Path to the Bybit CSV file
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with columns: timestamp, price, volume, venue
    """
    print(f"Processing Bybit CSV: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path, usecols=['id', 'timestamp', 'price', 'volume', 'side'])
    
    print(f"Loaded {len(df):,} rows")
    
    # Convert timestamp from milliseconds to seconds
    df['timestamp'] = (df['timestamp'] / 1000).astype(int)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    
    # Convert to numeric
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # Filter valid data
    df = df[(df['price'].notna()) & (df['volume'].notna()) & (df['price'] > 0)]
    
    # Filter date range
    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date + ' 23:59:59', utc=True)
    df = df[(df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)]
    
    print(f"After filtering: {len(df):,} rows")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Price range: {df['price'].min():.6f} to {df['price'].max():.6f}")
    
    # Prepare output format
    result = df[['timestamp', 'price', 'volume']].copy()
    result['venue'] = 'bybit'
    
    return result


def main():
    """Main function to process Bybit CSV."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Bybit CSV files')
    parser.add_argument('csv_file', help='Path to Bybit CSV file')
    parser.add_argument('--start', default='2025-07-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2025-09-30', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='temp/bybit_raw_data.parquet', help='Output file')
    
    args = parser.parse_args()
    
    # Process CSV
    df = process_bybit_csv(args.csv_file, args.start, args.end)
    
    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_parquet(args.output, index=False)
    print(f"Saved to: {args.output}")
    
    # Statistics
    outside_band = df[(df['price'] < 0.9990) | (df['price'] > 1.0010)]
    print(f"\nTrades outside ±0.1% band: {len(outside_band):,} ({len(outside_band)/len(df)*100:.3f}%)")
    
    if len(outside_band) > 0:
        print(f"Outside-band volume: ${outside_band['volume'].sum():,.2f}")


if __name__ == "__main__":
    main()

