#!/usr/bin/env python3
"""
Example: Complete CEM Workflow with PicoGK Integration
Demonstrates the full pipeline from natural language to 3D manufacturing
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def example_motor_housing():
    """
    Example 1: Design a lightweight motor housing
    
    Workflow:
    1. Parse natural language requirement
    2. Source components (bearings, fasteners)
    3. Recommend ShapeKernel base shape
    4. Calculate lattice parameters for 30% weight reduction
    5. Validate physics
    6. Generate and simulate with PicoGK
    7. Export BOM with costs
    """
    
    from backend.cem_engine.orchestrator import EngineOrchestrator
    
    # Initialize orchestrator
    orchestrator = EngineOrchestrator(
        hf_model_name="gpt2",
        csharp_project_path="/home/devlord/RobotCEM/csharp_runtime/RobotCEM",
        output_dir="/home/devlord/RobotCEM/backend/outputs"
    )
    
    # Natural language prompt
    prompt = """
    Design a motor housing for a 50W electric motor:
    - Main body dimensions: 150mm length, 100mm width, 80mm height
    - Material: Aluminum 6061 (for thermal management)
    - Manufacturing: CNC machining
    - Mounting: 4x M6 bolt holes on each side
    - Cooling fins: 2mm thick, 10mm spacing
    - Weight budget: minimize weight (target 30% reduction vs solid)
    - Environment: industrial, temperature -10°C to +60°C
    - Cost budget: $200 per unit
    """
    
    logger.info("=" * 80)
    logger.info("EXAMPLE 1: Motor Housing Design")
    logger.info("=" * 80)
    logger.info(f"Prompt: {prompt}")
    
    # Run complete workflow
    result = await orchestrator.run_from_prompt(prompt, output_name="motor_housing")
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("WORKFLOW RESULTS")
    logger.info("=" * 80)
    
    if result.get("sourcing_summary"):
        logger.info(f"\n✓ Component Sourcing:")
        logger.info(f"  - Components Found: {result['sourcing_summary']['components_found']}")
        logger.info(f"  - With Alternatives: {result['sourcing_summary']['components_with_alternatives']}")
        logger.info(f"  - Total Cost: ${result['sourcing_summary']['total_component_cost']:.2f}")
    
    if result.get("spec", {}).get("base_shape"):
        logger.info(f"\n✓ ShapeKernel Recommendation:")
        logger.info(f"  - Base Shape: {result['spec']['base_shape']['shape']}")
        logger.info(f"  - Dimensions: {result['spec']['base_shape']['dimensions']}")
    
    if result.get("spec", {}).get("lightweighting"):
        logger.info(f"\n✓ Lightweight Optimization:")
        logger.info(f"  - Enabled: True")
        logger.info(f"  - Beam Thickness: {result['spec']['lightweighting']['beam_thickness']} mm")
        logger.info(f"  - Cell Type: {result['spec']['lightweighting']['cell_type']}")
    
    if result.get("validation"):
        val = result["validation"]
        logger.info(f"\n✓ Physics Validation:")
        logger.info(f"  - Structural: {'PASS' if val.get('structural_valid') else 'FAIL'}")
        logger.info(f"  - Thermal: {'PASS' if val.get('thermal_valid') else 'FAIL'}")
        logger.info(f"  - Manufacturing: {'PASS' if val.get('manufacturing_valid') else 'FAIL'}")
    
    if result.get("generation", {}).get("success"):
        logger.info(f"\n✓ PicoGK Execution:")
        logger.info(f"  - Status: SUCCESS")
        logger.info(f"  - Generated STL: motor_housing.stl")
    
    if result.get("bom"):
        logger.info(f"\n✓ Bill of Materials:")
        logger.info(f"  - Components: {len(result['bom'].get('components', []))}")
        logger.info(f"  - Total Cost: ${result['bom'].get('total_cost', 0):.2f}")
    
    return result

async def example_lattice_infill():
    """
    Example 2: Design lattice-infilled bracket
    
    Demonstrates:
    - Conformal lattice adaptation to complex shapes
    - Stress-optimized beam thickness gradients
    - Multi-body Boolean operations
    """
    
    from backend.cem_engine.orchestrator import EngineOrchestrator
    
    orchestrator = EngineOrchestrator(
        csharp_project_path="/home/devlord/RobotCEM/csharp_runtime/RobotCEM",
        output_dir="/home/devlord/RobotCEM/backend/outputs",
    )
    
    prompt = """
    Design a support bracket with integrated lattice structure:
    - Main box: 80mm x 60mm x 40mm
    - Material: 3D printed Nylon (FDM)
    - Load: 100N vertical compression
    - Optimization: Minimize weight while maintaining stiffness
    - Lattice type: Conformal (adapts to shape)
    - Beam gradient: Thicker near supports, thinner at free ends
    """
    
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 2: Conformal Lattice Bracket")
    logger.info("=" * 80)
    
    result = await orchestrator.run_from_prompt(prompt, output_name="lattice_bracket")
    
    logger.info("\n✓ Design Parameters:")
    if result.get("spec", {}).get("lightweighting"):
        lw = result["spec"]["lightweighting"]
        logger.info(f"  - Cell Type: {lw.get('cell_type')} (conformal)")
        logger.info(f"  - Conformal: {lw.get('conformal')}")
        logger.info(f"  - Noise Level: {lw.get('noise_level')} (for vibration damping)")
    
    return result

async def example_component_sourcing():
    """
    Example 3: Demonstrate component sourcing workflow
    
    Workflow:
    1. Search local database
    2. If not found → search online marketplaces
    3. Check prices and availability
    4. Suggest alternatives if budget exceeded
    5. Add new components to database
    """
    
    from backend.storage.database import ComponentSourcingEngine
    
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 3: Component Sourcing")
    logger.info("=" * 80)
    
    sourcing = ComponentSourcingEngine()
    
    # Example parts to source
    parts_to_source = [
        {
            "name": "Deep Groove Ball Bearing",
            "specs": {
                "category": "bearings",
                "bore_diameter": 10,
                "outer_diameter": 26,
                "width": 8,
            },
            "budget": 15.0
        },
        {
            "name": "Stepper Motor",
            "specs": {
                "category": "motors",
                "power": 5,  # watts
                "torque": 0.5,  # Nm
                "voltage": 12,  # volts
            },
            "budget": 25.0
        },
    ]
    
    for part_spec in parts_to_source:
        logger.info(f"\nSourcing: {part_spec['name']}")
        logger.info(f"  Budget: ${part_spec['budget']}")
        
        component, result = await sourcing.find_component(
            part_spec["name"],
            part_spec["specs"],
            budget=part_spec["budget"]
        )
        
        logger.info(f"  Result: {result['status']}")
        
        if component:
            logger.info(f"  ✓ Found: {component.name}")
            logger.info(f"    Supplier: {component.supplier}")
            logger.info(f"    Price: ${component.price:.2f}")
            logger.info(f"    Lead time: {component.lead_time_days} days")
        elif result.get("alternatives"):
            logger.info(f"  ⚠ Alternatives available:")
            for alt in result["alternatives"][:2]:
                logger.info(f"    - {alt['name']}")
                logger.info(f"      Similarity: {alt['similarity']*100:.0f}%")
                if alt.get('improvements'):
                    logger.info(f"      Improvements: {', '.join(alt['improvements'])}")

async def example_multi_component_assembly():
    """
    Example 4: Assembly of multiple components using Boolean operations
    
    Creates complex geometry by combining:
    - Main housing (box)
    - Motor mount (cylinder)
    - Bearing supports (rings)
    - Cable glands (pipes)
    """
    
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 4: Multi-Component Assembly")
    logger.info("=" * 80)
    
    from backend.cem_engine.template_generator import TemplateBuilder
    
    # Create design specification
    design_spec = {
        "device_type": "motor_assembly",
        "base_shape": {
            "type": "box",
            "name": "Housing",
            "dimensions": {
                "length": 150,
                "width": 100,
                "height": 80
            }
        },
        "lightweighting": {
            "enabled": True,
            "type": "regular",
            "cell_size": 20,
            "beam_thickness": 2.5,
            "subsampling": 5
        },
        "material": {
            "density": 2.7,  # Aluminum
            "tensile_strength": 310,
        },
        "output_name": "motor_assembly.stl"
    }
    
    # Build C# code from templates
    builder = TemplateBuilder()
    csharp_code = builder.build_complete_design(design_spec)
    
    logger.info("\n✓ Generated C# Code (excerpt):")
    logger.info(csharp_code[:500] + "...")
    logger.info(f"\nTotal code length: {len(csharp_code)} characters")
    
    return csharp_code

async def main():
    """Run all examples"""
    
    logger.info("\n" + "=" * 80)
    logger.info("RobotCEM - PicoGK Integration Examples")
    logger.info("=" * 80)
    logger.info("This demonstrates the complete computational engineering workflow")
    logger.info("using PicoGK, ShapeKernel, and LatticeLibrary")
    
    try:
        # Example 3: Component sourcing (works without C# setup)
        await example_component_sourcing()
        
        # Example 4: Template generation (works standalone)
        await example_multi_component_assembly()
        
        # Examples 1 & 2 require C# project setup
        # Uncomment when csharp_runtime is configured:
        # await example_motor_housing()
        # await example_lattice_infill()
        
        logger.info("\n" + "=" * 80)
        logger.info("Examples completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
