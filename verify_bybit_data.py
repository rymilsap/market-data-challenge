"""Verify Bybit CSV data structure and timestamps"""
import pandas as pd

print("Loading Bybit CSV...")
df = pd.read_csv('USDCUSDT-2025-08.csv')

print(f"\nColumns: {list(df.columns)}")
print(f"Total rows: {len(df):,}")

# Convert timestamp - try both ms and seconds
try:
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    if df['datetime'].min().year < 2020:
        # If dates are too old, try seconds
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
except:
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)

# Convert price and volume to numeric
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

# Filter valid rows
df_valid = df[(df['price'].notna()) & (df['volume'].notna()) & (df['price'] > 0) & (df['price'] < 2)]

print(f"\nValid rows (price 0-2 range): {len(df_valid):,} of {len(df):,}")
print(f"Date range: {df_valid['datetime'].min()} to {df_valid['datetime'].max()}")
print(f"Price range: {df_valid['price'].min():.6f} to {df_valid['price'].max():.6f}")
print(f"Volume range: {df_valid['volume'].min():.2f} to {df_valid['volume'].max():.2f}")

# Show first few rows
print("\nFirst 10 valid rows:")
print(df_valid[['datetime', 'price', 'volume', 'side']].head(10))

# Check for outside-band prices
outside_band = df_valid[(df_valid['price'] < 0.9990) | (df_valid['price'] > 1.0010)]
print(f"\nTrades outside ±0.1% band: {len(outside_band):,} ({len(outside_band)/len(df_valid)*100:.2f}%)")

if len(outside_band) > 0:
    print(f"Outside-band price range: {outside_band['price'].min():.6f} to {outside_band['price'].max():.6f}")
    print(f"Outside-band volume: ${outside_band['volume'].sum():,.2f}")
    
    # Show distribution by hour
    outside_band['hour'] = outside_band['datetime'].dt.floor('H')
    hourly_stats = outside_band.groupby('hour').agg({
        'volume': 'sum',
        'price': ['min', 'max', 'count']
    }).reset_index()
    print(f"\nHourly distribution (first 10 hours with activity):")
    print(hourly_stats.head(10))
