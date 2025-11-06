# Hedged LP Mathematical Formulations

## Uniswap V2 50/50 Pool Delta Derivation

### Setup

- **P**: ETH price in USDT at entry
- **V**: Total USD value of LP position
- **x**: ETH amount in pool
- **y**: USDT amount in pool

### V2 Pool State at Entry

For a 50/50 pool by USD value:

- ETH value: `V/2`
- USDT value: `V/2`
- ETH amount: `x = V/(2P)`
- USDT amount: `y = V/2`

### Delta Calculation

The pool's ETH exposure is locally equivalent to holding `V/(2P)` ETH.

**Delta (in ETH units) = +V/(2P)**

### Hedge Requirement

To achieve local delta-neutrality:
**Short ETH on CEX = V/(2P)**

---

## Uniswap V3 Concentrated Liquidity Delta Derivation

### Setup

- **P₀**: Current ETH price at entry
- **P_low**: Lower bound = P₀ × (1 - 0.10) = 0.90P₀
- **P_high**: Upper bound = P₀ × (1 + 0.10) = 1.10P₀
- **L**: Liquidity amount
- **V**: Total USD value of position

### V3 Position Token Amounts

At entry with P₀ inside the range [P_low, P_high]:

**ETH Amount:**

```
ΔETH = L × (1/√P₀ - 1/√P_high)
```

**USDT Amount:**

```
ΔUSDT = L × (√P₀ - √P_low)
```

### Delta Calculation

The local delta (ETH units) is the derivative of the ETH amount with respect to price:

**Delta (in ETH units) = L × (-1/(2P₀^(3/2)))**

### Hedge Requirement

**Short ETH on CEX = L × (1/(2P₀^(3/2)))**

---

## Key Assumptions

1. **Local Delta Neutrality**: Hedging is valid only for small price movements
2. **No Rebalancing**: Position is static after initial hedge
3. **Perfect Liquidity**: No slippage in CEX hedge execution
4. **Price Continuity**: Smooth price movements without jumps
5. **No Funding Costs**: CEX perp funding rates are zero

---

## Boxed Final Formulas

### V2 50/50 Pool

```
Hedge Size = V/(2P)
```

### V3 ±10% Range

```
Hedge Size = L × (1/(2P₀^(3/2)))
```

Where:

- **V**: Total USD position size
- **P**: ETH price in USDT
- **L**: V3 liquidity amount
- **P₀**: Entry price



