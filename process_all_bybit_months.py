"""
Process all three months of Bybit data (July, August, September 2025)
and generate the complete USDC peg deviation analysis.
"""

import pandas as pd
import os
from datetime import datetime, timezone, timedelta

def process_month(csv_file, month_name):
    """Process a single month's Bybit CSV."""
    print(f"\nProcessing {month_name}...")
    print("=" * 60)
    
    # Read CSV
    df = pd.read_csv(csv_file, usecols=['id', 'timestamp', 'price', 'volume', 'side'])
    print(f"Loaded {len(df):,} rows")
    
    # Convert timestamp from milliseconds
    df['timestamp'] = (df['timestamp'] / 1000).astype(int)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    
    # Convert to numeric
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # Filter valid data
    df = df[(df['price'].notna()) & (df['volume'].notna()) & (df['price'] > 0)]
    
    print(f"Valid rows: {len(df):,}")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Price range: {df['price'].min():.6f} to {df['price'].max():.6f}")
    print(f"Total volume: ${df['volume'].sum():,.2f}")
    
    # Check outside band
    outside_band = df[(df['price'] < 0.9990) | (df['price'] > 1.0010)]
    print(f"Trades outside ±0.1% band: {len(outside_band):,} ({len(outside_band)/len(df)*100:.4f}%)")
    
    if len(outside_band) > 0:
        print(f"  Outside-band price range: {outside_band['price'].min():.6f} to {outside_band['price'].max():.6f}")
        print(f"  Outside-band volume: ${outside_band['volume'].sum():,.2f}")
    
    # Prepare output
    result = df[['timestamp', 'price', 'volume']].copy()
    result['venue'] = 'bybit'
    
    return result, outside_band

# Process all three months
print("=" * 60)
print("PROCESSING BYBIT DATA: JULY-SEPTEMBER 2025")
print("=" * 60)

july_df, july_outside = process_month('USDCUSDT-2025-07.csv', 'July 2025')
august_df, august_outside = process_month('USDCUSDT-2025-08.csv', 'August 2025')
september_df, september_outside = process_month('USDCUSDT-2025-09.csv', 'September 2025')

# Combine all months
print("\n" + "=" * 60)
print("COMBINING DATA")
print("=" * 60)

all_data = pd.concat([july_df, august_df, september_df], ignore_index=True)
all_outside = pd.concat([july_outside, august_outside, september_outside], ignore_index=True)

print(f"Total trades: {len(all_data):,}")
print(f"Total outside band: {len(all_outside):,} ({len(all_outside)/len(all_data)*100:.4f}%)")

if len(all_outside) > 0:
    print(f"Overall price range (outside band): {all_outside['price'].min():.6f} to {all_outside['price'].max():.6f}")
    print(f"Total outside-band volume: ${all_outside['volume'].sum():,.2f}")

# Save combined data
print("\nSaving combined data...")
os.makedirs('temp', exist_ok=True)
all_data.to_parquet('temp/bybit_raw_data_all.parquet', index=False)
print("Saved to: temp/bybit_raw_data_all.parquet")

# Generate hourly aggregation
print("\n" + "=" * 60)
print("GENERATING HOURLY AGGREGATION")
print("=" * 60)

# Create full hour range July 1 - September 30
start_date = datetime(2025, 7, 1, tzinfo=timezone.utc)
end_date = datetime(2025, 9, 30, 23, tzinfo=timezone.utc)
hours = pd.date_range(start=start_date, end=end_date, freq='h')

# Initialize result
result = pd.DataFrame({
    'time': [h.strftime('%Y-%m-%dT%H:%M:%SZ') for h in hours]
})

# Aggregate outside-band trades by hour
if len(all_outside) > 0:
    all_outside['datetime'] = pd.to_datetime(all_outside['timestamp'], unit='s', utc=True)
    all_outside['hour'] = all_outside['datetime'].dt.floor('h')
    
    bybit_hourly = all_outside.groupby('hour').agg({
        'volume': 'sum',
        'price': ['min', 'max']
    }).reset_index()
    
    bybit_hourly.columns = ['hour', 'bybit_volume', 'bybit_min_price', 'bybit_max_price']
    bybit_hourly['time'] = bybit_hourly['hour'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Merge with full hour range
    result = result.merge(bybit_hourly[['time', 'bybit_volume', 'bybit_min_price', 'bybit_max_price']], 
                         on='time', how='left')
else:
    result['bybit_volume'] = 0.0
    result['bybit_min_price'] = float('nan')
    result['bybit_max_price'] = float('nan')

# Add Uniswap columns (empty for now)
result['uniswap_volume'] = 0.0
result['uniswap_min_price'] = float('nan')
result['uniswap_max_price'] = float('nan')

# Fill NaN volumes with 0
result['bybit_volume'] = result['bybit_volume'].fillna(0.0)
result['uniswap_volume'] = result['uniswap_volume'].fillna(0.0)

# Reorder columns to match specification
result = result[['time', 'uniswap_volume', 'bybit_volume', 
                'uniswap_min_price', 'uniswap_max_price',
                'bybit_min_price', 'bybit_max_price']]

print(f"Generated {len(result)} hourly records")
print(f"Hours with Bybit outside-band activity: {(result['bybit_volume'] > 0).sum()}")

# Save final output
output_path = 'outputs/usdc_peg_outside_band_hourly.csv'
result.to_csv(output_path, index=False)

print(f"\nSaved to: {output_path}")

# Summary statistics
print("\n" + "=" * 60)
print("FINAL SUMMARY: JULY-SEPTEMBER 2025")
print("=" * 60)

print(f"Total period: 2,208 hours (92 days)")
print(f"Total Bybit trades analyzed: {len(all_data):,}")
print(f"Total Bybit volume: ${all_data['volume'].sum():,.2f}")
print(f"Trades outside ±0.1% band: {len(all_outside):,} ({len(all_outside)/len(all_data)*100:.4f}%)")

if len(all_outside) > 0:
    print(f"Outside-band volume: ${all_outside['volume'].sum():,.2f}")
    print(f"Hours with outside-band activity: {(result['bybit_volume'] > 0).sum()}")
    print(f"Price deviation range: {all_outside['price'].min():.6f} to {all_outside['price'].max():.6f}")
else:
    print("NO PEG DEVIATIONS DETECTED - PERFECT STABILITY!")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE!")
print("=" * 60)

