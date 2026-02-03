"""
Tool Server Module - Augments LLM with real-time pricing and cost calculation tools.

This module provides a set of specialized tools for:
- Product price lookup
- Material pricing
- Manufacturing cost estimation
- Currency conversion
- Tool caching and data persistence
"""

try:
    from .tool_registry import ToolRegistry, ToolDefinition, ToolParameter
    from .price_tools import (
        ProductPriceTool,
        MaterialPriceTool,
        ManufacturingCostEstimatorTool,
        CurrencyConversionTool,
        DensityLookupTool,
        MaterialCostCalculatorTool,
    )
    from .price_search import PriceExtractor, WebSearchEngine
    from .database_cache import CacheStore, get_cache_store
    from .llm_integration import SYSTEM_PROMPT, QueryClassifier, ToolChain
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import all tool modules: {e}", ImportWarning)

__all__ = [
    "ToolRegistry",
    "ToolDefinition",
    "ToolParameter",
    "ProductPriceTool",
    "MaterialPriceTool",
    "DensityLookupTool",
    "MaterialCostCalculatorTool",
    "ManufacturingCostEstimatorTool",
    "CurrencyConversionTool",
    "PriceExtractor",
    "WebSearchEngine",
    "CacheStore",
    "get_cache_store",
    "SYSTEM_PROMPT",
    "QueryClassifier",
    "ToolChain",
]
__all__ = [
    'ToolRegistry',
    'ProductPriceTool',
    'MaterialPriceTool',
    'ManufacturingCostTool',
    'CurrencyConversionTool',
    'DensityLookupTool'
]
