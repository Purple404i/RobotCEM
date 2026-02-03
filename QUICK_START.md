# Quick Start Guide - Using the PicoGK Integration

## Prerequisites

```bash
# Backend dependencies already in requirements.txt:
pip install -r backend/requirements.txt

# Make sure you have:
# - Python 3.8+
# - .NET 6.0+ (for C# runtime)
# - Git (for submodules)
```

## File Structure Reference

```
/home/devlord/RobotCEM/
├── backend/
│   ├── cem_engine/
│   │   ├── core.py              ← NEW: ShapeKernelAnalyzer, PartSpecification
│   │   ├── orchestrator.py       ← ENHANCED: 8-step workflow
│   │   ├── template_generator.py ← NEW: C# code templates
│   │   ├── physics_validator.py  ← Existing physics checks
│   │   └── ...
│   │
│   ├── intelligence/
│   │   └── parts_database.py     ← NEW: Component sourcing
│   │
│   ├── picogk_bridge/
│   │   └── executor.py           ← ENHANCED: ShapeKernel templates
│   │
│   ├── examples/
│   │   └── picogk_examples.py    ← NEW: Working examples
│   │
│   ├── PICOGK_INTEGRATION.md     ← Complete integration guide
│   └── ...
│
├── csharp_runtime/
│   ├── RobotCEM/
│   │   └── Program.cs            ← Calls Task() for designs
│   └── submodules/
│       ├── PicoGK/               ← Geometry kernel
│       ├── LEAP71_ShapeKernel/   ← BaseShapes
│       └── LEAP71_LatticeLibrary/ ← Lattice structures
│
├── IMPLEMENTATION_SUMMARY.md     ← What was built
├── DATA_FLOW.md                 ← Complete workflow diagram
└── ...
```

## Usage Examples

### Example 1: Source a Component from Database

```python
from backend.storage.database import ComponentSourcingEngine
import asyncio

async def find_bearing():
    engine = ComponentSourcingEngine()
    
    # This will:
    # 1. Search local database
    # 2. If not found → search online marketplaces
    # 3. Return best match or alternatives
    part, result = await engine.find_component(
        component_name="Deep Groove Ball Bearing",
        specs={
            "category": "bearings",
            "bore_diameter": 10,
            "outer_diameter": 26
        },
        budget=20.0
    )
    
    if part:
        print(f"Found: {part.name}")
        print(f"Price: ${part.price}")
        print(f"Supplier: {part.supplier}")
```
        print(f"Lead time: {part.lead_time_days} days")
    else:
        print("Alternatives available:")
        for alt in result['alternatives']:
            print(f"  - {alt['name']}")

asyncio.run(find_bearing())
```

### Example 2: Get Shape Recommendation

```python
from backend.cem_engine.core import ShapeKernelAnalyzer

analyzer = ShapeKernelAnalyzer()

# Get recommended base shape for a bearing housing
recommendation = analyzer.recommend_base_shape(
    device_type="housing",
    dimensions={"length": 100, "width": 80, "height": 60}
)

print(f"Recommended shape: {recommendation['shape']}")
print(f"Dimensions: {recommendation['dimensions']}")

# Result:
# Recommended shape: box
# Dimensions: {'length': 100, 'width': 80, 'height': 60}
```

### Example 3: Calculate Lattice Parameters

```python
analyzer = ShapeKernelAnalyzer()

# For 30% weight reduction with load optimization
lattice_params = analyzer.calculate_lattice_parameters(
    volume_reduction_target=0.3,
    load_case={"vertical": 100, "horizontal": 50}  # Forces in Newtons
)

print(f"Lattice enabled: {lattice_params['enabled']}")
print(f"Cell type: {lattice_params['cell_type']}")
print(f"Beam thickness: {lattice_params['beam_thickness']} mm")
print(f"Noise level: {lattice_params['noise_level']} (for vibration damping)")
```

### Example 4: Generate C# Code

```python
from backend.cem_engine.template_generator import TemplateBuilder

builder = TemplateBuilder()

design_spec = {
    "device_type": "motor_housing",
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
        "density": 2.7,  # g/cm³ for Aluminum
    },
    "output_name": "motor_housing.stl"
}

# This generates complete C# code ready to compile
csharp_code = builder.build_complete_design(design_spec)

# Write to file
with open("GeneratedDesign.cs", "w") as f:
    f.write(csharp_code)

print("C# code generated successfully!")
print(f"Total lines: {len(csharp_code.splitlines())}")
```

### Example 5: Complete Workflow (All Steps)

```python
from backend.cem_engine.orchestrator import EngineOrchestrator
import asyncio

async def full_workflow():
    orchestrator = EngineOrchestrator(
        hf_model_name="gpt2",
        csharp_project_path="/home/devlord/RobotCEM/csharp_runtime/RobotCEM",
        output_dir="/home/devlord/RobotCEM/backend/outputs"
    )
    
    # Single natural language prompt
    prompt = """
    Design a pump housing for a 5kW pump:
    - Material: Cast Aluminum (corrosion resistant)
    - Dimensions: 200mm x 150mm x 120mm
    - Ports: 4x inlet/outlet connections
    - Operating temperature: 0°C to 80°C
    - Manufacturing: CNC machining from billet
    - Weight budget: minimize (target 2kg or less)
    - Cost budget: $300 per unit
    """
    
    # Run complete workflow
    result = await orchestrator.run_from_prompt(prompt, output_name="pump_housing")
    
    # Access all results
    print("=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    
    # Step 1-2: Component sourcing
    sourcing = result.get("sourcing_summary", {})
    print(f"\n✓ Sourcing:")
    print(f"  Components found: {sourcing['components_found']}")
    print(f"  Total component cost: ${sourcing['total_component_cost']:.2f}")
    
    # Step 3: Shape recommendation
    base_shape = result.get("spec", {}).get("base_shape", {})
    print(f"\n✓ Geometry:")
    print(f"  Base shape: {base_shape.get('shape')}")
    
    # Step 4: Lattice parameters
    lightweighting = result.get("spec", {}).get("lightweighting", {})
    if lightweighting.get('enabled'):
        print(f"  Lattice: {lightweighting['cell_type']} (enabled)")
        print(f"  Beam thickness: {lightweighting['beam_thickness']} mm")
    
    # Step 5: Physics validation
    validation = result.get("validation", {})
    print(f"\n✓ Validation:")
    print(f"  Structural: {'PASS' if validation['structural_valid'] else 'FAIL'}")
    print(f"  Thermal: {'PASS' if validation['thermal_valid'] else 'FAIL'}")
    print(f"  Manufacturing: {'PASS' if validation['manufacturing_valid'] else 'FAIL'}")
    
    # Step 6-7: Generation & execution
    generation = result.get("generation", {})
    if generation.get("success"):
        print(f"\n✓ Geometry Generated: pump_housing.stl")
    
    # Step 8: BOM
    bom = result.get("bom", {})
    print(f"\n✓ Bill of Materials:")
    print(f"  Components: {len(bom.get('components', []))}")
    print(f"  Material cost: ${bom.get('material_cost', 0):.2f}")
    print(f"  Manufacturing: ${bom.get('manufacturing_cost', 0):.2f}")
    print(f"  Total: ${bom.get('total_cost', 0):.2f}")
    
    return result

result = asyncio.run(full_workflow())
```

## Connecting to Frontend (React)

### API Endpoint Example

```python
# In backend/api/routes.py (add these endpoints)

from fastapi import APIRouter, HTTPException
from backend.cem_engine.orchestrator import EngineOrchestrator

router = APIRouter(prefix="/api/design", tags=["design"])
orchestrator = EngineOrchestrator(...)

@router.post("/generate")
async def generate_design(prompt: str):
    """Generate design from natural language prompt"""
    try:
        result = await orchestrator.run_from_prompt(prompt)
        return {
            "status": "success",
            "spec": result["spec"],
            "sourcing": result["sourcing_summary"],
            "validation": result["validation"],
            "bom": result["bom"],
            "stl_file": "output.stl"  # Path to generated file
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/components/search")
async def search_components(name: str, budget: float = None):
    """Search for components"""
    engine = ComponentSourcingEngine()
    part, result = await engine.find_component(name, {}, budget)
    return result

@router.get("/recommendations/shapes")
async def get_shape_recommendations(device_type: str):
    """Get recommended base shapes"""
    analyzer = ShapeKernelAnalyzer()
    shapes = analyzer.recommend_base_shape(device_type, {})
    return shapes
```

### Frontend Integration Example

```javascript
// React component to show design results

import React, { useState } from 'react';

function DesignGenerator() {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateDesign = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/design/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await response.json();
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea 
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your design..."
      />
      <button onClick={generateDesign} disabled={loading}>
        {loading ? 'Generating...' : 'Generate'}
      </button>

      {result && (
        <div>
          <h3>Results</h3>
          
          {/* Components sourced */}
          <div>
            <h4>Components: {result.sourcing.components_found} found</h4>
            <p>Cost: ${result.sourcing.total_component_cost}</p>
          </div>

          {/* Validation results */}
          <div>
            <h4>Validation</h4>
            <p>Structural: {result.validation.structural_valid ? '✓' : '✗'}</p>
            <p>Thermal: {result.validation.thermal_valid ? '✓' : '✗'}</p>
          </div>

          {/* BOM */}
          <div>
            <h4>Bill of Materials</h4>
            <p>Total Cost: ${result.bom.total_cost}</p>
            <table>
              {/* Show components */}
            </table>
          </div>

          {/* 3D Viewer */}
          <STLViewer file={result.stl_file} />
        </div>
      )}
    </div>
  );
}
```

## Testing

```bash
# Run the examples
cd /home/devlord/RobotCEM
python -m backend.examples.picogk_examples

# Expected output:
# ✓ Component Sourcing Example
# ✓ Multi-Component Assembly Example
# Examples completed successfully!
```

## Common Issues & Solutions

### Issue: "No C# project found"
**Solution:** Set `csharp_project_path` to correct path
```python
orchestrator = EngineOrchestrator(
    csharp_project_path="/home/devlord/RobotCEM/csharp_runtime/RobotCEM"
)
```

### Issue: "ShapeKernel not found"
**Solution:** Make sure submodules are initialized
```bash
cd /home/devlord/RobotCEM/csharp_runtime
git submodule update --init --recursive
```

### Issue: "Component not in database"
**Solution:** This is expected! System will:
1. Search online marketplaces
2. Add to database automatically
3. Return with pricing

### Issue: "Physics validation fails"
**Solution:** The auto-fix loop will try up to 3 times. If it still fails, check the error messages for specific constraint violations.

## Next Steps

1. **Integrate real marketplace APIs** - Replace mock search with actual Digi-Key, Mouser APIs
2. **Add FEA integration** - Connect stress analysis for better optimization
3. **Implement ML training** - Learn from user designs and preferences
4. **Build frontend 3D viewer** - Interactive STL visualization and editing
5. **Extend device types** - Add more device categories and templates

## Architecture Diagram

```
┌─────────────────────────────────┐
│   Frontend (React)              │
│   - Prompt input                │
│   - STL viewer                  │
│   - BOM display                 │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   FastAPI Backend               │
│   - /api/design/generate        │
│   - /api/components/search      │
│   - /api/recommendations/...    │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Orchestrator                  │
│   - Parse → Source → Validate   │
│   - Generate → Execute → BOM    │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   C# Runtime                    │
│   - PicoGK                      │
│   - ShapeKernel                 │
│   - LatticeLibrary              │
│   → STL output                  │
└─────────────────────────────────┘
```

---

**You're ready to start using the PicoGK integration!**

Start with the examples in `backend/examples/picogk_examples.py` to see the complete workflow in action.
