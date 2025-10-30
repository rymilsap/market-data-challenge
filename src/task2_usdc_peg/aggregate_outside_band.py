"""
Aggregate outside-band volume data by hour for USDC peg deviation analysis.

This module processes raw Uniswap V3 and Bybit data to create hourly
aggregations of volume outside the ±0.1% band around 1.0000.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timezone
from utils import (
    load_from_parquet, save_to_csv, aggregate_hourly_data, 
    merge_venue_data, is_outside_band, create_temp_dir
)


def load_venue_data(venue: str) -> pd.DataFrame:
    """
    Load raw data for a specific venue.
    
    Args:
        venue: Venue name ('uniswap' or 'bybit')
        
    Returns:
        DataFrame with raw data
    """
    temp_dir = create_temp_dir()
    filepath = os.path.join(temp_dir, f'{venue}_raw_data.parquet')
    
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found, creating empty DataFrame")
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])
    
    try:
        df = load_from_parquet(filepath)
        print(f"Loaded {len(df)} records for {venue}")
        return df
    except Exception as e:
        print(f"Error loading {venue} data: {e}")
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'venue'])


def process_venue_data(df: pd.DataFrame, venue: str) -> pd.DataFrame:
    """
    Process raw venue data and aggregate by hour.
    
    Args:
        df: Raw venue data
        venue: Venue name
        
    Returns:
        Aggregated hourly data
    """
    if df.empty:
        print(f"No data for {venue}, creating empty aggregation")
        return pd.DataFrame(columns=[
            'time', f'{venue}_volume', f'{venue}_min_price', f'{venue}_max_price'
        ])
    
    # Filter for outside band trades
    df['outside_band'] = df['price'].apply(is_outside_band)
    outside_df = df[df['outside_band']].copy()
    
    print(f"{venue}: {len(outside_df)} trades outside band out of {len(df)} total")
    
    if outside_df.empty:
        print(f"No outside-band trades for {venue}")
        return pd.DataFrame(columns=[
            'time', f'{venue}_volume', f'{venue}_min_price', f'{venue}_max_price'
        ])
    
    # Aggregate by hour
    agg_df = aggregate_hourly_data(outside_df, venue)
    print(f"{venue}: Aggregated into {len(agg_df)} hours")
    
    return agg_df


def create_full_hour_range() -> pd.DataFrame:
    """
    Create DataFrame with all hours in the analysis period.
    
    Returns:
        DataFrame with all hours from 2025-07-01 to 2025-09-30
    """
    start_time = datetime(2025, 7, 1, tzinfo=timezone.utc)
    end_time = datetime(2025, 9, 30, 23, tzinfo=timezone.utc)
    
    hours = pd.date_range(start=start_time, end=end_time, freq='H')
    hour_strings = [h.strftime('%Y-%m-%dT%H:%M:%SZ') for h in hours]
    
    return pd.DataFrame({'time': hour_strings})


def merge_and_fill_data(uniswap_df: pd.DataFrame, bybit_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge venue data and fill missing values.
    
    Args:
        uniswap_df: Uniswap aggregated data
        bybit_df: Bybit aggregated data
        
    Returns:
        Merged DataFrame with all required columns
    """
    # Create base DataFrame with all hours
    base_df = create_full_hour_range()
    
    # Merge with venue data
    result_df = base_df.merge(uniswap_df, on='time', how='left')
    result_df = result_df.merge(bybit_df, on='time', how='left')
    
    # Fill missing values
    result_df['uniswap_volume'] = result_df['uniswap_volume'].fillna(0)
    result_df['bybit_volume'] = result_df['bybit_volume'].fillna(0)
    
    # Ensure proper column order
    columns = [
        'time', 'uniswap_volume', 'bybit_volume', 
        'uniswap_min_price', 'uniswap_max_price',
        'bybit_min_price', 'bybit_max_price'
    ]
    
    for col in columns:
        if col not in result_df.columns:
            result_df[col] = np.nan
    
    return result_df[columns]


def validate_output_data(df: pd.DataFrame) -> bool:
    """
    Validate the output data for correctness.
    
    Args:
        df: Output DataFrame
        
    Returns:
        True if data is valid, False otherwise
    """
    # Check required columns
    required_columns = [
        'time', 'uniswap_volume', 'bybit_volume',
        'uniswap_min_price', 'uniswap_max_price',
        'bybit_min_price', 'bybit_max_price'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            return False
    
    # Check data types
    if not pd.api.types.is_numeric_dtype(df['uniswap_volume']):
        print("uniswap_volume is not numeric")
        return False
    
    if not pd.api.types.is_numeric_dtype(df['bybit_volume']):
        print("bybit_volume is not numeric")
        return False
    
    # Check for negative volumes
    if (df['uniswap_volume'] < 0).any():
        print("Found negative uniswap_volume")
        return False
    
    if (df['bybit_volume'] < 0).any():
        print("Found negative bybit_volume")
        return False
    
    # Check time format
    try:
        pd.to_datetime(df['time'])
    except:
        print("Invalid time format")
        return False
    
    print("Data validation passed!")
    return True


def generate_summary_stats(df: pd.DataFrame) -> None:
    """
    Generate summary statistics for the output data.
    
    Args:
        df: Output DataFrame
    """
    print("\n=== Summary Statistics ===")
    print(f"Total hours: {len(df)}")
    print(f"Date range: {df['time'].min()} to {df['time'].max()}")
    
    # Volume statistics
    print(f"\nUniswap Volume:")
    print(f"  Total outside band: {df['uniswap_volume'].sum():,.2f} USDC")
    print(f"  Average per hour: {df['uniswap_volume'].mean():,.2f} USDC")
    print(f"  Max in single hour: {df['uniswap_volume'].max():,.2f} USDC")
    print(f"  Hours with volume: {(df['uniswap_volume'] > 0).sum()}")
    
    print(f"\nBybit Volume:")
    print(f"  Total outside band: {df['bybit_volume'].sum():,.2f} USDC")
    print(f"  Average per hour: {df['bybit_volume'].mean():,.2f} USDC")
    print(f"  Max in single hour: {df['bybit_volume'].max():,.2f} USDC")
    print(f"  Hours with volume: {(df['bybit_volume'] > 0).sum()}")
    
    # Price statistics
    uniswap_prices = df[df['uniswap_volume'] > 0]
    bybit_prices = df[df['bybit_volume'] > 0]
    
    if not uniswap_prices.empty:
        print(f"\nUniswap Price Range (outside band):")
        print(f"  Min: {uniswap_prices['uniswap_min_price'].min():.6f}")
        print(f"  Max: {uniswap_prices['uniswap_max_price'].max():.6f}")
    
    if not bybit_prices.empty:
        print(f"\nBybit Price Range (outside band):")
        print(f"  Min: {bybit_prices['bybit_min_price'].min():.6f}")
        print(f"  Max: {bybit_prices['bybit_max_price'].max():.6f}")


def main():
    """Main function to aggregate outside-band data."""
    print("Starting USDC peg deviation aggregation...")
    
    # Load raw data
    print("Loading Uniswap data...")
    uniswap_df = load_venue_data('uniswap')
    
    print("Loading Bybit data...")
    bybit_df = load_venue_data('bybit')
    
    # Process venue data
    print("Processing Uniswap data...")
    uniswap_agg = process_venue_data(uniswap_df, 'uniswap')
    
    print("Processing Bybit data...")
    bybit_agg = process_venue_data(bybit_df, 'bybit')
    
    # Merge data
    print("Merging venue data...")
    final_df = merge_and_fill_data(uniswap_agg, bybit_agg)
    
    # Validate output
    if not validate_output_data(final_df):
        print("Data validation failed!")
        return
    
    # Generate summary statistics
    generate_summary_stats(final_df)
    
    # Save output
    output_path = 'outputs/usdc_peg_outside_band_hourly.csv'
    os.makedirs('outputs', exist_ok=True)
    save_to_csv(final_df, output_path)
    
    print(f"\nOutput saved to: {output_path}")
    print(f"Output shape: {final_df.shape}")
    
    # Show sample
    print("\nSample output:")
    print(final_df.head(10))


if __name__ == "__main__":
    main()

