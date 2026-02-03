"""
FastAPI Tool Server Endpoints

RESTful API for all pricing and calculation tools.
Provides both individual endpoint access and integrated tool discovery.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from .price_tools import (
    ProductPriceTool,
    MaterialPriceTool,
    DensityLookupTool,
    MaterialCostCalculatorTool,
    ManufacturingCostEstimatorTool,
    CurrencyConversionTool
)
from .tool_registry import get_tool_registry
from .database_cache import get_cache_store

logger = logging.getLogger(__name__)

# Initialize tools and cache
cache_store = get_cache_store()
registry = get_tool_registry()

product_price_tool = ProductPriceTool(cache_store)
material_price_tool = MaterialPriceTool(cache_store)
density_tool = DensityLookupTool(cache_store)
material_cost_tool = MaterialCostCalculatorTool(cache_store)
manufacturing_cost_tool = ManufacturingCostEstimatorTool(cache_store)
currency_tool = CurrencyConversionTool(cache_store)

router = APIRouter(prefix="/tools", tags=["pricing_tools"])


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class ProductPriceLookupRequest(BaseModel):
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(1, description="Quantity")
    region: str = Field("US", description="Geographic region")


class MaterialPriceLookupRequest(BaseModel):
    material_name: str = Field(..., description="Material specification")
    unit: str = Field("kg", description="Unit of measurement")
    purity_grade: Optional[str] = Field(None, description="Material grade")


class DensityLookupRequest(BaseModel):
    material_name: str = Field(..., description="Material name")
    unit: str = Field("g/cm3", description="Output unit")


class MaterialCostCalculatorRequest(BaseModel):
    material_name: str = Field(..., description="Material name")
    quantity: float = Field(..., description="Amount")
    unit: str = Field(..., description="Unit")
    price_per_unit: float = Field(..., description="Price per unit")
    unit_price: str = Field("USD", description="Currency")


class ManufacturingCostEstimatorRequest(BaseModel):
    manufacturing_method: str = Field(..., description="Manufacturing method")
    material: str = Field(..., description="Material")
    weight_g: float = Field(..., description="Weight in grams")
    volume_cm3: Optional[float] = Field(None, description="Volume")
    complexity: str = Field("moderate", description="Complexity")
    post_processing: Optional[str] = Field(None, description="Post-processing")


class CurrencyConversionRequest(BaseModel):
    amount: float = Field(..., description="Amount to convert")
    from_currency: str = Field(..., description="Source currency")
    to_currency: str = Field(..., description="Target currency")


# ============================================================================
# Tool Endpoints
# ============================================================================

@router.post("/product_price_lookup")
async def product_price_lookup(request: ProductPriceLookupRequest):
    """
    Look up consumer product prices.
    
    Examples:
    - RTX 4070
    - iPhone 15 Pro Max
    - Samsung Galaxy S24
    """
    try:
        result = await product_price_tool.execute(
            product_name=request.product_name,
            quantity=request.quantity,
            region=request.region
        )
        return result
    
    except Exception as e:
        logger.error(f"Product price lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/material_price_lookup")
async def material_price_lookup(request: MaterialPriceLookupRequest):
    """
    Look up raw material prices.
    
    Examples:
    - Titanium Ti-6Al-4V
    - 6061 Aluminum
    - Stainless Steel 304
    """
    try:
        result = await material_price_tool.execute(
            material_name=request.material_name,
            unit=request.unit,
            purity_grade=request.purity_grade
        )
        return result
    
    except Exception as e:
        logger.error(f"Material price lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/density_lookup")
async def density_lookup(request: DensityLookupRequest):
    """
    Look up material density for volume-to-mass conversion.
    
    Examples:
    - Aluminum 6061
    - Titanium Ti-6Al-4V
    - PLA plastic
    """
    try:
        result = await density_tool.execute(
            material_name=request.material_name,
            unit=request.unit
        )
        return result
    
    except Exception as e:
        logger.error(f"Density lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/material_cost_calculator")
async def material_cost_calculator(request: MaterialCostCalculatorRequest):
    """
    Calculate material cost from price and weight.
    
    Typically called after material_price_lookup.
    """
    try:
        result = await material_cost_tool.execute(
            material_name=request.material_name,
            quantity=request.quantity,
            unit=request.unit,
            price_per_unit=request.price_per_unit,
            unit_price=request.unit_price
        )
        return result
    
    except Exception as e:
        logger.error(f"Material cost calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manufacturing_cost_estimator")
async def manufacturing_cost_estimator(request: ManufacturingCostEstimatorRequest):
    """
    Estimate manufacturing costs based on method and part properties.
    
    Supported methods:
    - FDM (Fused Deposition Modeling)
    - SLA (Stereolithography)
    - DMLS (Direct Metal Laser Sintering)
    - SLM (Selective Laser Melting)
    - CNC (Computer Numerical Control)
    - Machining
    - Casting
    - Forging
    - Sheet_Metal
    """
    try:
        result = await manufacturing_cost_tool.execute(
            manufacturing_method=request.manufacturing_method,
            material=request.material,
            weight_g=request.weight_g,
            volume_cm3=request.volume_cm3,
            complexity=request.complexity,
            post_processing=request.post_processing
        )
        return result
    
    except Exception as e:
        logger.error(f"Manufacturing cost estimation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/currency_convert")
async def currency_convert(request: CurrencyConversionRequest):
    """
    Convert between currencies using live exchange rates.
    
    Supported currencies: USD, EUR, GBP, JPY, CNY, INR, CAD, AUD, CHF, SGD, HKD, NZD, MXN, BRL
    """
    try:
        result = await currency_tool.execute(
            amount=request.amount,
            from_currency=request.from_currency,
            to_currency=request.to_currency
        )
        return result
    
    except Exception as e:
        logger.error(f"Currency conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Tool Discovery and Management Endpoints
# ============================================================================

@router.get("/")
async def tools_root():
    """Get list of available tools."""
    return {
        "message": "Tool Server - Real-time Pricing & Cost Calculation",
        "version": "1.0.0",
        "tools": list(registry.get_all_tools().keys()),
        "documentation": "/tools/schema"
    }


@router.get("/schema")
async def tools_schema():
    """Get LLM-compatible JSON schema for all tools."""
    return {
        "type": "function",
        "functions": registry.to_json_schema()
    }


@router.get("/tools")
async def list_tools():
    """Get detailed information about all available tools."""
    return registry.to_dict()


@router.get("/tools/{tool_name}")
async def get_tool_details(tool_name: str):
    """Get details about a specific tool."""
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    return {
        'name': tool.name,
        'description': tool.description,
        'category': tool.category,
        'parameters': [
            {
                'name': p.name,
                'type': p.type,
                'description': p.description,
                'required': p.required,
                'enum': p.enum,
                'default': p.default
            }
            for p in tool.parameters
        ],
        'returns': tool.returns,
        'examples': tool.examples
    }


@router.get("/tools/category/{category}")
async def get_tools_by_category(category: str):
    """Get all tools in a specific category."""
    tools = registry.get_tools_by_category(category)
    if not tools:
        raise HTTPException(status_code=404, detail=f"No tools found in category: {category}")
    
    return {
        'category': category,
        'tools': [t.name for t in tools],
        'count': len(tools)
    }


# ============================================================================
# Cache Management Endpoints
# ============================================================================

@router.get("/cache/stats")
async def cache_statistics():
    """Get cache statistics."""
    try:
        if hasattr(cache_store.primary, 'get_cache_stats'):
            stats = await cache_store.primary.get_cache_stats()
        else:
            stats = {'message': 'Cache stats not available for this backend'}
        
        return {
            'status': 'success',
            'stats': stats
        }
    
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear-expired")
async def clear_expired_cache(background_tasks: BackgroundTasks):
    """Clear expired cache entries."""
    try:
        count = await cache_store.clear_expired()
        return {
            'status': 'success',
            'entries_cleared': count
        }
    
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/{key}")
async def delete_cache_entry(key: str):
    """Delete a specific cache entry."""
    try:
        success = await cache_store.delete(key)
        return {
            'status': 'success' if success else 'not_found',
            'key': key
        }
    
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'tools': len(registry.get_all_tools()),
        'message': 'Tool Server operational'
    }
