"""
Tool Registry and Management

Maintains list of available tools, their schemas, and metadata for LLM function calling.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str  # 'string', 'number', 'integer', 'object', 'array'
    description: str
    required: bool = True
    enum: Optional[List] = None
    default: Optional[any] = None


@dataclass
class ToolDefinition:
    """Complete tool definition for LLM function calling."""
    name: str
    description: str
    category: str  # 'pricing', 'calculation', 'conversion'
    parameters: List[ToolParameter]
    returns: Dict[str, str]  # Description of return values
    examples: List[Dict] = None
    cost_estimate: Optional[str] = None  # Free, credit-based, etc.


class ToolRegistry:
    """Registry of all available tools with LLM-compatible schemas."""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools."""
        
        # Product Price Lookup Tool
        self.register_tool(ToolDefinition(
            name='product_price_lookup',
            description='Look up current market prices for consumer products (GPUs, phones, electronics, etc.)',
            category='pricing',
            parameters=[
                ToolParameter(
                    name='product_name',
                    type='string',
                    description='Name of the product (e.g., "RTX 4070", "iPhone 15 Pro Max")',
                    required=True
                ),
                ToolParameter(
                    name='quantity',
                    type='integer',
                    description='Number of units to price',
                    required=False,
                    default=1
                ),
                ToolParameter(
                    name='region',
                    type='string',
                    description='Geographic region for pricing (US, EU, CN, etc.)',
                    required=False,
                    default='US'
                ),
            ],
            returns={
                'status': 'success/not_found/error',
                'product': 'Product name',
                'prices': 'List of found prices',
                'average': 'Average price across sources',
                'min': 'Minimum price found',
                'max': 'Maximum price found',
                'currency': 'Currency of prices',
                'sources': 'List of sources with URLs',
                'confidence': 'Confidence score (0.0-1.0)'
            },
            examples=[
                {
                    'query': 'product_price_lookup(product_name="RTX 4070")',
                    'response': {'status': 'success', 'product': 'RTX 4070', 'average': 599.99}
                }
            ]
        ))
        
        # Material Price Lookup Tool
        self.register_tool(ToolDefinition(
            name='material_price_lookup',
            description='Look up prices for raw materials (metals, alloys, composites, etc.)',
            category='pricing',
            parameters=[
                ToolParameter(
                    name='material_name',
                    type='string',
                    description='Material name (e.g., "Titanium Ti-6Al-4V", "6061 Aluminum", "Carbon Fiber")',
                    required=True
                ),
                ToolParameter(
                    name='unit',
                    type='string',
                    description='Unit of measurement',
                    required=False,
                    enum=['kg', 'lb', 'g', 'm3', 'cm3'],
                    default='kg'
                ),
                ToolParameter(
                    name='purity_grade',
                    type='string',
                    description='Material grade or specification',
                    required=False
                ),
            ],
            returns={
                'status': 'success/not_found/error',
                'material': 'Material name',
                'unit': 'Unit of measurement',
                'average_price': 'Average price per unit',
                'min_price': 'Minimum price found',
                'max_price': 'Maximum price found',
                'currency': 'Currency',
                'sources': 'Supplier sources',
                'confidence': 'Confidence score'
            }
        ))
        
        # Density Lookup Tool
        self.register_tool(ToolDefinition(
            name='density_lookup',
            description='Look up material density to convert volume to mass',
            category='calculation',
            parameters=[
                ToolParameter(
                    name='material_name',
                    type='string',
                    description='Material name',
                    required=True
                ),
                ToolParameter(
                    name='unit',
                    type='string',
                    description='Unit for output density',
                    required=False,
                    enum=['g/cm3', 'kg/m3', 'lb/in3'],
                    default='g/cm3'
                ),
            ],
            returns={
                'material': 'Material name',
                'density': 'Density value',
                'unit': 'Unit of density',
                'status': 'success/error',
                'confidence': 'How confident the value is'
            }
        ))
        
        # Material Cost Calculator
        self.register_tool(ToolDefinition(
            name='material_cost_calculator',
            description='Calculate raw material cost from price per unit and weight/volume',
            category='calculation',
            parameters=[
                ToolParameter(
                    name='material_name',
                    type='string',
                    description='Material name',
                    required=True
                ),
                ToolParameter(
                    name='quantity',
                    type='number',
                    description='Quantity of material',
                    required=True
                ),
                ToolParameter(
                    name='unit',
                    type='string',
                    description='Unit of quantity',
                    required=True,
                    enum=['kg', 'lb', 'g', 'cm3', 'm3']
                ),
                ToolParameter(
                    name='price_per_unit',
                    type='number',
                    description='Price per unit (from material_price_lookup)',
                    required=True
                ),
                ToolParameter(
                    name='unit_price',
                    type='string',
                    description='Currency unit of price',
                    required=False,
                    default='USD'
                ),
            ],
            returns={
                'material': 'Material name',
                'quantity': 'Input quantity',
                'unit': 'Input unit',
                'total_cost': 'Total raw material cost',
                'currency': 'Currency',
                'calculation': 'Breakdown of calculation'
            }
        ))
        
        # Manufacturing Cost Estimator
        self.register_tool(ToolDefinition(
            name='manufacturing_cost_estimator',
            description='Estimate manufacturing cost based on material, method, and weight',
            category='calculation',
            parameters=[
                ToolParameter(
                    name='manufacturing_method',
                    type='string',
                    description='Manufacturing process',
                    required=True,
                    enum=['DMLS', 'SLM', 'FDM', 'CNC', 'Machining', 'Casting', 'Forging', 'Sheet_Metal']
                ),
                ToolParameter(
                    name='material',
                    type='string',
                    description='Material being used',
                    required=True
                ),
                ToolParameter(
                    name='weight_g',
                    type='number',
                    description='Part weight in grams',
                    required=True
                ),
                ToolParameter(
                    name='volume_cm3',
                    type='number',
                    description='Part volume in cubic centimeters (optional)',
                    required=False
                ),
                ToolParameter(
                    name='complexity',
                    type='string',
                    description='Part complexity (simple/moderate/complex)',
                    required=False,
                    enum=['simple', 'moderate', 'complex'],
                    default='moderate'
                ),
                ToolParameter(
                    name='post_processing',
                    type='string',
                    description='Post-processing requirements',
                    required=False
                ),
            ],
            returns={
                'method': 'Manufacturing method',
                'material': 'Material used',
                'weight_g': 'Part weight',
                'raw_material_cost': 'Cost of raw material',
                'manufacturing_cost': 'Manufacturing labor/machine cost',
                'post_processing_cost': 'Post-processing cost',
                'total_cost': 'Total estimated cost',
                'currency': 'Currency',
                'confidence': 'Confidence of estimate'
            }
        ))
        
        # Currency Converter
        self.register_tool(ToolDefinition(
            name='currency_convert',
            description='Convert between currencies using live exchange rates',
            category='conversion',
            parameters=[
                ToolParameter(
                    name='amount',
                    type='number',
                    description='Amount to convert',
                    required=True
                ),
                ToolParameter(
                    name='from_currency',
                    type='string',
                    description='Source currency code (USD, EUR, GBP, etc.)',
                    required=True
                ),
                ToolParameter(
                    name='to_currency',
                    type='string',
                    description='Target currency code',
                    required=True
                ),
            ],
            returns={
                'from_amount': 'Original amount',
                'from_currency': 'Original currency',
                'to_amount': 'Converted amount',
                'to_currency': 'Target currency',
                'exchange_rate': 'Applied exchange rate',
                'timestamp': 'When rate was fetched'
            }
        ))
    
    def register_tool(self, tool_def: ToolDefinition):
        """Register a tool definition."""
        self.tools[tool_def.name] = tool_def
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, ToolDefinition]:
        """Get all registered tools."""
        return self.tools
    
    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """Get all tools in a category."""
        return [t for t in self.tools.values() if t.category == category]
    
    def to_json_schema(self) -> Dict:
        """Convert registry to OpenAI-compatible JSON schema."""
        tools_schema = []
        
        for tool_def in self.tools.values():
            tool_schema = {
                'type': 'function',
                'function': {
                    'name': tool_def.name,
                    'description': tool_def.description,
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            }
            
            # Add parameters
            for param in tool_def.parameters:
                param_schema = {
                    'type': param.type,
                    'description': param.description
                }
                
                if param.enum:
                    param_schema['enum'] = param.enum
                
                if param.default is not None:
                    param_schema['default'] = param.default
                
                tool_schema['function']['parameters']['properties'][param.name] = param_schema
                
                if param.required:
                    tool_schema['function']['parameters']['required'].append(param.name)
            
            tools_schema.append(tool_schema)
        
        return tools_schema
    
    def to_dict(self) -> Dict:
        """Convert registry to dictionary format for API responses."""
        result = {}
        for name, tool_def in self.tools.items():
            result[name] = {
                'description': tool_def.description,
                'category': tool_def.category,
                'parameters': [
                    {
                        'name': p.name,
                        'type': p.type,
                        'description': p.description,
                        'required': p.required,
                        'enum': p.enum,
                        'default': p.default
                    }
                    for p in tool_def.parameters
                ],
                'returns': tool_def.returns,
                'examples': tool_def.examples
            }
        return result


# Global registry instance
_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
