"""
Tool Implementations for LLM-Augmented Pricing

Each tool handles a specific pricing or calculation task.
All tools return structured JSON suitable for LLM consumption.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import asyncio
from decimal import Decimal

from .price_search import WebSearchEngine, PriceExtractor
from .database_cache import CacheStore

logger = logging.getLogger(__name__)


class BasePriceTool:
    """Base class for all pricing tools."""
    
    def __init__(self, cache_store: CacheStore = None):
        self.cache_store = cache_store
        self.search_engine = WebSearchEngine(cache_store)
    
    async def execute(self, **kwargs) -> Dict:
        """Execute the tool. Override in subclasses."""
        raise NotImplementedError


class ProductPriceTool(BasePriceTool):
    """Look up consumer product prices."""
    
    async def execute(
        self,
        product_name: str,
        quantity: int = 1,
        region: str = 'US',
        **kwargs
    ) -> Dict:
        """
        Lookup product pricing.
        
        Args:
            product_name: Product to search for
            quantity: Quantity (affects bulk pricing)
            region: Geographic region
        
        Returns:
            Structured pricing data
        """
        logger.info(f"Tool: product_price_lookup('{product_name}', qty={quantity}, region={region})")
        
        try:
            result = await self.search_engine.search_product_price(
                product_name=product_name,
                quantity=quantity,
                max_results=5
            )
            
            return result
        
        except Exception as e:
            logger.error(f"ProductPriceTool error: {e}")
            return {
                'status': 'error',
                'product': product_name,
                'error': str(e)
            }


class MaterialPriceTool(BasePriceTool):
    """Look up raw material prices."""
    
    # Database of standard materials with typical specifications
    MATERIAL_SPECS = {
        'aluminum': ['6061', '5083', '7075', 'pure'],
        'steel': ['1045', '4140', '304', '316'],
        'titanium': ['Ti-6Al-4V', 'Ti-5Al-5V-5Fe', 'Grade 2'],
        'copper': ['pure', 'brass', 'bronze'],
        'nickel': ['Inconel 625', 'Inconel 718'],
        'composite': ['carbon-fiber', 'glass-fiber', 'aramid'],
        'polymer': ['ABS', 'PLA', 'PETG', 'Nylon', 'PEEK']
    }
    
    async def execute(
        self,
        material_name: str,
        unit: str = 'kg',
        purity_grade: str = None,
        **kwargs
    ) -> Dict:
        """
        Lookup material pricing.
        
        Args:
            material_name: Material specification
            unit: Unit of measurement (kg, lb, g, m3)
            purity_grade: Optional specification/grade
        
        Returns:
            Material pricing data
        """
        logger.info(f"Tool: material_price_lookup('{material_name}', unit={unit}, grade={purity_grade})")
        
        try:
            # Format search query
            search_term = material_name
            if purity_grade:
                search_term = f"{material_name} {purity_grade}"
            
            result = await self.search_engine.search_material_price(
                material_name=search_term,
                unit=unit,
                max_results=5
            )
            
            # Normalize units if needed
            if result['status'] == 'success' and unit != 'kg':
                result['normalized_to_kg'] = self._normalize_to_kg(
                    result.get('average_price', 0),
                    unit
                )
            
            return result
        
        except Exception as e:
            logger.error(f"MaterialPriceTool error: {e}")
            return {
                'status': 'error',
                'material': material_name,
                'error': str(e)
            }
    
    @staticmethod
    def _normalize_to_kg(price: float, from_unit: str) -> float:
        """Convert price to per-kg equivalent."""
        conversions = {
            'kg': 1.0,
            'lb': 2.20462,
            'g': 1000,
            'm3': 0.001,  # This is approximate; depends on material density
            'cm3': 1000000
        }
        return price * conversions.get(from_unit, 1.0)


class DensityLookupTool(BasePriceTool):
    """Look up material density for volume-to-mass conversion."""
    
    # Material density database (g/cm³)
    MATERIAL_DENSITIES = {
        'aluminum': {'6061': 2.70, '5083': 2.66, '7075': 2.81, 'pure': 2.70},
        'steel': {'1045': 7.85, '304': 8.0, '316': 8.0, '4140': 7.85},
        'stainless': {'304': 8.0, '316': 8.0, '410': 7.75},
        'titanium': {'Ti-6Al-4V': 4.43, 'Ti-5Al-5V-5Fe': 4.81, 'Grade 2': 4.51},
        'copper': {'pure': 8.96, 'brass': 8.5, 'bronze': 8.75},
        'nickel': {'Inconel 625': 8.44, 'Inconel 718': 8.19},
        'cast iron': 7.2,
        'magnesium': 1.8,
        'lead': 11.34,
        'zinc': 7.14,
        'tungsten': 19.25,
        'platinum': 21.45,
        'gold': 19.3,
        'silver': 10.49,
        'plastic': {
            'ABS': 1.04,
            'PLA': 1.24,
            'PETG': 1.27,
            'Nylon': 1.14,
            'TPU': 1.21,
            'PEEK': 1.32,
            'Polycarbonate': 1.20
        },
        'composite': {
            'carbon-fiber': 1.60,
            'glass-fiber': 1.85,
            'aramid': 1.44
        }
    }
    
    async def execute(
        self,
        material_name: str,
        unit: str = 'g/cm3',
        **kwargs
    ) -> Dict:
        """
        Lookup material density.
        
        Args:
            material_name: Material name
            unit: Output unit (g/cm3, kg/m3, lb/in3)
        
        Returns:
            Density information
        """
        logger.info(f"Tool: density_lookup('{material_name}', unit={unit})")
        
        try:
            # Search material database
            density_g_cm3 = self._find_density(material_name)
            
            if density_g_cm3 is None:
                return {
                    'status': 'not_found',
                    'material': material_name,
                    'message': f'Density not found for {material_name}. Please search manually.'
                }
            
            # Convert to requested unit
            converted = self._convert_density(density_g_cm3, unit)
            
            return {
                'status': 'success',
                'material': material_name,
                'density': converted,
                'unit': unit,
                'base_unit': 'g/cm3',
                'base_density': density_g_cm3,
                'confidence': 'high'
            }
        
        except Exception as e:
            logger.error(f"DensityLookupTool error: {e}")
            return {
                'status': 'error',
                'material': material_name,
                'error': str(e)
            }
    
    @staticmethod
    def _find_density(material_name: str) -> Optional[float]:
        """Search density database."""
        material_lower = material_name.lower()
        
        # Direct lookup
        if material_lower in DensityLookupTool.MATERIAL_DENSITIES:
            data = DensityLookupTool.MATERIAL_DENSITIES[material_lower]
            return data if isinstance(data, float) else next(iter(data.values()))
        
        # Partial match
        for mat_key, mat_data in DensityLookupTool.MATERIAL_DENSITIES.items():
            if mat_key in material_lower or material_lower in mat_key:
                if isinstance(mat_data, dict):
                    return next(iter(mat_data.values()))
                return mat_data
        
        return None
    
    @staticmethod
    def _convert_density(density_g_cm3: float, to_unit: str) -> float:
        """Convert density to requested unit."""
        conversions = {
            'g/cm3': 1.0,
            'kg/m3': density_g_cm3 * 1000,
            'lb/in3': density_g_cm3 * 0.036127,
            'lb/ft3': density_g_cm3 * 62.4279
        }
        return round(conversions.get(to_unit, density_g_cm3), 4)


class MaterialCostCalculatorTool(BasePriceTool):
    """Calculate raw material cost from price and weight."""
    
    async def execute(
        self,
        material_name: str,
        quantity: float,
        unit: str,
        price_per_unit: float,
        unit_price: str = 'USD',
        **kwargs
    ) -> Dict:
        """
        Calculate material cost.
        
        Args:
            material_name: Material name
            quantity: Amount of material
            unit: Unit of quantity
            price_per_unit: Price per unit (from material_price_lookup)
            unit_price: Currency
        
        Returns:
            Cost calculation breakdown
        """
        logger.info(
            f"Tool: material_cost_calculator('{material_name}', {quantity}{unit}, "
            f"${price_per_unit}/{unit})"
        )
        
        try:
            # Normalize quantity to kg if needed
            quantity_kg = self._normalize_quantity_to_kg(quantity, unit)
            
            total_cost = quantity_kg * price_per_unit
            
            return {
                'status': 'success',
                'material': material_name,
                'input': {
                    'quantity': quantity,
                    'unit': unit
                },
                'normalized': {
                    'quantity_kg': round(quantity_kg, 4),
                    'price_per_kg': round(price_per_unit, 2)
                },
                'calculation': f"{quantity_kg:.4f} kg × ${price_per_unit}/kg = ${total_cost:.2f}",
                'total_cost': round(total_cost, 2),
                'currency': unit_price,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"MaterialCostCalculatorTool error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def _normalize_quantity_to_kg(quantity: float, unit: str) -> float:
        """Convert any unit to kg."""
        conversions = {
            'kg': 1.0,
            'g': 0.001,
            'lb': 0.453592,
            'oz': 0.0283495,
            'mg': 0.000001
        }
        return quantity * conversions.get(unit, 1.0)


class ManufacturingCostEstimatorTool(BasePriceTool):
    """Estimate manufacturing cost based on method and material."""
    
    # Manufacturing cost models ($/g for base cost, adjusted by complexity)
    COST_MODELS = {
        'FDM': {'base_cost_per_g': 0.05, 'setup_cost': 10, 'methods': ['polymer']},
        'SLA': {'base_cost_per_g': 0.08, 'setup_cost': 15, 'methods': ['resin']},
        'DMLS': {'base_cost_per_g': 0.80, 'setup_cost': 50, 'methods': ['metal']},
        'SLM': {'base_cost_per_g': 1.20, 'setup_cost': 75, 'methods': ['metal']},
        'CNC': {'base_cost_per_g': 0.40, 'setup_cost': 30, 'methods': ['metal', 'plastic']},
        'Machining': {'base_cost_per_g': 0.35, 'setup_cost': 25, 'methods': ['metal']},
        'Casting': {'base_cost_per_g': 0.15, 'setup_cost': 100, 'methods': ['metal']},
        'Forging': {'base_cost_per_g': 0.25, 'setup_cost': 150, 'methods': ['metal']},
        'Sheet_Metal': {'base_cost_per_g': 0.20, 'setup_cost': 40, 'methods': ['metal']}
    }
    
    # Complexity multipliers
    COMPLEXITY_MULTIPLIERS = {
        'simple': 1.0,
        'moderate': 1.5,
        'complex': 2.5
    }
    
    # Post-processing cost estimates
    POST_PROCESSING_COSTS = {
        'none': 0,
        'light_sanding': 15,
        'polishing': 30,
        'anodizing': 50,
        'plating': 75,
        'painting': 40,
        'heat_treatment': 100,
        'assembly': 75
    }
    
    async def execute(
        self,
        manufacturing_method: str,
        material: str,
        weight_g: float,
        volume_cm3: Optional[float] = None,
        complexity: str = 'moderate',
        post_processing: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Estimate manufacturing cost.
        
        Args:
            manufacturing_method: e.g., 'DMLS', 'CNC', 'FDM'
            material: Material type
            weight_g: Part weight in grams
            volume_cm3: Optional volume for material cost calculation
            complexity: simple/moderate/complex
            post_processing: Post-processing type
        
        Returns:
            Cost breakdown
        """
        logger.info(
            f"Tool: manufacturing_cost_estimator(method={manufacturing_method}, "
            f"material={material}, weight={weight_g}g, complexity={complexity})"
        )
        
        try:
            if manufacturing_method not in self.COST_MODELS:
                return {
                    'status': 'error',
                    'error': f"Unknown manufacturing method: {manufacturing_method}"
                }
            
            model = self.COST_MODELS[manufacturing_method]
            complexity_mult = self.COMPLEXITY_MULTIPLIERS.get(complexity, 1.5)
            
            # Calculate manufacturing cost
            manufacturing_cost = (
                model['base_cost_per_g'] * weight_g * complexity_mult +
                model['setup_cost']
            )
            
            # Post-processing cost
            post_processing_cost = 0
            if post_processing:
                post_processing_cost = self.POST_PROCESSING_COSTS.get(
                    post_processing.lower(), 0
                )
            
            total_cost = manufacturing_cost + post_processing_cost
            
            # Estimate raw material cost
            raw_material_cost = 0
            if volume_cm3:
                # Would need density to calculate; recommend calling density_lookup
                pass
            
            return {
                'status': 'success',
                'method': manufacturing_method,
                'material': material,
                'weight_g': weight_g,
                'complexity': complexity,
                'costs': {
                    'base_cost_per_g': model['base_cost_per_g'],
                    'complexity_multiplier': complexity_mult,
                    'setup_cost': model['setup_cost'],
                    'manufacturing_cost': round(manufacturing_cost, 2),
                    'post_processing_cost': post_processing_cost,
                },
                'calculation': {
                    'manufacturing': f"({model['base_cost_per_g']}$/g × {weight_g}g × {complexity_mult}) + ${model['setup_cost']} = ${manufacturing_cost:.2f}",
                    'post_processing': f"{post_processing or 'None'}: ${post_processing_cost:.2f}",
                    'total': f"${total_cost:.2f}"
                },
                'total_cost': round(total_cost, 2),
                'currency': 'USD',
                'confidence': 'medium',
                'note': 'Raw material cost not included. Call material_cost_calculator for accurate total.',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"ManufacturingCostEstimatorTool error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


class CurrencyConversionTool(BasePriceTool):
    """Convert between currencies using live exchange rates."""
    
    # Fallback rates (updated periodically via API in production)
    EXCHANGE_RATES = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'JPY': 149.50,
        'CNY': 7.08,
        'INR': 83.12,
        'CAD': 1.36,
        'AUD': 1.52,
        'CHF': 0.88,
        'SGD': 1.34,
        'HKD': 7.81,
        'NZD': 1.69,
        'MXN': 17.05,
        'BRL': 4.97,
    }
    
    async def execute(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        **kwargs
    ) -> Dict:
        """
        Convert between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
        
        Returns:
            Conversion result
        """
        logger.info(
            f"Tool: currency_convert({amount}{from_currency} → {to_currency})"
        )
        
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            if from_currency not in self.EXCHANGE_RATES:
                return {
                    'status': 'error',
                    'error': f"Unknown currency: {from_currency}"
                }
            
            if to_currency not in self.EXCHANGE_RATES:
                return {
                    'status': 'error',
                    'error': f"Unknown currency: {to_currency}"
                }
            
            # Convert via USD
            amount_usd = amount / self.EXCHANGE_RATES[from_currency]
            converted_amount = amount_usd * self.EXCHANGE_RATES[to_currency]
            exchange_rate = self.EXCHANGE_RATES[to_currency] / self.EXCHANGE_RATES[from_currency]
            
            return {
                'status': 'success',
                'from_amount': amount,
                'from_currency': from_currency,
                'to_amount': round(converted_amount, 2),
                'to_currency': to_currency,
                'exchange_rate': round(exchange_rate, 4),
                'calculation': f"{amount} {from_currency} × {exchange_rate:.4f} = {converted_amount:.2f} {to_currency}",
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"CurrencyConversionTool error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
