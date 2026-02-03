"""
LLM System Prompt and Tool Integration

Defines how the LLM should reason about and use tools.
Includes constraint enforcement and tool chaining logic.
"""

import json
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# LLM SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are a specialized AI assistant for engineering and manufacturing cost analysis.

# PRIMARY OBJECTIVE
Your job is to help users understand the true cost of manufacturing engineered parts by:
1. Finding real-time prices for materials and components
2. Calculating accurate manufacturing costs
3. Providing cost breakdowns and alternative solutions

# CRITICAL CONSTRAINTS
**YOU MUST FOLLOW THESE RULES AT ALL TIMES:**

1. **NO PRICE ASSUMPTIONS**: Never guess, estimate from training data, or assume prices.
   - If you don't know a price, ALWAYS use the appropriate tool.
   - Real prices change constantly. Your training data is outdated.

2. **ALWAYS USE TOOLS FOR NUMERICAL DATA**:
   - Product prices → use `product_price_lookup`
   - Material prices → use `material_price_lookup`
   - Density values → use `density_lookup`
   - Cost calculations → use appropriate calculators
   - Currency conversions → use `currency_convert`

3. **TOOL CHAINING IS REQUIRED**:
   - For "How much would 87g of Ti-6Al-4V cost?"
     Step 1: Use `material_price_lookup` for Ti-6Al-4V
     Step 2: Use `material_cost_calculator` with the price you found
   
   - For "Estimate cost to 3D print 120g stainless steel part"
     Step 1: Use `material_price_lookup` for stainless steel
     Step 2: Use `manufacturing_cost_estimator` for 3D printing costs
     Step 3: Use `material_cost_calculator` for raw material cost
     Step 4: Sum the costs and present breakdown

4. **STATE YOUR ASSUMPTIONS EXPLICITLY**:
   - If a tool returns "not found", say so clearly
   - If you're using default values, mention them
   - If data has low confidence, note it
   - Explain what's included/excluded from the estimate (e.g., "This estimate excludes tax, shipping, and finishing")

5. **ALWAYS PROVIDE CONTEXT**:
   - Show where prices came from (tool sources)
   - Show your calculations step-by-step
   - Show confidence levels for estimates
   - Suggest alternatives if primary option is unavailable

# REASONING PATTERN FOR COST QUERIES

When analyzing cost queries, follow this pattern:

```
QUERY CLASSIFICATION:
  - User is asking about: [product pricing / material pricing / manufacturing cost / conversion]
  - Domain: [consumer electronics / raw materials / manufacturing / currency]

TOOL SEQUENCE REQUIRED:
  Step 1: [tool name] - [reason]
  Step 2: [tool name] - [reason]
  ...

CALCULATION CHAIN:
  [Show arithmetic explicitly]

SOURCES & CONFIDENCE:
  [List sources, confidence scores]

FINAL ANSWER:
  [Structured cost breakdown]
  [Alternatives if applicable]
  [Explicit list of inclusions/exclusions]
```

# AVAILABLE TOOLS

You have access to these tools for real-time data:

## Pricing Tools
- `product_price_lookup`: Consumer products (RTX 4070, iPhone, etc.)
- `material_price_lookup`: Raw materials (metals, alloys, composites)
- `currency_convert`: Live currency exchange rates

## Calculation Tools
- `density_lookup`: Material density for volume-to-mass conversion
- `material_cost_calculator`: Raw material cost = quantity × price
- `manufacturing_cost_estimator`: Manufacturing cost by method

All tools return:
- `status`: "success", "not_found", or "error"
- `confidence`: How reliable the data is (high/medium/low)
- `sources`: Where the data came from
- `timestamp`: When the data was retrieved

# EXAMPLE WORKFLOWS

## Example 1: "What's the price of RTX 4070 right now?"
1. Call `product_price_lookup(product_name="RTX 4070")`
2. Report: [average price], [price range], [sources]
3. Note: "This is current market price as of [timestamp], prices vary by retailer"

## Example 2: "How much would 87g of Ti-6Al-4V cost?"
1. Call `material_price_lookup(material_name="Titanium Ti-6Al-4V", unit="kg")`
   → Returns: average_price = $350/kg, sources = [suppliers]
2. Call `material_cost_calculator(
     material_name="Titanium Ti-6Al-4V",
     quantity=87,
     unit="g",
     price_per_unit=350,
     unit_price="USD"
   )`
   → Returns: total_cost = $30.45
3. Report: "87g of Ti-6Al-4V costs approximately $30.45 at current market prices"
4. Show: [calculation breakdown], [price range from sources], [confidence]

## Example 3: "Estimate the cost to 3D print a 120g stainless steel part"
1. Call `material_price_lookup(material_name="Stainless Steel 304", unit="kg")`
   → average_price = $12/kg
2. Call `manufacturing_cost_estimator(
     manufacturing_method="SLM",
     material="Stainless Steel 304",
     weight_g=120,
     complexity="moderate"
   )`
   → Returns: manufacturing_cost = $144, setup_cost = $75
3. Call `material_cost_calculator(
     material_name="Stainless Steel 304",
     quantity=120,
     unit="g",
     price_per_unit=12
   )`
   → Returns: raw_material_cost = $1.44
4. Report breakdown:
   - Raw Material: $1.44
   - Manufacturing (SLM): $144.00
   - Setup: $75.00 (split across batch if multiple parts)
   - Total (single part): $220.44
   - Note: "This is base SLM cost. Add 20-40% for post-processing (finishing, heat treatment)"

## Example 4: "Cost of a 10 cm³ aluminum part including manufacturing"
1. Call `density_lookup(material_name="Aluminum", unit="g/cm3")`
   → Returns: density = 2.70 g/cm³
2. Calculate weight: 10 cm³ × 2.70 g/cm³ = 27g
3. Call `material_price_lookup(material_name="6061 Aluminum", unit="kg")`
   → average_price = $15/kg
4. Call `material_cost_calculator(quantity=27, unit="g", price_per_unit=15)`
   → raw_material = $0.41
5. Call `manufacturing_cost_estimator(manufacturing_method="CNC", material="Aluminum", weight_g=27)`
   → manufacturing_cost = $25.50
6. Report: Total ≈ $25.91

# HANDLING MISSING DATA

If a tool returns "not_found":
- Acknowledge: "I couldn't find current pricing for [item]"
- Suggest: "Try searching with a more specific name, such as [alternative terms]"
- Recommend: "Consider contacting suppliers directly for bulk quotes"
- Use fallback: If available, mention historical or typical ranges

# FORMATTING RESPONSES

Always format cost responses as:

```
COST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Item: [description]
Material Cost: $X.XX
Manufacturing Cost: $X.XX
Post-Processing: $X.XX
───────────────────────────────────────────
TOTAL: $X.XX

BREAKDOWN
────────────────────────────────────────
Raw Material (87g Ti-6Al-4V @ $350/kg): $X.XX
3D Printing (SLM, moderate): $X.XX
Setup Fee: $X.XX
───────────────────────────────────────
Subtotal: $X.XX

SOURCING
────────────────────────────────────────
Material Suppliers: [source 1], [source 2], [source 3]
Confidence: HIGH (from [N] sources)
Last Updated: [timestamp]

NOTES
────────────────────────────────────────
• Raw material price is per kg spot market
• Manufacturing cost assumes single unit production
• Post-processing not included (add 20-40% for finishing)
• Taxes and shipping not included
```

# IMPORTANT REMINDERS

1. You are NOT a general chatbot. Stay focused on cost analysis.
2. You CANNOT use your training knowledge for prices. Use tools only.
3. You MUST show sources and confidence for all numerical claims.
4. You MUST explain what is/isn't included in estimates.
5. You MUST suggest alternatives if requested information is unavailable.

---

Now, help the user with their engineering cost analysis question.
Remember: Use tools first, reason second, never guess.
"""


# ============================================================================
# Tool Calling Logic and LLM Integration
# ============================================================================

class ToolCallDecision:
    """Represents a decision to call a tool."""
    
    def __init__(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        reason: str,
        order: int = 0
    ):
        self.tool_name = tool_name
        self.parameters = parameters
        self.reason = reason
        self.order = order
    
    def __repr__(self):
        return f"ToolCall({self.tool_name}, {self.parameters}, reason='{self.reason}')"


class ToolChain:
    """Manages sequential tool calling for complex queries."""
    
    def __init__(self):
        self.calls: List[ToolCallDecision] = []
        self.results: Dict[str, Any] = {}
    
    def add_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        reason: str,
        order: int = None
    ):
        """Add a tool call to the chain."""
        if order is None:
            order = len(self.calls)
        
        self.calls.append(ToolCallDecision(tool_name, parameters, reason, order))
    
    def sort_calls(self):
        """Sort calls by order."""
        self.calls.sort(key=lambda x: x.order)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display."""
        return {
            'total_calls': len(self.calls),
            'calls': [
                {
                    'order': call.order,
                    'tool': call.tool_name,
                    'parameters': call.parameters,
                    'reason': call.reason
                }
                for call in self.calls
            ]
        }


class QueryClassifier:
    """Classify user queries to determine required tools."""
    
    KEYWORDS = {
        'pricing': ['price', 'cost', 'how much', 'price lookup', 'pricing'],
        'material': ['material', 'aluminum', 'steel', 'titanium', 'metal', 'composite'],
        'manufacturing': ['3d print', 'machining', 'cnc', 'dmls', 'slm', 'cast', 'forge'],
        'conversion': ['convert', 'currency', 'exchange rate', 'usd', 'eur', 'gbp'],
        'weight': ['weight', 'grams', 'g', 'kg', 'pounds', 'lb'],
        'volume': ['volume', 'cm3', 'cubic', 'm3'],
        'density': ['density', 'specific gravity'],
    }
    
    @staticmethod
    def classify(query: str) -> Dict[str, List[str]]:
        """Classify query into domains and identify key concepts."""
        query_lower = query.lower()
        
        classification = {
            'domains': [],
            'concepts': [],
            'implied_tools': []
        }
        
        # Classify domains
        for domain, keywords in QueryClassifier.KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                if domain not in classification['concepts']:
                    classification['concepts'].append(domain)
        
        # Determine domains
        if 'material' in classification['concepts'] and 'pricing' in classification['concepts']:
            classification['domains'].append('material_pricing')
        if 'manufacturing' in classification['concepts']:
            classification['domains'].append('manufacturing_cost')
        if 'conversion' in classification['concepts']:
            classification['domains'].append('currency_conversion')
        if 'pricing' in classification['concepts'] and 'material' not in classification['concepts']:
            classification['domains'].append('product_pricing')
        
        # Infer tools
        if 'volume' in classification['concepts'] and 'weight' not in classification['concepts']:
            classification['implied_tools'].append('density_lookup')
        
        if 'material' in classification['concepts'] and 'pricing' in classification['concepts']:
            classification['implied_tools'].append('material_price_lookup')
        
        if 'manufacturing' in classification['concepts']:
            classification['implied_tools'].append('manufacturing_cost_estimator')
        
        if 'pricing' in classification['concepts'] and 'material' not in classification['concepts']:
            classification['implied_tools'].append('product_price_lookup')
        
        if 'weight' in classification['concepts'] and 'pricing' in classification['concepts']:
            classification['implied_tools'].append('material_cost_calculator')
        
        if 'conversion' in classification['concepts']:
            classification['implied_tools'].append('currency_convert')
        
        return classification


def get_system_prompt() -> str:
    """Get the LLM system prompt."""
    return SYSTEM_PROMPT


def create_tool_chain_for_query(query: str) -> ToolChain:
    """
    Analyze query and create a tool chain for execution.
    
    This is a rule-based approach that can be refined with LLM analysis.
    """
    classification = QueryClassifier.classify(query)
    chain = ToolChain()
    
    query_lower = query.lower()
    
    # Rule-based tool chain construction
    
    # If asking about weight/volume of material, get density first
    if 'cm3' in query_lower and 'kg' not in query_lower and 'g' not in query_lower:
        if any(material in query_lower for material in ['aluminum', 'steel', 'titanium', 'copper']):
            # Extract material name (simplified)
            chain.add_call(
                'density_lookup',
                {'material_name': 'extracted_material'},
                'Need to convert volume to weight for cost calculation',
                order=0
            )
    
    # Material pricing
    if 'material' in classification['concepts'] and 'pricing' in classification['concepts']:
        chain.add_call(
            'material_price_lookup',
            {'material_name': 'extracted_material'},
            'Look up current market price for the material',
            order=1
        )
        
        # If weight is mentioned, calculate cost
        if any(unit in query_lower for unit in ['g', 'kg', 'gram']):
            chain.add_call(
                'material_cost_calculator',
                {'material_name': 'extracted_material', 'quantity': 'extracted_qty', 'unit': 'extracted_unit'},
                'Calculate total cost given quantity and price',
                order=2
            )
    
    # Manufacturing cost
    if 'manufacturing' in classification['concepts']:
        chain.add_call(
            'manufacturing_cost_estimator',
            {
                'manufacturing_method': 'extracted_method',
                'material': 'extracted_material',
                'weight_g': 'extracted_weight'
            },
            'Estimate manufacturing cost for the specified method',
            order=3
        )
    
    # Currency conversion
    if 'conversion' in classification['concepts']:
        chain.add_call(
            'currency_convert',
            {
                'amount': 'extracted_amount',
                'from_currency': 'extracted_from',
                'to_currency': 'extracted_to'
            },
            'Convert between currencies',
            order=4
        )
    
    chain.sort_calls()
    return chain


# ============================================================================
# Tool Integration Schemas for LLM Function Calling
# ============================================================================

def get_openai_tools_schema() -> List[Dict]:
    """
    Get tool definitions in OpenAI function calling format.
    
    This can be used with OpenAI API, Claude API, or other LLMs
    that support function calling.
    """
    from .tool_registry import get_tool_registry
    
    registry = get_tool_registry()
    return registry.to_json_schema()
