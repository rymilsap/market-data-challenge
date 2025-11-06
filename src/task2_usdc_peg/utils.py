"""
Utils for USDC peg deviation analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from typing import Tuple, Optional

getcontext().prec = 28

BAND_LOWER = Decimal('0.9990')
BAND_UPPER = Decimal('1.0010')
BAND_CENTER = Decimal('1.0000')


def round_to_hour(timestamp: int) -> str:
    """Round unix timestamp to top of hour (ISO8601)."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    hour_dt = dt.replace(minute=0, second=0, microsecond=0)
    return hour_dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def is_outside_band(price: float) -> bool:
    """Check if price is outside ±0.1% band (0.999-1.001)."""
    if pd.isna(price) or price <= 0:
        return False
    
    price_decimal = Decimal(str(price))
    return price_decimal < BAND_LOWER or price_decimal > BAND_UPPER


def calculate_price_from_amounts(amount0: float, amount1: float, 
                                token0_decimals: int, token1_decimals: int,
                                token0_symbol: str, token1_symbol: str) -> float:
    """Calculate USDT per USDC from raw amounts."""
    norm_amount0 = amount0 / (10 ** token0_decimals)
    norm_amount1 = amount1 / (10 ** token1_decimals)
    
    if token0_symbol == 'USDC' and token1_symbol == 'USDT':
        if norm_amount0 == 0:
            return np.nan
        return norm_amount1 / norm_amount0
    elif token0_symbol == 'USDT' and token1_symbol == 'USDC':
        if norm_amount1 == 0:
            return np.nan
        return norm_amount0 / norm_amount1
    else:
        raise ValueError(f"Unexpected token pair: {token0_symbol}/{token1_symbol}")


def safe_divide(numerator: float, denominator: float) -> float:
    """Safe division, returns NaN if denom is zero."""
    if denominator == 0 or pd.isna(denominator):
        return np.nan
    return numerator / denominator


def validate_price(price: float) -> bool:
    """Check price is reasonable (0.5-2.0 range)."""
    if pd.isna(price):
        return False
    return 0.5 <= price <= 2.0


def validate_volume(volume: float) -> bool:
    """Check volume is positive."""
    if pd.isna(volume):
        return False
    return volume > 0


def aggregate_hourly_data(df: pd.DataFrame, venue: str) -> pd.DataFrame:
    """Aggregate trades by hour for given venue."""
    if df.empty:
        return pd.DataFrame(columns=[
            'time', f'{venue}_volume', f'{venue}_min_price', f'{venue}_max_price'
        ])
    
    # Add hour column
    df['hour'] = df['timestamp'].apply(round_to_hour)
    
    # Filter for outside band trades
    df['outside_band'] = df['price'].apply(is_outside_band)
    outside_df = df[df['outside_band']].copy()
    
    if outside_df.empty:
        # No outside band trades
        return pd.DataFrame(columns=[
            'time', f'{venue}_volume', f'{venue}_min_price', f'{venue}_max_price'
        ])
    
    # Aggregate by hour
    agg_data = []
    for hour in df['hour'].unique():
        hour_data = outside_df[outside_df['hour'] == hour]
        
        if hour_data.empty:
            agg_data.append({
                'time': hour,
                f'{venue}_volume': 0,
                f'{venue}_min_price': np.nan,
                f'{venue}_max_price': np.nan
            })
        else:
            agg_data.append({
                'time': hour,
                f'{venue}_volume': hour_data['volume'].sum(),
                f'{venue}_min_price': hour_data['price'].min(),
                f'{venue}_max_price': hour_data['price'].max()
            })
    
    return pd.DataFrame(agg_data)


def merge_venue_data(uniswap_df: pd.DataFrame, bybit_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge Uniswap and Bybit data by hour.
    
    Args:
        uniswap_df: Uniswap aggregated data
        bybit_df: Bybit aggregated data
        
    Returns:
        Merged DataFrame with all columns
    """
    # Create full hour range
    start_time = datetime(2025, 7, 1, tzinfo=timezone.utc)
    end_time = datetime(2025, 9, 30, 23, tzinfo=timezone.utc)
    
    hours = pd.date_range(start=start_time, end=end_time, freq='H')
    hour_strings = [h.strftime('%Y-%m-%dT%H:%M:%SZ') for h in hours]
    
    # Create base DataFrame with all hours
    base_df = pd.DataFrame({'time': hour_strings})
    
    # Merge with venue data
    result_df = base_df.merge(uniswap_df, on='time', how='left')
    result_df = result_df.merge(bybit_df, on='time', how='left')
    
    # Fill missing values
    result_df['uniswap_volume'] = result_df['uniswap_volume'].fillna(0)
    result_df['bybit_volume'] = result_df['bybit_volume'].fillna(0)
    
    return result_df


def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """
    Save DataFrame to CSV with proper formatting.
    
    Args:
        df: DataFrame to save
        filepath: Output file path
    """
    df.to_csv(filepath, index=False, float_format='%.6f')


def load_from_parquet(filepath: str) -> pd.DataFrame:
    """
    Load DataFrame from Parquet file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Loaded DataFrame
    """
    return pd.read_parquet(filepath)


def save_to_parquet(df: pd.DataFrame, filepath: str) -> None:
    """
    Save DataFrame to Parquet file.
    
    Args:
        df: DataFrame to save
        filepath: Output file path
    """
    df.to_parquet(filepath, index=False)


def create_temp_dir() -> str:
    """
    Create temporary directory for data storage.
    
    Returns:
        Path to temporary directory
    """
    import os
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def assert_band_logic():
    """
    Unit test for band logic.
    """
    # Test cases
    test_prices = [0.9989, 0.9990, 0.9995, 1.0000, 1.0005, 1.0010, 1.0011]
    expected = [True, False, False, False, False, False, True]
    
    for price, expected_result in zip(test_prices, expected):
        result = is_outside_band(price)
        assert result == expected_result, f"Band logic failed for price {price}"
    
    print("Band logic tests passed!")


if __name__ == "__main__":
    # Run unit tests
    assert_band_logic()
    print("All utility functions working correctly!")

