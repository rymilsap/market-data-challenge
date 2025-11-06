"""
Uniswap V2/V3 delta-neutral hedge calculator.
"""

from decimal import Decimal, getcontext
from typing import Tuple

getcontext().prec = 28


def calculate_v2_hedge(eth_price: float, position_usd: float) -> float:
    """V2 50/50 pool: short size = V/(2P)"""
    if eth_price <= 0 or position_usd <= 0:
        raise ValueError("Price and position size must be positive")
    
    return position_usd / (2 * eth_price)


def calculate_v3_hedge(eth_price: float, liquidity: float, 
                      range_pct: float = 0.10) -> Tuple[float, dict]:
    """V3 concentrated liquidity: delta = L / (2*P^1.5)"""
    if eth_price <= 0 or liquidity <= 0:
        raise ValueError("Price and liquidity must be positive")
    
    p_low = eth_price * (1 - range_pct)
    p_high = eth_price * (1 + range_pct)
    
    hedge_size = liquidity / (2 * (eth_price ** 1.5))
    
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
    """Calculate funding costs for perp hedge."""
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
    print("=== Uniswap Hedged LP Calculator ===\n")
    
    eth_price = 2000.0
    position_usd = 100000.0
    liquidity = 1000.0
    
    print(f"ETH Price: ${eth_price:,.2f}")
    print(f"Position Size: ${position_usd:,.2f}")
    print(f"V3 Liquidity: {liquidity:,.2f}\n")
    
    v2_hedge = calculate_v2_hedge(eth_price, position_usd)
    print(f"V2 50/50 Hedge Size: {v2_hedge:.4f} ETH")
    print(f"V2 Hedge Value: ${v2_hedge * eth_price:,.2f}\n")
    
    v3_hedge, v3_info = calculate_v3_hedge(eth_price, liquidity)
    print(f"V3 ±10% Hedge Size: {v3_hedge:.4f} ETH")
    print(f"V3 Hedge Value: ${v3_hedge * eth_price:,.2f}")
    print(f"V3 Position ETH: {v3_info['eth_amount']:.4f}")
    print(f"V3 Position USDT: ${v3_info['usdt_amount']:,.2f}")
    print(f"V3 Range: ${v3_info['p_low']:.2f} - ${v3_info['p_high']:.2f}\n")
    
    v2_costs = analyze_hedge_costs(v2_hedge, eth_price)
    print("V2 Hedge Costs (8hr funding @ 0.01%):")
    print(f"  8hr: ${v2_costs['funding_cost_8h']:.2f}")
    print(f"  Daily: ${v2_costs['funding_cost_daily']:.2f}")
    print(f"  Annual: ${v2_costs['funding_cost_annual']:.2f}\n")
    
    print("Assumptions: local delta only, no rebalancing, perfect execution")


if __name__ == "__main__":
    main()

