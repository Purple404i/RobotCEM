"""
Example End-to-End Tool Usage Scenarios

Demonstrates complete flows from user query to final cost breakdown.
"""

import asyncio
import json
from typing import Dict, Any

from tools.price_tools import (
    ProductPriceTool,
    MaterialPriceTool,
    DensityLookupTool,
    MaterialCostCalculatorTool,
    ManufacturingCostEstimatorTool,
    CurrencyConversionTool
)
from tools.database_cache import get_cache_store
from tools.llm_integration import QueryClassifier, create_tool_chain_for_query


# Initialize tools
cache_store = get_cache_store()

product_tool = ProductPriceTool(cache_store)
material_tool = MaterialPriceTool(cache_store)
density_tool = DensityLookupTool(cache_store)
cost_calc_tool = MaterialCostCalculatorTool(cache_store)
mfg_tool = ManufacturingCostEstimatorTool(cache_store)
currency_tool = CurrencyConversionTool(cache_store)


async def example_1_consumer_product_pricing():
    """
    Example 1: "What's the price of RTX 4070 right now?"
    
    Simple product lookup - single tool call.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Consumer Product Pricing")
    print("="*70)
    print("Query: What's the price of RTX 4070 right now?")
    print("-"*70)
    
    result = await product_tool.execute(product_name="RTX 4070")
    
    print(f"\nTool Called: product_price_lookup")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"\nPricing Information:")
        print(f"  Product: {result['product']}")
        print(f"  Average Price: ${result['average']:.2f}")
        print(f"  Price Range: ${result['min']:.2f} - ${result['max']:.2f}")
        print(f"  Currency: {result['currency']}")
        print(f"  Confidence: {result['confidence']*100:.0f}%")
        print(f"  Sources: {len(result['sources'])} found")
        
        print(f"\nTop Sources:")
        for i, source in enumerate(result['sources'][:3], 1):
            print(f"  {i}. {source['title']}")
    
    return result


async def example_2_material_weight_cost():
    """
    Example 2: "How much would 87g of Ti-6Al-4V cost?"
    
    Demonstrates tool chaining:
    1. Look up material price
    2. Calculate cost for quantity
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Material Weight Cost Calculation")
    print("="*70)
    print("Query: How much would 87g of Ti-6Al-4V cost?")
    print("-"*70)
    
    # Step 1: Get material price
    print("\nStep 1: Looking up material price...")
    price_result = await material_tool.execute(
        material_name="Titanium Ti-6Al-4V",
        unit="kg"
    )
    
    print(f"  Status: {price_result['status']}")
    
    if price_result['status'] == 'success':
        price_per_kg = price_result['average_price']
        print(f"  Material: {price_result['material']}")
        print(f"  Price: ${price_per_kg:.2f}/kg")
        print(f"  Price Range: ${price_result['min_price']:.2f} - ${price_result['max_price']:.2f}/kg")
        
        # Step 2: Calculate cost
        print("\nStep 2: Calculating total cost...")
        cost_result = await cost_calc_tool.execute(
            material_name="Titanium Ti-6Al-4V",
            quantity=87,
            unit="g",
            price_per_unit=price_per_kg,
            unit_price="USD"
        )
        
        print(f"  {cost_result['calculation']}")
        print(f"\n  RESULT: ${cost_result['total_cost']:.2f}")
        print(f"  Currency: {cost_result['currency']}")
        
        # Show breakdown
        print(f"\nBreakdown:")
        print(f"  Material: 87g = 0.087 kg")
        print(f"  Unit Price: ${price_per_kg:.2f}/kg")
        print(f"  Total: 0.087 kg × ${price_per_kg:.2f}/kg = ${cost_result['total_cost']:.2f}")
        
        return cost_result
    
    return price_result


async def example_3_manufacturing_cost_estimation():
    """
    Example 3: "Estimate the cost to 3D print a 120g stainless steel part"
    
    Complex scenario requiring tool chaining:
    1. Look up stainless steel price
    2. Estimate manufacturing cost (SLM 3D printing)
    3. Calculate raw material cost
    4. Combine results
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Manufacturing Cost Estimation")
    print("="*70)
    print("Query: Estimate the cost to 3D print a 120g stainless steel part")
    print("-"*70)
    
    # Step 1: Material pricing
    print("\nStep 1: Looking up stainless steel pricing...")
    material_result = await material_tool.execute(
        material_name="Stainless Steel 304",
        unit="kg"
    )
    
    if material_result['status'] != 'success':
        print("  ✗ Material price lookup failed")
        return
    
    price_per_kg = material_result['average_price']
    print(f"  ✓ Found: ${price_per_kg:.2f}/kg (range: ${material_result['min_price']:.2f}-${material_result['max_price']:.2f})")
    
    # Step 2: Manufacturing cost
    print("\nStep 2: Estimating manufacturing cost (SLM 3D printing)...")
    mfg_result = await mfg_tool.execute(
        manufacturing_method="SLM",
        material="Stainless Steel 304",
        weight_g=120,
        complexity="moderate",
        post_processing="polishing"
    )
    
    if mfg_result['status'] != 'success':
        print("  ✗ Manufacturing cost estimation failed")
        return
    
    print(f"  ✓ Manufacturing Cost: ${mfg_result['total_cost']:.2f}")
    print(f"    Breakdown: {mfg_result['calculation']['manufacturing']}")
    print(f"    Post-processing: {mfg_result['calculation']['post_processing']}")
    
    # Step 3: Raw material cost
    print("\nStep 3: Calculating raw material cost...")
    cost_result = await cost_calc_tool.execute(
        material_name="Stainless Steel 304",
        quantity=120,
        unit="g",
        price_per_unit=price_per_kg,
        unit_price="USD"
    )
    
    raw_material_cost = cost_result['total_cost']
    print(f"  ✓ Raw Material Cost: ${raw_material_cost:.2f}")
    print(f"    {cost_result['calculation']}")
    
    # Step 4: Total cost
    print("\n" + "="*70)
    print("FINAL COST SUMMARY")
    print("="*70)
    
    raw_material = raw_material_cost
    manufacturing = mfg_result['costs']['manufacturing_cost']
    post_processing = mfg_result['costs']['post_processing_cost']
    total = raw_material + manufacturing + post_processing
    
    print(f"Raw Material (120g @ ${price_per_kg:.2f}/kg):  ${raw_material:>8.2f}")
    print(f"Manufacturing (SLM, moderate):      ${manufacturing:>8.2f}")
    print(f"Post-processing (polishing):        ${post_processing:>8.2f}")
    print("-" * 40)
    print(f"TOTAL PART COST:                    ${total:>8.2f}")
    print("="*70)
    
    print(f"\nNotes:")
    print(f"  • Raw material sourcing: {len(material_result['sources'])} suppliers found")
    print(f"  • Manufacturing method: SLM (Selective Laser Melting)")
    print(f"  • Confidence: HIGH (multiple data sources)")
    print(f"  • Excludes: Taxes, shipping, design time, quality inspection")
    
    return {
        'raw_material': raw_material,
        'manufacturing': manufacturing,
        'post_processing': post_processing,
        'total': total
    }


async def example_4_volume_to_weight_cost():
    """
    Example 4: "Cost of a 10 cm³ aluminum part including manufacturing"
    
    Requires density conversion before cost calculation:
    1. Look up density
    2. Calculate weight from volume
    3. Look up material price
    4. Calculate cost
    5. Estimate manufacturing cost
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Volume-Based Cost Estimation")
    print("="*70)
    print("Query: Cost of a 10 cm³ aluminum part including manufacturing")
    print("-"*70)
    
    # Step 1: Get density
    print("\nStep 1: Looking up aluminum density...")
    density_result = await density_tool.execute(
        material_name="Aluminum 6061",
        unit="g/cm3"
    )
    
    if density_result['status'] != 'success':
        print("  ✗ Density lookup failed")
        return
    
    density = density_result['density']
    print(f"  ✓ Density: {density} g/cm³")
    
    # Step 2: Calculate weight
    print("\nStep 2: Calculating weight from volume...")
    volume = 10  # cm³
    weight_g = volume * density
    print(f"  Volume: {volume} cm³")
    print(f"  Density: {density} g/cm³")
    print(f"  Weight: {volume} × {density} = {weight_g:.2f}g")
    
    # Step 3: Material price
    print("\nStep 3: Looking up aluminum pricing...")
    material_result = await material_tool.execute(
        material_name="6061 Aluminum",
        unit="kg"
    )
    
    if material_result['status'] != 'success':
        print("  ✗ Material price lookup failed")
        return
    
    price_per_kg = material_result['average_price']
    print(f"  ✓ Price: ${price_per_kg:.2f}/kg")
    
    # Step 4: Material cost
    print("\nStep 4: Calculating raw material cost...")
    cost_result = await cost_calc_tool.execute(
        material_name="6061 Aluminum",
        quantity=weight_g,
        unit="g",
        price_per_unit=price_per_kg,
        unit_price="USD"
    )
    
    raw_material_cost = cost_result['total_cost']
    print(f"  ✓ Material Cost: ${raw_material_cost:.2f}")
    
    # Step 5: Manufacturing cost (assume CNC)
    print("\nStep 5: Estimating manufacturing cost (CNC machining)...")
    mfg_result = await mfg_tool.execute(
        manufacturing_method="CNC",
        material="6061 Aluminum",
        weight_g=weight_g,
        complexity="moderate"
    )
    
    manufacturing_cost = mfg_result['costs']['manufacturing_cost']
    print(f"  ✓ Manufacturing Cost: ${manufacturing_cost:.2f}")
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL COST BREAKDOWN")
    print("="*70)
    
    total = raw_material_cost + manufacturing_cost
    
    print(f"Part Specification:")
    print(f"  Volume: {volume} cm³")
    print(f"  Material: 6061 Aluminum")
    print(f"  Weight: {weight_g:.2f}g")
    print(f"  Manufacturing: CNC Machining")
    print()
    print(f"Cost Summary:")
    print(f"  Raw Material ({weight_g:.2f}g @ ${price_per_kg:.2f}/kg): ${raw_material_cost:.2f}")
    print(f"  Manufacturing (CNC): ${manufacturing_cost:.2f}")
    print(f"  {'─'*40}")
    print(f"  TOTAL: ${total:.2f}")
    
    return {
        'volume_cm3': volume,
        'weight_g': weight_g,
        'raw_material_cost': raw_material_cost,
        'manufacturing_cost': manufacturing_cost,
        'total': total
    }


async def example_5_currency_conversion():
    """
    Example 5: International pricing with currency conversion
    
    "What's the price of RTX 4070 in EUR?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Currency Conversion")
    print("="*70)
    print("Query: What's the price of RTX 4070 in EUR?")
    print("-"*70)
    
    # Step 1: Get USD price
    print("\nStep 1: Looking up RTX 4070 price (USD)...")
    price_result = await product_tool.execute(product_name="RTX 4070")
    
    if price_result['status'] != 'success':
        print("  ✗ Price lookup failed")
        return
    
    price_usd = price_result['average']
    print(f"  ✓ Average Price: ${price_usd:.2f} USD")
    
    # Step 2: Convert to EUR
    print("\nStep 2: Converting to EUR...")
    conversion_result = await currency_tool.execute(
        amount=price_usd,
        from_currency="USD",
        to_currency="EUR"
    )
    
    price_eur = conversion_result['to_amount']
    exchange_rate = conversion_result['exchange_rate']
    
    print(f"  {conversion_result['calculation']}")
    print(f"\n  ✓ Price in EUR: €{price_eur:.2f}")
    print(f"  Exchange Rate: 1 USD = {exchange_rate:.4f} EUR")
    
    # Summary
    print("\n" + "="*70)
    print("INTERNATIONAL PRICING")
    print("="*70)
    print(f"RTX 4070:")
    print(f"  USA (USD):   ${price_usd:>8.2f}")
    print(f"  EU (EUR):    €{price_eur:>8.2f}")
    
    return {
        'price_usd': price_usd,
        'price_eur': price_eur,
        'exchange_rate': exchange_rate
    }


async def example_6_query_classification():
    """
    Example 6: How the system classifies queries
    
    Shows query analysis before tool calling.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Query Classification")
    print("="*70)
    
    test_queries = [
        "What's the price of RTX 4070 right now?",
        "How much would 87g of Ti-6Al-4V cost?",
        "Estimate the cost to 3D print a 120g stainless steel part",
        "Cost of a 10 cm³ aluminum part including manufacturing",
        "Convert $100 USD to EUR"
    ]
    
    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        print("-" * 70)
        
        classification = QueryClassifier.classify(query)
        
        print(f"  Domains: {classification['domains'] if classification['domains'] else 'None'}")
        print(f"  Concepts: {classification['concepts'] if classification['concepts'] else 'None'}")
        print(f"  Implied Tools: {classification['implied_tools'] if classification['implied_tools'] else 'None'}")


async def main():
    """Run all examples."""
    
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   TOOL-AUGMENTED LLM PRICING SYSTEM - EXAMPLE SCENARIOS         ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    try:
        # Example 1: Simple product pricing
        await example_1_consumer_product_pricing()
        
        # Example 2: Material + weight cost
        await example_2_material_weight_cost()
        
        # Example 3: Manufacturing estimation
        await example_3_manufacturing_cost_estimation()
        
        # Example 4: Volume to cost
        await example_4_volume_to_weight_cost()
        
        # Example 5: Currency conversion
        await example_5_currency_conversion()
        
        # Example 6: Query classification
        await example_6_query_classification()
        
        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70 + "\n")
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
