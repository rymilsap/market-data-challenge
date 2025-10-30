"""Parse Bybit CSV properly with correct timestamp handling"""
import pandas as pd
from datetime import datetime

print("Parsing Bybit USDCUSDT-2025-08.csv...")

# Read with proper handling of the extra column
df = pd.read_csv('USDCUSDT-2025-08.csv', usecols=['id', 'timestamp', 'price', 'volume', 'side'])

print(f"Total rows: {len(df):,}")

# Convert timestamp from milliseconds
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

# Convert to numeric
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

# Filter valid data
df_valid = df[(df['price'].notna()) & (df['volume'].notna())]

print(f"Valid rows: {len(df_valid):,}")
print(f"\nDate range: {df_valid['datetime'].min()} to {df_valid['datetime'].max()}")
print(f"Price range: {df_valid['price'].min():.6f} to {df_valid['price'].max():.6f}")
print(f"Volume stats: min=${df_valid['volume'].min():.2f}, max=${df_valid['volume'].max():.2f}, total=${df_valid['volume'].sum():,.2f}")

# Check outside band
outside_band = df_valid[(df_valid['price'] < 0.9990) | (df_valid['price'] > 1.0010)]
print(f"\nTrades outside ±0.1% band: {len(outside_band):,} ({len(outside_band)/len(df_valid)*100:.3f}%)")

if len(outside_band) > 0:
    print(f"Outside-band price range: {outside_band['price'].min():.6f} to {outside_band['price'].max():.6f}")
    print(f"Outside-band volume: ${outside_band['volume'].sum():,.2f}")

# Sample data
print("\nFirst 10 trades:")
print(df_valid[['datetime', 'price', 'volume', 'side']].head(10).to_string(index=False))

# Hourly aggregation
print("\nPreparing for hourly aggregation...")
df_valid['hour'] = df_valid['datetime'].dt.floor('H')

hourly = df_valid.groupby('hour').agg({
    'volume': 'sum',
    'price': ['count', 'min', 'max', 'mean']
}).reset_index()

print(f"Total hours covered: {len(hourly)}")
print("\nFirst 10 hours:")
print(hourly.head(10))

print("\n✅ Data looks good! Ready to integrate with Uniswap data.")

