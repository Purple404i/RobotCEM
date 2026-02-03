"""
Price Extraction and Search Utilities

Handles web search via DuckDuckGo, price extraction with regex,
and result parsing for various product and material categories.
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from decimal import Decimal
import asyncio
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class PriceExtractor:
    """Extracts prices from text using advanced regex patterns."""
    
    # Regex patterns for various price formats
    PRICE_PATTERNS = {
        'standard_usd': r'\$\s*([0-9,]+\.?[0-9]*)\s*(?:USD)?',
        'standard_eur': r'€\s*([0-9,]+\.?[0-9]*)\s*(?:EUR)?',
        'standard_gbp': r'£\s*([0-9,]+\.?[0-9]*)\s*(?:GBP)?',
        'currency_code': r'([0-9,]+\.?[0-9]*)\s*(?:USD|EUR|GBP|JPY|CNY|INR)',
        'price_per_unit': r'([0-9,]+\.?[0-9]*)\s*(?:per|/)\s*(?:kg|lb|oz|m³|unit|piece)',
        'range': r'\$\s*([0-9,]+\.?[0-9]*)\s*-\s*\$?([0-9,]+\.?[0-9]*)',
    }
    
    @staticmethod
    def clean_number(value: str) -> float:
        """Convert currency string to float."""
        return float(value.replace(',', '').strip())
    
    @staticmethod
    def extract_prices(text: str) -> List[Dict[str, any]]:
        """Extract all prices from text with context."""
        prices = []
        
        for pattern_name, pattern in PriceExtractor.PRICE_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if pattern_name == 'range':
                        min_price = PriceExtractor.clean_number(match.group(1))
                        max_price = PriceExtractor.clean_number(match.group(2))
                        prices.append({
                            'type': 'range',
                            'min': min_price,
                            'max': max_price,
                            'text': match.group(0),
                            'position': match.start()
                        })
                    else:
                        price = PriceExtractor.clean_number(match.group(1))
                        prices.append({
                            'type': pattern_name,
                            'value': price,
                            'text': match.group(0),
                            'position': match.start()
                        })
                except ValueError:
                    continue
        
        # Sort by position and deduplicate
        prices.sort(key=lambda x: x['position'])
        return prices
    
    @staticmethod
    def extract_best_price(text: str) -> Optional[float]:
        """Extract most likely price from text (assumes first valid price)."""
        prices = PriceExtractor.extract_prices(text)
        if prices:
            if prices[0]['type'] == 'range':
                return prices[0]['min']  # Return lower bound
            return prices[0].get('value')
        return None


class WebSearchEngine:
    """DuckDuckGo-based web search for product and material pricing."""
    
    def __init__(self, cache_store=None):
        self.cache_store = cache_store
        self.price_extractor = PriceExtractor()
    
    async def search_product_price(
        self,
        product_name: str,
        quantity: int = 1,
        max_results: int = 5
    ) -> Dict:
        """
        Search for product pricing via DuckDuckGo.
        
        Args:
            product_name: Product to search for
            quantity: Quantity for pricing (some prices are quantity-dependent)
            max_results: Max search results to parse
        
        Returns:
            Dict with price, sources, confidence score
        """
        cache_key = f"product:{product_name}:{quantity}"
        
        # Check cache
        if self.cache_store:
            cached = await self.cache_store.get(cache_key)
            if cached:
                return cached
        
        try:
            # Build search query
            search_query = f"{product_name} price buy online"
            
            # Perform search (using DDGS)
            results = await asyncio.to_thread(
                lambda: list(DDGS().text(search_query, max_results=max_results))
            )
            
            if not results:
                return {
                    'status': 'not_found',
                    'product': product_name,
                    'quantity': quantity,
                    'message': 'No search results found'
                }
            
            # Extract prices from results
            prices = []
            sources = []
            
            for result in results:
                body = result.get('body', '')
                title = result.get('title', '')
                href = result.get('href', '')
                
                extracted_prices = self.price_extractor.extract_prices(body)
                if extracted_prices:
                    prices.extend(extracted_prices)
                    sources.append({
                        'title': title,
                        'url': href,
                        'snippet': body[:200]
                    })
            
            # Calculate statistics
            if prices:
                numeric_prices = [p['value'] if p['type'] != 'range' else p['min'] 
                                for p in prices if 'value' in p or 'min' in p]
                
                if numeric_prices:
                    response = {
                        'status': 'success',
                        'product': product_name,
                        'quantity': quantity,
                        'prices': numeric_prices,
                        'average': sum(numeric_prices) / len(numeric_prices),
                        'min': min(numeric_prices),
                        'max': max(numeric_prices),
                        'currency': 'USD',  # DuckDuckGo US results
                        'sources': sources[:3],
                        'confidence': min(1.0, len(numeric_prices) / max_results),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Cache result
                    if self.cache_store:
                        await self.cache_store.set(cache_key, response, ttl=3600)
                    
                    return response
            
            return {
                'status': 'prices_not_found',
                'product': product_name,
                'message': 'Found results but no prices extracted',
                'sources': sources[:3]
            }
        
        except Exception as e:
            logger.error(f"Search error for {product_name}: {e}")
            return {
                'status': 'error',
                'product': product_name,
                'error': str(e)
            }
    
    async def search_material_price(
        self,
        material_name: str,
        unit: str = 'kg',
        max_results: int = 5
    ) -> Dict:
        """
        Search for raw material pricing.
        
        Args:
            material_name: Material (e.g., "Titanium Ti-6Al-4V", "6061 Aluminum")
            unit: Unit of measurement (kg, lb, m³)
            max_results: Max search results
        
        Returns:
            Dict with material pricing data
        """
        cache_key = f"material:{material_name}:{unit}"
        
        if self.cache_store:
            cached = await self.cache_store.get(cache_key)
            if cached:
                return cached
        
        try:
            search_query = f"{material_name} price per {unit} bulk industrial supplier"
            
            results = await asyncio.to_thread(
                lambda: list(DDGS().text(search_query, max_results=max_results))
            )
            
            if not results:
                return {
                    'status': 'not_found',
                    'material': material_name,
                    'unit': unit
                }
            
            prices = []
            sources = []
            
            for result in results:
                body = result.get('body', '')
                title = result.get('title', '')
                href = result.get('href', '')
                
                extracted_prices = self.price_extractor.extract_prices(body)
                if extracted_prices:
                    prices.extend(extracted_prices)
                    sources.append({
                        'title': title,
                        'url': href,
                        'snippet': body[:200]
                    })
            
            if prices:
                numeric_prices = [p['value'] if p['type'] != 'range' else p['min'] 
                                for p in prices if 'value' in p or 'min' in p]
                
                if numeric_prices:
                    response = {
                        'status': 'success',
                        'material': material_name,
                        'unit': unit,
                        'prices': numeric_prices,
                        'average_price': sum(numeric_prices) / len(numeric_prices),
                        'min_price': min(numeric_prices),
                        'max_price': max(numeric_prices),
                        'currency': 'USD',
                        'sources': sources[:3],
                        'confidence': min(1.0, len(numeric_prices) / max_results),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if self.cache_store:
                        await self.cache_store.set(cache_key, response, ttl=7200)
                    
                    return response
            
            return {
                'status': 'prices_not_found',
                'material': material_name,
                'sources': sources[:3]
            }
        
        except Exception as e:
            logger.error(f"Material search error for {material_name}: {e}")
            return {
                'status': 'error',
                'material': material_name,
                'error': str(e)
            }
    
    async def search_manufacturing_cost_reference(
        self,
        material: str,
        method: str,
        weight_g: float,
        max_results: int = 3
    ) -> Dict:
        """
        Search for manufacturing cost references (e.g., 3D printing, machining costs).
        
        Args:
            material: Material type
            method: Manufacturing method (e.g., "DMLS", "CNC", "FDM")
            weight_g: Part weight in grams
            max_results: Max results to search
        
        Returns:
            Dict with cost references and methodology
        """
        cache_key = f"mfg:{material}:{method}:{weight_g}"
        
        if self.cache_store:
            cached = await self.cache_store.get(cache_key)
            if cached:
                return cached
        
        try:
            search_query = f"{method} 3D printing {material} cost estimate {weight_g}g"
            
            results = await asyncio.to_thread(
                lambda: list(DDGS().text(search_query, max_results=max_results))
            )
            
            if not results:
                return {
                    'status': 'no_data',
                    'method': method,
                    'material': material,
                    'weight_g': weight_g
                }
            
            sources = []
            for result in results:
                sources.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', '')[:300]
                })
            
            response = {
                'status': 'success',
                'method': method,
                'material': material,
                'weight_g': weight_g,
                'sources': sources,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.cache_store:
                await self.cache_store.set(cache_key, response, ttl=7200)
            
            return response
        
        except Exception as e:
            logger.error(f"Manufacturing cost search error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
