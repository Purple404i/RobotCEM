# PicoGK & LEAP71 Integration Guide

This document explains how RobotCEM integrates PicoGK and LEAP71 libraries for computational engineering according to the project plan.

## Architecture Overview

RobotCEM follows a 3-layer architecture aligned with LEAP71 software stack:

```
┌─────────────────────────────────────────────────┐
│  Layer 3: Application (CEM Engine)              │
│  - Device specification                          │
│  - Component sourcing                            │
│  - Physics validation                            │
└─────────────────────────────────────────────────┘
              ↓ generates C# code ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: ShapeKernel (High-level APIs)          │
│  - BaseShapes (Box, Sphere, Cylinder, Pipe...)   │
│  - Boolean operations (Union, Intersection)      │
│  - Lattice structures (Conformal, Regular)       │
│  - Smoothing & optimization                      │
└─────────────────────────────────────────────────┘
              ↓ compiles & runs ↓
┌─────────────────────────────────────────────────┐
│  Layer 1: PicoGK (Geometry Kernel)               │
│  - Voxel representation                          │
│  - Mesh export (STL, OBJ)                        │
│  - Physics simulation                            │
│  - Visualization                                 │
└─────────────────────────────────────────────────┘
```

## Key Libraries

### PicoGK
- **Purpose**: Compact geometry kernel for computational engineering
- **Main Operations**:
  - `Voxels`: Voxel-based geometry representation
  - `Mesh`: Convert voxels to mesh for export
  - `Boolean`: Union, Intersection, Subtraction operations
  - `Smoothen()`: Smooth geometry edges
  - `Offset()`: Expand/contract geometry
  - `ExportSTL()`: Export to manufacturing format

### ShapeKernel
- **Purpose**: High-level engineering primitives built on PicoGK
- **BaseShapes**:
  - `BaseBBox`: Rectangular box with dimensions
  - `BaseSphere`: Sphere with radius
  - `BaseCylinder`: Cylinder with radius and height
  - `BasePipe`: Hollow pipe (outer/inner radius)
  - `BaseLens`: Optical lens shape
  - `BaseRing`: Ring/bearing geometry

### LatticeLibrary
- **Purpose**: Beam-based lattice structures for weight optimization
- **Components**:
  - `ICellArray`: Define grid of cells (Regular, Conformal, Random)
  - `ILatticeType`: Connection logic (BodyCentered, Octahedron, Custom)
  - `IBeamThickness`: Gradient-based beam sizing (Constant, Boundary-based, Global)

## Implementation in RobotCEM

### 1. Component Sourcing (Step 2 of workflow)

**File**: `backend/storage/database.py`

```python
# Workflow:
# 1. Search local database for parts
sourcing_engine = ComponentSourcingEngine()
part, result = await sourcing_engine.find_component(
    component_name="bearing",
    specs={"diameter": 20, "bore": 10},
    budget=50.0
)

# 2. If not found → search online marketplace
# 3. Check pricing
# 4. Add new parts to database
# 5. Suggest alternatives if unavailable
```

**Features**:
- Multi-supplier search (Digi-Key, Mouser, Alibaba, etc.)
- Price tracking and comparison
- Lead time management
- Database persistence

### 2. Base Shape Recommendation (Step 3 of workflow)

**File**: `backend/cem_engine/core.py` - `ShapeKernelAnalyzer`

```python
shape_analyzer = ShapeKernelAnalyzer()

# Automatically recommend shape based on device type
recommendation = shape_analyzer.recommend_base_shape(
    device_type="bearing",
    dimensions={"diameter": 30, "bore": 15}
)
# Returns: {"shape": "ring", "dimensions": {...}}

# Or for housing
recommendation = shape_analyzer.recommend_base_shape(
    device_type="housing",
    dimensions={"length": 100, "width": 50, "height": 75}
)
# Returns: {"shape": "box", "dimensions": {...}}
```

### 3. Lattice Generation for Lightweight Design

**File**: `backend/cem_engine/core.py` - `ShapeKernelAnalyzer.calculate_lattice_parameters()`

```python
lattice_params = shape_analyzer.calculate_lattice_parameters(
    volume_reduction_target=0.3,  # 30% weight reduction
    load_case={"vertical": 100}   # Load distribution
)

# Generated parameters:
# {
#   "enabled": true,
#   "cell_type": "regular",
#   "beam_thickness": 3.5,
#   "noise_level": 0.1,
#   "conformal": true
# }
```

### 4. C# Code Generation with ShapeKernel

**File**: `backend/picogk_bridge/executor.py` - `ShapeKernelTemplate`

The executor generates C# code that uses BaseShapes:

```csharp
using Leap71.ShapeKernel;
using PicoGK;

public class GeneratedDesign {
    public static void Task() {
        // Create base geometry
        BaseSphere oSphere = new BaseSphere(new LocalFrame(), 25);
        Voxels voxSphere = oSphere.voxConstruct();
        
        // Apply lattice infill
        ICellArray xCellArray = new RegularCellArray(voxSphere, 20, 20, 20);
        ILatticeType xLatticeType = new BodyCenteredLattice();
        IBeamThickness xBeamThickness = new ConstantBeamThickness(3.5);
        
        Voxels voxLattice = voxGetFinalLatticeGeometry(...);
        
        // Combine and export
        Voxels voxFinal = voxSphere.voxBooleanIntersection(voxLattice);
        Mesh mFinal = voxFinal.voxSmooth().voxGetMesh();
        mFinal.ExportSTL("output_sphere.stl");
    }
}
```

### 5. Physics Validation

**File**: `backend/cem_engine/physics_validator.py`

Validates:
- **Structural**: Stress, strain, factor of safety
- **Thermal**: Heat distribution, thermal gradients
- **Manufacturing**: Wall thickness, overhang angles, support requirements

## Workflow Integration

The complete orchestrator workflow (Step by step):

**File**: `backend/cem_engine/orchestrator.py`

```
User Prompt
    ↓
Step 1: Parse Natural Language
    ↓
Step 2: Source Components (Database → Market → Alternatives)
    ↓
Step 3: Recommend BaseShape (e.g., sphere, box, cylinder)
    ↓
Step 4: Calculate Lattice Parameters (if lightweighting enabled)
    ↓
Step 5: Validate Design (Structural, Thermal, Manufacturing)
    ↓ (repeat if fails)
Step 6: Generate C# Code with ShapeKernel
    ↓
Step 7: Execute PicoGK (Compile & Run)
    ↓
Step 8: Generate BOM with Pricing
    ↓
Output: STL + Report + Cost Analysis
```

## Device Type Mappings

Automatic shape selection based on device type:

| Device Type | Recommended Shape | Parameters | Use Case |
|---|---|---|---|
| **bearing** | Ring | outer_radius, inner_radius | Load distribution, rotational components |
| **connector** | Cylinder | radius, height | Connection interfaces |
| **housing** | Box | length, width, height | Component enclosure |
| **manifold** | Pipe | outer_radius, inner_radius, height | Fluid/gas flow paths |
| **lens** | Lens | radius, thickness | Optical components |
| **junction** | Box | length, width, height | Connection points |

## Manufacturing Methods

Design rules automatically adapt to manufacturing:

- **FDM 3D Printing**: Min wall 0.8mm, supports for >45° overhangs
- **SLA 3D Printing**: Min wall 0.4mm, escape holes required
- **SLS 3D Printing**: Min wall 0.7mm, self-supporting
- **CNC Machining**: Min tool 0.5mm, depth:diameter ratio ≤ 4:1

## Material Database

Built-in materials with properties:

- **Thermoplastics**: PLA, ABS, PETG, Nylon
- **Metals**: Aluminum 6061, Steel 1045, Stainless 316L
- **Composites**: Carbon Fiber, Glass Fiber

Each material includes:
- Density, tensile/yield strength, elastic modulus
- Thermal properties (expansion, max temperature)
- Cost and availability
- Manufacturing compatibility

## Optimization Strategies

### Weight Reduction
Uses LatticeLibrary conformal lattices:
- Regular grid lattices (simple, fast)
- Conformal lattices (adapts to shape)
- Randomized lattices (vibration damping)

### Cost Optimization
- Component sourcing from multiple suppliers
- Material substitution within design rules
- Simplified geometry where precision not critical

### Performance Optimization
- Physics-driven lattice sizing
- Boundary-based beam thickness gradients
- Smooth transitions for stress concentration reduction

## Example: Design a Motor Housing

```python
orchestrator = EngineOrchestrator(
    csharp_project_path="/path/to/csharp_runtime",
    output_dir="backend/outputs"
)

result = await orchestrator.run_from_prompt(
    prompt="Design a motor housing with 100mm diameter, 150mm length, "
           "for 50W motor, 3D printed in PLA, minimize weight by 30%",
    output_name="motor_housing"
)

# Result includes:
# - Sourced components (bearings, fasteners, etc.)
# - Recommended shape: box with mounting bosses
# - Lattice infill enabled
# - Physics validation report
# - Generated STL file
# - Bill of materials with costs
# - Factor of safety calculations
```

## Extending the System

### Add New Device Type
1. Add to `ShapeKernelAnalyzer.recommend_base_shape()` method
2. Define parameters mapping in device type dictionary
3. Specify manufacturing constraints in `DESIGN_RULES`

### Add New Material
1. Add to `MATERIAL_DATABASE` in `backend/cem_engine/material_db.py`
2. Include all mechanical and thermal properties
3. Update manufacturing compatibility rules

### Add New Lattice Type
1. Implement `ILatticeType` interface in LEAP71_LatticeLibrary
2. Add to C# template generator in `ShapeKernelTemplate`
3. Add parameter calculation in `calculate_lattice_parameters()`

## Performance Considerations

- **Voxel Size**: 0.1-1mm (smaller = higher quality but slower)
- **Lattice Cell Size**: 10-50mm (affects detail and computation time)
- **Subsampling**: 2-10 (higher = better beam gradients but slower)

## References

- [PicoGK Documentation](https://picogk.org)
- [LEAP71 ShapeKernel](https://github.com/leap71/LEAP71_ShapeKernel)
- [LEAP71 LatticeLibrary](https://github.com/leap71/LEAP71_LatticeLibrary)
- [Computational Engineering](https://leap71.com/computationalengineering/)
