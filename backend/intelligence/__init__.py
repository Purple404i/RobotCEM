"""
Intelligence Module - Market search, pricing, and intelligent caching

Includes:
- Market search engine integration
- Material pricing intelligence
- Supplier discovery
- Price analysis and trends
"""

try:
    from .market_search import MarketSearchEngine
    from .material_pricing import MaterialPricingEngine
    from .cache import Cache
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import intelligence modules: {e}", ImportWarning)

__all__ = [
    "MarketSearchEngine",
    "MaterialPricingEngine",
    "Cache",
]
