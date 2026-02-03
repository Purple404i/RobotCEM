# RobotCEM Data Flow & Integration Points

## Complete System Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                              │
│  Natural Language Prompt: "Design a motor housing 150mm x 100mm..."      │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      STEP 1: PARSE PROMPT                                │
│  PromptParser → Extract device_type, dimensions, materials, constraints  │
│  Output: DesignSpecification with all parameters                         │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│             STEP 2: COMPONENT SOURCING (New)                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  For each component in spec.components:                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ 2a. Search Local Database                                           │ │
│  │     ↓ Found? → Add to spec.sourced_components                        │ │
│  │     ↓ Not found? → Continue to 2b                                   │ │
│  └────┬────────────────────────────────────────────────────────────────┘ │
│       │                                                                   │
│       ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ 2b. Search Online Marketplaces                                      │ │
│  │     API Calls:                                                       │ │
│  │     - Digi-Key API → Price, Stock, Lead time                        │ │
│  │     - Mouser API → Price, Stock, Lead time                          │ │
│  │     - Alibaba API → Price, Stock, Lead time                         │ │
│  │     - Return: Best match by price/availability                      │ │
│  │     ↓ Found? → Add to database + spec.sourced_components            │ │
│  │     ↓ Not found? → Continue to 2c                                   │ │
│  └────┬────────────────────────────────────────────────────────────────┘ │
│       │                                                                   │
│       ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ 2c. Find Alternatives                                              │ │
│  │     - Search for similar specs                                      │ │
│  │     - Calculate similarity score (0-1)                              │ │
│  │     - Return alternatives with pros/cons                            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  Output: spec.sourced_components, spec.component_costs                   │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│         STEP 3: RECOMMEND SHAPEKERNAL BASE SHAPE (New)                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ShapeKernelAnalyzer.recommend_base_shape(device_type, dimensions)       │
│                                                                           │
│  Mapping Logic:                                                          │
│  - bearing → ring (outer_radius, inner_radius, thickness)               │
│  - housing → box (length, width, height)                                │
│  - connector → cylinder (radius, height)                                │
│  - manifold → pipe (outer_radius, inner_radius, height)                 │
│  - lens → lens (radius, thickness)                                      │
│  - ... (15 categories total)                                            │
│                                                                           │
│  Output: spec.base_shape = {shape, dimensions}                          │
│  Example: {shape: "box", dimensions: {length: 150, width: 100, ...}}    │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│      STEP 4: CALCULATE LATTICE PARAMETERS (New)                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  If optimization_goal == "lightweight":                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ calculate_lattice_parameters(                                     │  │
│  │   volume_reduction_target: 0.3,  // 30% lighter                   │  │
│  │   load_case: {vertical: 100N}    // Load distribution             │  │
│  │ )                                                                 │  │
│  │                                                                   │  │
│  │ Returns:                                                          │  │
│  │ {                                                                 │  │
│  │   "enabled": true,                                                │  │
│  │   "cell_type": "regular",                                         │  │
│  │   "cell_size": 20,                                                │  │
│  │   "beam_thickness": 3.5,    // Calculated from reduction target   │  │
│  │   "conformal": true,                                              │  │
│  │   "noise_level": 0.1                                              │  │
│  │ }                                                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  Output: spec.lightweighting = lattice_params                            │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│      STEP 5: PHYSICS VALIDATION (Existing + Enhanced)                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PhysicsValidator.validate_structural(spec) →                            │
│  ├─ Check stress ≤ yield_strength / safety_factor                        │
│  ├─ Check strain ≤ 0.05 (5%)                                            │
│  ├─ Check FOS (Factor of Safety) ≥ 1.5                                  │
│  └─ Return: {is_valid, errors, warnings}                                │
│                                                                           │
│  PhysicsValidator.validate_thermal(spec) →                               │
│  ├─ Check max_temperature ≤ material.max_temp                            │
│  ├─ Check thermal gradients ≤ limits                                    │
│  └─ Return: {is_valid, errors, warnings}                                │
│                                                                           │
│  PhysicsValidator.validate_manufacturing(spec) →                         │
│  ├─ Check wall_thickness ≥ min_wall (method-specific)                    │
│  ├─ Check overhang_angle ≤ max_angle                                    │
│  ├─ Check hole_diameter ≥ min_hole                                      │
│  └─ Return: {is_valid, errors, warnings}                                │
│                                                                           │
│  If validation fails:                                                    │
│  ├─ propose_fixes() modifies spec                                        │
│  ├─ Retry up to 3 times                                                 │
│  └─ Log all iterations                                                  │
│                                                                           │
│  Output: validation_report with all checks                               │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │ Passed validation?
                       │
         ┌─────────────┴─────────────┐
         │ Yes                       │ No
         ▼                           ▼
  Continue to 6           Auto-fix & Retry Step 5
                          (max 3 iterations)
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│       STEP 6: GENERATE C# CODE (With ShapeKernel)                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  TemplateBuilder.build_complete_design(spec) →                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ using Leap71.ShapeKernel;                                         │  │
│  │ using PicoGK;                                                    │  │
│  │                                                                   │  │
│  │ public class GeneratedDesign {                                    │  │
│  │   public static void Task() {                                     │  │
│  │     // Generate base shape                                        │  │
│  │     BaseBBox oBox = new BaseBBox(...);   // From spec.base_shape  │  │
│  │     Voxels voxBox = oBox.voxConstruct();                          │  │
│  │                                                                   │  │
│  │     // If lightweighting enabled:                                 │  │
│  │     ICellArray xCellArray = new RegularCellArray(...);            │  │
│  │     ILatticeType xLatticeType = new BodyCenteredLattice();        │  │
│  │     IBeamThickness xBeamThickness = new ConstantBeamThickness(..) │  │
│  │     Voxels voxLattice = voxGetFinalLatticeGeometry(...);          │  │
│  │     Voxels voxInfilled = voxBox.voxBooleanIntersection(voxLat);   │  │
│  │                                                                   │  │
│  │     // Smooth and finalize                                        │  │
│  │     Voxels voxFinal = voxInfilled.voxSmooth();                    │  │
│  │                                                                   │  │
│  │     // Export                                                     │  │
│  │     Mesh mFinal = voxFinal.mshGetMesh();                          │  │
│  │     mFinal.ExportSTL("output.stl");                               │  │
│  │   }                                                               │  │
│  │ }                                                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  Output: C# source code ready for compilation                            │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│        STEP 7: EXECUTE PICOGK (Compile & Run)                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PicoGKExecutor.compile_and_run(csharp_code, spec) →                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 1. Write code to GeneratedDesign.cs                              │  │
│  │ 2. dotnet clean                                                  │  │
│  │ 3. dotnet build --configuration Release                          │  │
│  │    ├─ Compiles PicoGK + ShapeKernel + User code                  │  │
│  │    └─ All BaseShapes and LatticeLibrary linked                   │  │
│  │ 4. dotnet run --configuration Release                            │  │
│  │    ├─ Executes generated Task()                                  │  │
│  │    ├─ PicoGK voxelizes geometry                                  │  │
│  │    ├─ ShapeKernel creates BaseShapes                             │  │
│  │    ├─ LatticeLibrary generates beam structures                   │  │
│  │    └─ Exports output_device.stl                                  │  │
│  │ 5. Capture stdout/stderr for analysis                            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  Output: STL file + execution logs + geometry analysis                   │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│       STEP 8: GENERATE BOM & PRICING ANALYSIS                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  MaterialPricingEngine.generate_bom(spec, stl_analysis) →                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ For each sourced_component:                                      │  │
│  │ ├─ component_cost = component.price                              │  │
│  │ ├─ supplier_markup = 1.2x (standard)                             │  │
│  │ └─ assembly_labor = device_complexity * hourly_rate              │  │
│  │                                                                   │  │
│  │ From STL analysis:                                               │  │
│  │ ├─ material_volume = analyze_mesh(stl_file)                      │  │
│  │ ├─ material_mass = material_volume * material_density            │  │
│  │ ├─ material_cost = material_mass * price_per_kg                  │  │
│  │ ├─ manufacturing_time = estimate_from_volume()                   │  │
│  │ └─ manufacturing_cost = machine_time * hourly_rate               │  │
│  │                                                                   │  │
│  │ Final costs:                                                      │  │
│  │ ├─ Components: $X                                                │  │
│  │ ├─ Materials: $Y                                                 │  │
│  │ ├─ Manufacturing: $Z                                             │  │
│  │ ├─ Assembly: $A                                                  │  │
│  │ ├─ Contingency (10%): $C                                         │  │
│  │ └─ Total: $(X+Y+Z+A+C)                                           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  Output: Complete BOM with pricing breakdown                             │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        FINAL OUTPUT                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  result = {                                                              │
│    "spec": {                                                             │
│      "device_type": "motor_housing",                                     │
│      "base_shape": {"shape": "box", ...},                                │
│      "lightweighting": {...},                                            │
│      "sourced_components": [...],                                        │
│      "component_costs": {...}                                            │
│    },                                                                    │
│    "sourcing_summary": {                                                 │
│      "components_found": 5,                                              │
│      "components_with_alternatives": 1,                                  │
│      "total_component_cost": 125.50                                      │
│    },                                                                    │
│    "validation": {                                                       │
│      "structural_valid": true,                                           │
│      "thermal_valid": true,                                              │
│      "manufacturing_valid": true,                                        │
│      "structural": {...},                                                │
│      "thermal": {...},                                                   │
│      "manufacturing": {...}                                              │
│    },                                                                    │
│    "generation": {                                                       │
│      "success": true,                                                    │
│      "stl_file": "motor_housing.stl",                                    │
│      "geometry": {...}                                                   │
│    },                                                                    │
│    "bom": {                                                              │
│      "components": [...],                                                │
│      "material_cost": 45.00,                                             │
│      "manufacturing_cost": 120.00,                                       │
│      "assembly_cost": 50.00,                                             │
│      "total_cost": 340.50                                                │
│    }                                                                     │
│  }                                                                       │
│                                                                           │
│  Files Generated:                                                        │
│  ├─ motor_housing.stl (Mesh for 3D printing/manufacturing)              │
│  ├─ motor_housing_report.json (Complete specification)                  │
│  ├─ motor_housing_bom.csv (Bill of materials)                           │
│  └─ motor_housing_log.txt (Detailed workflow logs)                      │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Parts Database (JSON)

```json
{
  "components": [
    {
      "id": "bearing_608_skf_001",
      "name": "Deep Groove Ball Bearing 608",
      "category": "bearings",
      "manufacturer": "SKF",
      "supplier": "Digi-Key",
      "material": "Chrome Steel",
      "specifications": {
        "bore_diameter": 8,
        "outer_diameter": 22,
        "width": 7,
        "dynamic_load_rating": 480
      },
      "price": 5.50,
      "currency": "USD",
      "last_price_check": "2026-02-02T10:30:00",
      "lead_time_days": 1,
      "stock_availability": "In Stock",
      "datasheet_url": "https://...",
      "compatible_with": ["shaft_8mm", "housing_22mm"]
    }
  ],
  "metadata": {
    "last_updated": "2026-02-02T10:30:00",
    "total_components": 42
  }
}
```

### Design Specification (JSON)

```json
{
  "device_type": "motor_housing",
  "dimensions": {
    "length": 150,
    "width": 100,
    "height": 80
  },
  "loads": {
    "vertical": 100,
    "horizontal": 50
  },
  "material_preferences": ["Aluminum"],
  "manufacturing_method": "CNC_machining",
  "components": [
    {
      "name": "bearing",
      "quantity": 2,
      "specifications": {
        "bore_diameter": 10,
        "outer_diameter": 26
      }
    }
  ],
  "base_shape": {
    "shape": "box",
    "dimensions": {
      "length": 150,
      "width": 100,
      "height": 80
    }
  },
  "lightweighting": {
    "enabled": true,
    "cell_type": "regular",
    "cell_size": 20,
    "beam_thickness": 3.5,
    "subsampling": 5
  },
  "sourced_components": [...],
  "component_costs": {...}
}
```

## Error Handling Flow

```
Design Request
    ↓
[Try Step 1: Parse]
├─ Fail → InvalidPromptError → Return error to user
└─ Success → Continue

[Try Step 2: Source]
├─ Component not found → Add to alternatives list
├─ API timeout → Use cache or mock data
└─ Success → Continue

[Try Step 3-4: Shape & Lattice]
├─ Invalid dimensions → Auto-correct
└─ Success → Continue

[Try Step 5: Validation]
├─ Fails → Auto-fix & retry (up to 3x)
├─ Still fails → Suggest manual fixes + alternatives
└─ Success → Continue

[Try Step 6: Generate C#]
├─ Template error → Log + provide diagnostics
└─ Success → Continue

[Try Step 7: Execute]
├─ Compilation error → Show error line + fix suggestion
├─ Runtime error → Capture stdout + debug info
└─ Success → Continue

[Try Step 8: BOM]
├─ Missing cost data → Use estimates
└─ Success → Return complete result

All failures logged with full context for debugging
```

## Integration Points with Existing Systems

| System | Integration | Data Flow |
|--------|-------------|-----------|
| **Prompt Parser** | Input device requirements | Spec → CEM Engine |
| **Material DB** | Material properties & costs | Used in validation + BOM |
| **Design Rules** | Manufacturing constraints | Used in validation |
| **Pricing Engine** | Component + material costs | BOM generation |
| **Physics Validator** | Stress/thermal checks | Validation loop |
| **PicoGK Bridge** | Geometry generation | STL output |
| **Frontend (future)** | Display results | Show BOM, STL, costs |

---

This complete data flow implements your plan precisely:
✅ Parse natural language
✅ Search database first
✅ Search online market if needed  
✅ Check pricing
✅ Add to database
✅ Recommend shapes
✅ Calculate lattices
✅ Validate physics
✅ Generate 3D geometry
✅ Export manufacturable file + costs
