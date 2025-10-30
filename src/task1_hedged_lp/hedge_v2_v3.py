"""
Hedged LP Calculator for Uniswap V2 and V3

This module provides functions to calculate delta-neutral hedge sizes
for Uniswap V2 50/50 pools and V3 concentrated liquidity positions.
"""

from decimal import Decimal, getcontext
from typing import Tuple

# Set precision for decimal calculations
getcontext().prec = 28


def calculate_v2_hedge(eth_price: float, position_usd: float) -> float:
    """
    Calculate required short ETH size for V2 50/50 pool delta neutrality.
    
    Args:
        eth_price: Current ETH price in USDT
        position_usd: Total USD value of LP position
        
    Returns:
        Required short ETH amount for delta neutrality
    """
    if eth_price <= 0 or position_usd <= 0:
        raise ValueError("Price and position size must be positive")
    
    # V2 50/50 pool delta = V/(2P)
    hedge_size = position_usd / (2 * eth_price)
    return hedge_size


def calculate_v3_hedge(eth_price: float, liquidity: float, 
                      range_pct: float = 0.10) -> Tuple[float, dict]:
    """
    Calculate required short ETH size for V3 concentrated liquidity delta neutrality.
    
    Args:
        eth_price: Current ETH price in USDT
        liquidity: V3 liquidity amount
        range_pct: Range percentage (default 0.10 for ±10%)
        
    Returns:
        Tuple of (hedge_size, position_info)
    """
    if eth_price <= 0 or liquidity <= 0:
        raise ValueError("Price and liquidity must be positive")
    
    # Calculate range bounds
    p_low = eth_price * (1 - range_pct)
    p_high = eth_price * (1 + range_pct)
    
    # V3 delta = L × (1/(2P₀^(3/2)))
    hedge_size = liquidity / (2 * (eth_price ** 1.5))
    
    # Calculate position token amounts
    sqrt_p = eth_price ** 0.5
    sqrt_p_low = p_low ** 0.5
    sqrt_p_high = p_high ** 0.5
    
    eth_amount = liquidity * (1/sqrt_p - 1/sqrt_p_high)
    usdt_amount = liquidity * (sqrt_p - sqrt_p_low)
    
    position_info = {
        'eth_amount': eth_amount,
        'usdt_amount': usdt_amount,
        'p_low': p_low,
        'p_high': p_high,
        'range_pct': range_pct
    }
    
    return hedge_size, position_info


def analyze_hedge_costs(hedge_size: float, eth_price: float, 
                       funding_rate: float = 0.0001) -> dict:
    """
    Analyze costs associated with maintaining the hedge.
    
    Args:
        hedge_size: Size of short ETH position
        eth_price: Current ETH price
        funding_rate: CEX perp funding rate (8-hourly)
        
    Returns:
        Dictionary of cost analysis
    """
    notional_value = hedge_size * eth_price
    
    costs = {
        'hedge_size_eth': hedge_size,
        'notional_value_usd': notional_value,
        'funding_cost_8h': notional_value * funding_rate,
        'funding_cost_daily': notional_value * funding_rate * 3,
        'funding_cost_annual': notional_value * funding_rate * 3 * 365
    }
    
    return costs


def main():
    """Example usage and demonstration."""
    print("=== Uniswap Hedged LP Calculator ===\n")
    
    # Example parameters
    eth_price = 2000.0  # $2000 ETH
    position_usd = 100000.0  # $100k position
    liquidity = 1000.0  # V3 liquidity amount
    
    print(f"ETH Price: ${eth_price:,.2f}")
    print(f"Position Size: ${position_usd:,.2f}")
    print(f"V3 Liquidity: {liquidity:,.2f}\n")
    
    # V2 Calculation
    v2_hedge = calculate_v2_hedge(eth_price, position_usd)
    print(f"V2 50/50 Hedge Size: {v2_hedge:.4f} ETH")
    print(f"V2 Hedge Value: ${v2_hedge * eth_price:,.2f}\n")
    
    # V3 Calculation
    v3_hedge, v3_info = calculate_v3_hedge(eth_price, liquidity)
    print(f"V3 ±10% Hedge Size: {v3_hedge:.4f} ETH")
    print(f"V3 Hedge Value: ${v3_hedge * eth_price:,.2f}")
    print(f"V3 Position ETH: {v3_info['eth_amount']:.4f}")
    print(f"V3 Position USDT: ${v3_info['usdt_amount']:,.2f}")
    print(f"V3 Range: ${v3_info['p_low']:.2f} - ${v3_info['p_high']:.2f}\n")
    
    # Cost Analysis
    v2_costs = analyze_hedge_costs(v2_hedge, eth_price)
    print("V2 Hedge Costs (8-hourly funding):")
    print(f"  Funding Cost: ${v2_costs['funding_cost_8h']:.2f}")
    print(f"  Daily Cost: ${v2_costs['funding_cost_daily']:.2f}")
    print(f"  Annual Cost: ${v2_costs['funding_cost_annual']:.2f}\n")
    
    print("Key Assumptions:")
    print("- Local delta neutrality (small price movements only)")
    print("- No rebalancing after initial hedge")
    print("- Perfect liquidity execution")
    print("- Continuous price movements")


if __name__ == "__main__":
    main()

