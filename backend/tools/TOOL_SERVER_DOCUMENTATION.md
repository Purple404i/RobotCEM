# Tool-Augmented LLM Pricing System Documentation

## Overview

This system implements a sophisticated pricing and cost calculation backend that augments an LLM with real-time data retrieval capabilities. The LLM never guesses prices—it always uses tools to fetch current market data.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM (Claude, GPT-4, etc.)                │
│  - Receives system prompt enforcing tool usage              │
│  - Classifies user queries                                  │
│  - Chains tool calls in correct order                       │
│  - Formats results for humans                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Tool Calling Protocol
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Tool Server                       │
│                     /tools/[endpoint]                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  pricing_tools.py - Tool Implementations             │   │
│  │  • ProductPriceTool                                  │   │
│  │  • MaterialPriceTool                                 │   │
│  │  • DensityLookupTool                                 │   │
│  │  • MaterialCostCalculatorTool                        │   │
│  │  • ManufacturingCostEstimatorTool                    │   │
│  │  • CurrencyConversionTool                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  price_search.py - Data Retrieval                    │   │
│  │  • WebSearchEngine (DuckDuckGo)                      │   │
│  │  • PriceExtractor (regex parsing)                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
    ┌──────────────────┐         ┌──────────────────┐
    │  Cache Layer     │         │  External APIs   │
    │  (SQLAlchemy)    │         │  • DuckDuckGo    │
    │  • Redis (opt)   │         │  • Exchange Rates│
    │  • SQLite        │         │  • Suppliers     │
    └──────────────────┘         └──────────────────┘
```

## Tool Server Endpoints

### Price Lookup Tools

#### `POST /tools/product_price_lookup`
Look up consumer product prices.

**Request:**
```json
{
  "product_name": "RTX 4070",
  "quantity": 1,
  "region": "US"
}
```

**Response:**
```json
{
  "status": "success",
  "product": "RTX 4070",
  "prices": [599.99, 609.99, 619.99],
  "average": 609.99,
  "min": 599.99,
  "max": 619.99,
  "currency": "USD",
  "sources": [
    {"title": "Newegg", "url": "https://...", "snippet": "..."},
    {"title": "Amazon", "url": "https://...", "snippet": "..."}
  ],
  "confidence": 0.95,
  "timestamp": "2024-02-03T10:30:00"
}
```

#### `POST /tools/material_price_lookup`
Look up raw material prices.

**Request:**
```json
{
  "material_name": "Titanium Ti-6Al-4V",
  "unit": "kg",
  "purity_grade": null
}
```

**Response:**
```json
{
  "status": "success",
  "material": "Titanium Ti-6Al-4V",
  "unit": "kg",
  "prices": [320, 350, 380],
  "average_price": 350,
  "min_price": 320,
  "max_price": 380,
  "currency": "USD",
  "sources": [
    {"title": "Supplier A", "url": "...", "snippet": "..."}
  ],
  "confidence": 0.85,
  "timestamp": "2024-02-03T10:30:00"
}
```

### Calculation Tools

#### `POST /tools/density_lookup`
Look up material density for volume-to-mass conversion.

**Request:**
```json
{
  "material_name": "Aluminum 6061",
  "unit": "g/cm3"
}
```

**Response:**
```json
{
  "status": "success",
  "material": "Aluminum 6061",
  "density": 2.70,
  "unit": "g/cm3",
  "base_density": 2.70,
  "base_unit": "g/cm3",
  "confidence": "high"
}
```

#### `POST /tools/material_cost_calculator`
Calculate material cost from price and weight.

**Request:**
```json
{
  "material_name": "Titanium Ti-6Al-4V",
  "quantity": 87,
  "unit": "g",
  "price_per_unit": 350,
  "unit_price": "USD"
}
```

**Response:**
```json
{
  "status": "success",
  "material": "Titanium Ti-6Al-4V",
  "input": {
    "quantity": 87,
    "unit": "g"
  },
  "normalized": {
    "quantity_kg": 0.087,
    "price_per_kg": 350
  },
  "calculation": "0.0870 kg × $350/kg = $30.45",
  "total_cost": 30.45,
  "currency": "USD",
  "timestamp": "2024-02-03T10:30:00"
}
```

#### `POST /tools/manufacturing_cost_estimator`
Estimate manufacturing cost by method.

**Request:**
```json
{
  "manufacturing_method": "SLM",
  "material": "Stainless Steel 304",
  "weight_g": 120,
  "volume_cm3": null,
  "complexity": "moderate",
  "post_processing": "polishing"
}
```

**Response:**
```json
{
  "status": "success",
  "method": "SLM",
  "material": "Stainless Steel 304",
  "weight_g": 120,
  "complexity": "moderate",
  "costs": {
    "base_cost_per_g": 1.2,
    "complexity_multiplier": 1.5,
    "setup_cost": 75,
    "manufacturing_cost": 291.0,
    "post_processing_cost": 30.0
  },
  "calculation": {
    "manufacturing": "(1.2$/g × 120g × 1.5) + $75 = $291.00",
    "post_processing": "polishing: $30.00",
    "total": "$321.00"
  },
  "total_cost": 321.0,
  "currency": "USD",
  "confidence": "medium",
  "note": "Raw material cost not included. Call material_cost_calculator for accurate total.",
  "timestamp": "2024-02-03T10:30:00"
}
```

#### `POST /tools/currency_convert`
Convert between currencies.

**Request:**
```json
{
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "EUR"
}
```

**Response:**
```json
{
  "status": "success",
  "from_amount": 100,
  "from_currency": "USD",
  "to_amount": 92.0,
  "to_currency": "EUR",
  "exchange_rate": 0.92,
  "calculation": "100 USD × 0.9200 = 92.00 EUR",
  "timestamp": "2024-02-03T10:30:00"
}
```

### Discovery Endpoints

#### `GET /tools/`
Get list of available tools.

#### `GET /tools/schema`
Get LLM-compatible JSON schema for all tools.

#### `GET /tools/tools`
Get detailed information about all tools.

#### `GET /tools/tools/{tool_name}`
Get details about specific tool.

#### `GET /tools/tools/category/{category}`
Get all tools in a category (pricing, calculation, conversion).

### Cache Management

#### `GET /tools/cache/stats`
Get cache statistics and hit rates.

#### `POST /tools/cache/clear-expired`
Clear expired cache entries.

#### `DELETE /tools/cache/{key}`
Delete specific cache entry.

## LLM Integration

### System Prompt
The LLM receives a detailed system prompt that:
1. **Forbids price assumptions** - Must use tools
2. **Enforces tool chaining** - For complex queries
3. **Requires source attribution** - Show where data came from
4. **Explicitly states assumptions** - What's included/excluded

### Example LLM Query Flow

**User Query:** "How much would 87g of Ti-6Al-4V cost?"

**LLM Reasoning:**
```
1. Classify: This is a material cost query
2. Required tools: material_price_lookup → material_cost_calculator
3. Tool sequence:
   Step 1: material_price_lookup(material_name="Titanium Ti-6Al-4V", unit="kg")
   Step 2: material_cost_calculator(material_name="Titanium Ti-6Al-4V", quantity=87, unit="g", price_per_unit=<from step 1>)
```

**Tool Execution:**
```
Tool 1 Result: average_price = $350/kg, confidence = 0.85
Tool 2 Result: total_cost = $30.45, calculation = "0.087kg × $350/kg = $30.45"
```

**LLM Response:**
```
87g of Ti-6Al-4V costs approximately $30.45 at current market prices (as of Feb 3, 2024).

CALCULATION BREAKDOWN
════════════════════
Weight: 87g = 0.087 kg
Material Price: $350/kg (from 3 supplier sources)
Calculation: 0.087 kg × $350/kg = $30.45

SOURCING & CONFIDENCE
═════════════════════
Sources: [Supplier 1, Supplier 2, Supplier 3]
Confidence: HIGH (from multiple sources)
Last Updated: Feb 3, 2024

NOTES
═════
• This is raw material cost only
• Bulk discounts may apply for larger quantities
• Prices may vary by supplier and form (powder vs ingot)
```

## Cost Estimation Models

### Manufacturing Methods & Base Costs

| Method | Base Cost/g | Setup Cost | Best For |
|--------|------------|-----------|----------|
| FDM | $0.05 | $10 | Plastic prototypes |
| SLA | $0.08 | $15 | Resin details |
| DMLS | $0.80 | $50 | Metal functional parts |
| SLM | $1.20 | $75 | High-precision metals |
| CNC | $0.40 | $30 | Metal/plastic production |
| Machining | $0.35 | $25 | High-tolerance metal |
| Casting | $0.15 | $100 | Large metal parts |
| Forging | $0.25 | $150 | High-strength metal |
| Sheet Metal | $0.20 | $40 | Enclosures, brackets |

### Complexity Multipliers

- Simple: 1.0×
- Moderate: 1.5×
- Complex: 2.5×

### Typical Material Densities (g/cm³)

| Material | Density |
|----------|---------|
| Aluminum 6061 | 2.70 |
| Steel 1045 | 7.85 |
| Titanium Ti-6Al-4V | 4.43 |
| Stainless 304 | 8.00 |
| PLA Plastic | 1.24 |
| Carbon Fiber | 1.60 |

## Database Caching Strategy

### Cache Key Format
```
product:{product_name}:{quantity}
material:{material_name}:{unit}
density:{material_name}
mfg:{material}:{method}:{weight_g}
```

### TTL (Time To Live)

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Product Prices | 1 hour | Change frequently |
| Material Prices | 2 hours | Change periodically |
| Density Data | 7 days | Stable |
| Manufacturing Costs | 1 day | May update with capacity |
| Exchange Rates | 6 hours | Update throughout day |

### Cache Hit Statistics

Cached responses include metadata:
```json
{
  "_cache_metadata": {
    "cached_at": "2024-02-03T08:00:00",
    "hits": 5,
    "source": "cache",
    "confidence": "high"
  }
}
```

## Integration with RobotCEM

### Replacing Rate-Limited APIs

The system replaces these external dependencies:

| Old API | Replacement |
|---------|------------|
| Alpha Vantage (500 req/day) | DuckDuckGo (unlimited) |
| Firecrawl (500 credits) | price_search.WebSearchEngine |
| Finnhub (rate limited) | Direct search via DuckDuckGo |
| iTick API (rate limited) | material_price_lookup tool |

### Using in Design Generation

When the LLM generates designs, it now:

```python
# Before: Assumes material prices (wrong!)
material_cost = 87 * 5.0  # Random guess

# After: Uses tools
material_price_response = await material_price_tool.execute(
    material_name="Titanium Ti-6Al-4V"
)
actual_price = material_price_response['average_price']
material_cost = 0.087 * actual_price
```

## Best Practices

### 1. Always Chain Tools for Complex Queries
```python
# Query: "What's the cost to 3D print 150g aluminum?"
# Required chain:
# 1. density_lookup('Aluminum 6061') → density
# 2. material_price_lookup('Aluminum 6061') → price
# 3. manufacturing_cost_estimator('SLM', 'Aluminum 6061', 150g)
# 4. material_cost_calculator(150g, $price/kg)
```

### 2. Handle "not_found" Gracefully
```json
{
  "status": "not_found",
  "material": "Exotic Alloy XYZ",
  "message": "Could not find pricing. Try these alternatives: Inconel 718, Waspaloy"
}
```

### 3. Always Show Confidence
Low confidence (< 0.7) data should be flagged:
```
Estimated at $X.XX (LOW CONFIDENCE - based on limited sources)
```

### 4. Explicit Exclusions
Always state what's NOT included:
- "This cost excludes: taxes, shipping, post-processing, quality assurance"

### 5. Cache Warmup
Pre-populate common materials at startup:
```python
common_materials = ['Aluminum 6061', 'Steel 1045', 'Titanium Ti-6Al-4V', 'Stainless 304']
for material in common_materials:
    await material_price_tool.execute(material_name=material)
```

## Performance Considerations

### Request Latency

- **Cached responses**: < 10ms
- **First search**: 500-2000ms (includes web search)
- **Multi-tool chains**: < 5 seconds total

### Optimization Tips

1. **Cache aggressively** - Most price queries are duplicates
2. **Batch requests** - Process multiple tools in parallel
3. **Search fewer results** - 3-5 sources usually sufficient
4. **Use fallback data** - Keep manual material database as backup

## Future Enhancements

1. **Scylla DB Integration** - Replace SQLite for distributed caching
2. **Real-time supplier APIs** - Direct integration with McMaster-Carr, Digikey
3. **Machine learning pricing** - Predict price ranges before searching
4. **Historical data** - Track price trends over time
5. **Bulk discounts** - Automatic volume discount calculation
6. **Lead time optimization** - Factor manufacturing timeline into recommendations

## Troubleshooting

### "no_data" Status
- Tool ran but found no search results
- Try alternative material names (e.g., "Ti-6Al-4V" vs "Ti-6-2-4-2")
- Check if material is specialized (not in popular search results)

### Low Confidence Score
- Limited number of sources found
- Conflicting prices across suppliers
- Material is niche/specialty
- Recommend manual supplier contact

### Cache Misses
- Tool response too large for cache
- Cache entry expired (check TTL)
- Malformed cache key
- Check `/tools/cache/stats` endpoint

## Testing the System

### Manual Testing
```bash
# Test product pricing
curl -X POST "http://localhost:8000/tools/product_price_lookup" \
  -H "Content-Type: application/json" \
  -d '{"product_name":"RTX 4070"}'

# Test material pricing
curl -X POST "http://localhost:8000/tools/material_price_lookup" \
  -H "Content-Type: application/json" \
  -d '{"material_name":"Titanium Ti-6Al-4V","unit":"kg"}'

# Test tool discovery
curl "http://localhost:8000/tools/schema"
```

### Automated Testing
```python
# In tests/test_tools.py
async def test_product_price_lookup():
    result = await product_price_tool.execute(product_name="RTX 4070")
    assert result['status'] == 'success'
    assert result['average'] > 0
    assert result['confidence'] > 0.5
```
