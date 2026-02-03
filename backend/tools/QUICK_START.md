# Tool Server Quick Start

## 1-Minute Setup

### Prerequisites
```bash
# Already in requirements.txt:
duckduckgo-search>=2.6.0
fastapi>=0.104.1
sqlalchemy>=2.0.20
```

### Start the API

```bash
cd /home/devlord/RobotCEM
source dw_env/bin/activate

# Run FastAPI with tool server included
python -m uvicorn backend.api.main:app --reload --port 8000
```

### Test Endpoints

```bash
# Check tool server is running
curl http://localhost:8000/tools/health

# Get available tools
curl http://localhost:8000/tools/schema

# Lookup product price
curl -X POST http://localhost:8000/tools/product_price_lookup \
  -H "Content-Type: application/json" \
  -d '{"product_name":"RTX 4070"}'

# Lookup material price
curl -X POST http://localhost:8000/tools/material_price_lookup \
  -H "Content-Type: application/json" \
  -d '{"material_name":"Titanium Ti-6Al-4V","unit":"kg"}'
```

### Run Examples

```bash
cd /home/devlord/RobotCEM
python -m backend.examples.tool_usage_examples
```

## Tool Server URLs

### Base URL
```
http://localhost:8000/tools/
```

### Pricing Tools
- `POST /tools/product_price_lookup` - Consumer products
- `POST /tools/material_price_lookup` - Raw materials
- `POST /tools/density_lookup` - Material density
- `POST /tools/material_cost_calculator` - Calculate material cost
- `POST /tools/manufacturing_cost_estimator` - Manufacturing cost
- `POST /tools/currency_convert` - Currency conversion

### Discovery & Management
- `GET /tools/` - Tool list
- `GET /tools/schema` - LLM schema
- `GET /tools/tools` - All tools info
- `GET /tools/tools/{name}` - Specific tool
- `GET /tools/health` - Health check
- `GET /tools/cache/stats` - Cache statistics
- `POST /tools/cache/clear-expired` - Clear expired cache
- `DELETE /tools/cache/{key}` - Delete cache entry

## Example API Calls

### Get RTX 4070 Price

```bash
curl -X POST http://localhost:8000/tools/product_price_lookup \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "RTX 4070",
    "quantity": 1,
    "region": "US"
  }'
```

Response:
```json
{
  "status": "success",
  "product": "RTX 4070",
  "average": 609.99,
  "min": 599.99,
  "max": 619.99,
  "confidence": 0.95
}
```

### Get Titanium Price

```bash
curl -X POST http://localhost:8000/tools/material_price_lookup \
  -H "Content-Type: application/json" \
  -d '{
    "material_name": "Titanium Ti-6Al-4V",
    "unit": "kg"
  }'
```

### Calculate Cost for 87g

```bash
curl -X POST http://localhost:8000/tools/material_cost_calculator \
  -H "Content-Type: application/json" \
  -d '{
    "material_name": "Titanium Ti-6Al-4V",
    "quantity": 87,
    "unit": "g",
    "price_per_unit": 350
  }'
```

### Estimate SLM 3D Printing Cost

```bash
curl -X POST http://localhost:8000/tools/manufacturing_cost_estimator \
  -H "Content-Type: application/json" \
  -d '{
    "manufacturing_method": "SLM",
    "material": "Stainless Steel 304",
    "weight_g": 120,
    "complexity": "moderate",
    "post_processing": "polishing"
  }'
```

### Check Cache Stats

```bash
curl http://localhost:8000/tools/cache/stats
```

## Using Tools from Python

### Simple Usage

```python
from backend.tools.price_tools import MaterialPriceTool
from backend.tools.database_cache import get_cache_store

cache_store = get_cache_store()
tool = MaterialPriceTool(cache_store)

result = await tool.execute(material_name="Titanium Ti-6Al-4V")
print(result['average_price'])  # $350/kg
```

### Complete Workflow

```python
import asyncio
from backend.tools.price_tools import (
    MaterialPriceTool,
    MaterialCostCalculatorTool,
    ManufacturingCostEstimatorTool
)
from backend.tools.database_cache import get_cache_store

async def calculate_part_cost():
    cache = get_cache_store()
    
    # Step 1: Get material price
    material_tool = MaterialPriceTool(cache)
    mat_result = await material_tool.execute(
        material_name="Stainless Steel 304",
        unit="kg"
    )
    price_per_kg = mat_result['average_price']
    
    # Step 2: Calculate raw material cost
    cost_tool = MaterialCostCalculatorTool(cache)
    cost_result = await cost_tool.execute(
        material_name="Stainless Steel 304",
        quantity=120,
        unit="g",
        price_per_unit=price_per_kg
    )
    raw_material = cost_result['total_cost']
    
    # Step 3: Get manufacturing cost
    mfg_tool = ManufacturingCostEstimatorTool(cache)
    mfg_result = await mfg_tool.execute(
        manufacturing_method="SLM",
        material="Stainless Steel 304",
        weight_g=120,
        complexity="moderate"
    )
    manufacturing = mfg_result['total_cost']
    
    # Total
    total = raw_material + manufacturing
    
    print(f"Raw Material: ${raw_material:.2f}")
    print(f"Manufacturing: ${manufacturing:.2f}")
    print(f"TOTAL: ${total:.2f}")

asyncio.run(calculate_part_cost())
```

## Integration with RobotCEM Design Pipeline

### In CEM Engine

```python
from backend.tools.price_tools import MaterialPriceTool, ManufacturingCostEstimatorTool
from backend.tools.database_cache import get_cache_store

class CEMEngineWithTools:
    def __init__(self):
        self.cache = get_cache_store()
        self.material_tool = MaterialPriceTool(self.cache)
        self.mfg_tool = ManufacturingCostEstimatorTool(self.cache)
    
    async def estimate_design_cost(self, material, weight_g, method):
        """Get accurate cost for proposed design."""
        
        # Material cost
        mat_result = await self.material_tool.execute(material_name=material)
        if mat_result['status'] != 'success':
            return None
        
        # Manufacturing cost
        mfg_result = await self.mfg_tool.execute(
            manufacturing_method=method,
            material=material,
            weight_g=weight_g
        )
        
        return {
            'material_cost': mat_result['average_price'] * (weight_g / 1000),
            'manufacturing_cost': mfg_result['total_cost'],
            'sources': mat_result['sources'],
            'confidence': min(mat_result['confidence'], 0.8)
        }
```

### In Design Specification

```python
class DesignSpecification:
    def __init__(self, materials, manufacturing_method):
        self.materials = materials
        self.method = manufacturing_method
        self.tools = CEMEngineWithTools()
    
    async def calculate_bom_cost(self, components):
        """Calculate BOM cost using live prices."""
        
        total_cost = 0
        details = []
        
        for component in components:
            cost_data = await self.tools.estimate_design_cost(
                material=component['material'],
                weight_g=component['weight_g'],
                method=self.method
            )
            
            if cost_data:
                details.append({
                    'component': component['name'],
                    'cost': cost_data['material_cost'] + cost_data['manufacturing_cost']
                })
                total_cost += cost_data['material_cost'] + cost_data['manufacturing_cost']
        
        return {
            'total': total_cost,
            'details': details,
            'currency': 'USD'
        }
```

## Monitoring & Debugging

### View Cache Stats

```bash
curl http://localhost:8000/tools/cache/stats | jq
```

### Clear Expired Cache

```bash
curl -X POST http://localhost:8000/tools/cache/clear-expired
```

### View Tool Definitions

```bash
curl http://localhost:8000/tools/schema | jq
curl http://localhost:8000/tools/tools | jq
```

### Check Specific Tool

```bash
curl http://localhost:8000/tools/tools/material_price_lookup | jq
```

## Performance Tips

### 1. Enable Caching

Cache is automatic, but monitor:

```bash
curl http://localhost:8000/tools/cache/stats | grep total_hits
```

Higher hit rate = better performance.

### 2. Use Appropriate TTL

```python
# Prices change often - 1 hour
await cache_store.set(key, value, ttl=3600)

# Density never changes - 7 days
await cache_store.set(key, value, ttl=604800)
```

### 3. Batch Queries

```python
# Instead of sequential calls
for material in materials:
    result = await tool.execute(material_name=material)  # 1-3s each

# Use asyncio.gather for parallel
results = await asyncio.gather(
    tool.execute(material_name=materials[0]),
    tool.execute(material_name=materials[1]),
    tool.execute(material_name=materials[2]),
)  # ~1-3s total
```

### 4. Optional Redis for High Load

```python
# In config
REDIS_URL="redis://localhost:6379"

# Then CacheStore automatically uses Redis as primary
cache = get_cache_store()  # Uses Redis if available, falls back to SQLite
```

## Common Issues

### "Tool not found" Error

Check tool name:
```bash
curl http://localhost:8000/tools/schema | jq '.functions[].function.name'
```

### Searches failing silently

- DuckDuckGo might be rate limiting (rare)
- Check logs for error details
- Increase retry delays in `price_search.py`

### Cache growing too large

```bash
curl -X POST http://localhost:8000/tools/cache/clear-expired
```

Clears entries older than their TTL.

### Prices seem wrong

- Verify query is specific (e.g., "Titanium Ti-6Al-4V" not just "Titanium")
- Check `confidence` score
- Look at `sources` list
- May need to contact supplier directly for bulk quotes

## Next Steps

1. **Deploy to production** - System is ready
2. **Monitor metrics** - Check `/tools/cache/stats` regularly
3. **Add supplier APIs** - Integrate Digikey, McMaster-Carr directly
4. **Build UI** - Frontend for manual price lookups
5. **Integrate with design pipeline** - Use in CEM for real-time costing

---

**Questions?** See `TOOL_SERVER_DOCUMENTATION.md` or `IMPLEMENTATION_GUIDE.md`.
