"""
C# Code Generation Templates for ShapeKernel BaseShapes and Assemblies
Generates production-ready code for PicoGK geometry kernel
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseShapeTemplate:
    """Templates for ShapeKernel BaseShape instantiation"""
    
    @staticmethod
    def box(var_name: str, dimensions: Dict[str, float]) -> str:
        """Generate BaseBBox (Box) code"""
        length = dimensions.get("length", 10)
        width = dimensions.get("width", 10)
        height = dimensions.get("height", 10)
        return f"""
BaseBBox {var_name} = new BaseBBox(
    new LocalFrame(), 
    {length}f,  // length (X)
    {width}f,   // width (Y)
    {height}f   // height (Z)
);
Voxels vox{var_name} = {var_name}.voxConstruct();
"""
    
    @staticmethod
    def sphere(var_name: str, dimensions: Dict[str, float]) -> str:
        """Generate BaseSphere code"""
        radius = dimensions.get("radius", 10)
        return f"""
BaseSphere {var_name} = new BaseSphere(
    new LocalFrame(), 
    {radius}f   // radius
);
Voxels vox{var_name} = {var_name}.voxConstruct();
"""
    
    @staticmethod
    def cylinder(var_name: str, dimensions: Dict[str, float]) -> str:
        """Generate BaseCylinder code"""
        radius = dimensions.get("radius", 5)
        height = dimensions.get("height", 20)
        return f"""
BaseCylinder {var_name} = new BaseCylinder(
    new LocalFrame(), 
    {radius}f,   // radius
    {height}f    // height
);
Voxels vox{var_name} = {var_name}.voxConstruct();
"""
    
    @staticmethod
    def pipe(var_name: str, dimensions: Dict[str, float]) -> str:
        """Generate BasePipe (hollow cylinder) code"""
        outer_radius = dimensions.get("outer_radius", 10)
        inner_radius = dimensions.get("inner_radius", 5)
        height = dimensions.get("height", 30)
        return f"""
BasePipe {var_name} = new BasePipe(
    new LocalFrame(), 
    {outer_radius}f,  // outer radius
    {inner_radius}f,  // inner radius
    {height}f         // height
);
Voxels vox{var_name} = {var_name}.voxConstruct();
"""
    
    @staticmethod
    def lens(var_name: str, dimensions: Dict[str, float]) -> str:
        """Generate BaseLens code"""
        radius = dimensions.get("radius", 15)
        thickness = dimensions.get("thickness", 5)
        return f"""
BaseLens {var_name} = new BaseLens(
    new LocalFrame(), 
    {radius}f,      // radius
    {thickness}f    // thickness
);
Voxels vox{var_name} = {var_name}.voxConstruct();
"""
    
    @staticmethod
    def ring(var_name: str, dimensions: Dict[str, float]) -> str:
        """Generate BaseRing code"""
        outer_radius = dimensions.get("outer_radius", 15)
        inner_radius = dimensions.get("inner_radius", 8)
        thickness = dimensions.get("thickness", 2)
        return f"""
BaseRing {var_name} = new BaseRing(
    new LocalFrame(), 
    {outer_radius}f,  // outer radius
    {inner_radius}f,  // inner radius
    {thickness}f      // thickness
);
Voxels vox{var_name} = {var_name}.voxConstruct();
"""

class LatticeTemplate:
    """Templates for LatticeLibrary lattice generation"""
    
    @staticmethod
    def regular_lattice(bounding_shape: str, params: Dict[str, Any]) -> str:
        """Generate regular lattice infill code"""
        cell_size = params.get("cell_size", 20)
        beam_thickness = params.get("beam_thickness", 2.0)
        
        return f"""
// Configure regular lattice structure
ICellArray xCellArray = new RegularCellArray(
    vox{bounding_shape}, 
    {cell_size}, {cell_size}, {cell_size}
);

ILatticeType xLatticeType = new BodyCenteredLattice();

IBeamThickness xBeamThickness = new ConstantBeamThickness({beam_thickness}f);
xBeamThickness.SetBoundingVoxels(vox{bounding_shape});

uint nSubSample = {params.get('subsampling', 5)};
Voxels voxLattice = voxGetFinalLatticeGeometry(
    xCellArray,
    xLatticeType,
    xBeamThickness,
    nSubSample
);

// Combine lattice with bounding shape
Voxels voxInfilled = vox{bounding_shape}.voxBooleanIntersection(voxLattice);
"""
    
    @staticmethod
    def conformal_lattice(bounding_shape: str, params: Dict[str, Any]) -> str:
        """Generate conformal lattice that adapts to shape"""
        cells_per_dim = params.get("cells_per_dim", 10)
        beam_thickness = params.get("beam_thickness", 2.0)
        
        return f"""
// Configure conformal lattice (adapts to shape boundary)
ICellArray xCellArray = new ConformalCellArray(
    vox{bounding_shape},
    {cells_per_dim}  // cells per dimension
);

ILatticeType xLatticeType = new BodyCenteredLattice();

IBeamThickness xBeamThickness = new BoundaryBeamThickness();
xBeamThickness.SetBoundingVoxels(vox{bounding_shape});

uint nSubSample = {params.get('subsampling', 5)};
Voxels voxLattice = voxGetFinalLatticeGeometry(
    xCellArray,
    xLatticeType,
    xBeamThickness,
    nSubSample
);

Voxels voxInfilled = vox{bounding_shape}.voxBooleanIntersection(voxLattice);
"""
    
    @staticmethod
    def gradient_lattice(bounding_shape: str, params: Dict[str, Any]) -> str:
        """Generate lattice with varying beam thickness (stress-optimized)"""
        cell_size = params.get("cell_size", 20)
        min_beam = params.get("min_beam_thickness", 1.5)
        max_beam = params.get("max_beam_thickness", 4.0)
        
        return f"""
// Configure gradient lattice for stress optimization
ICellArray xCellArray = new RegularCellArray(
    vox{bounding_shape}, 
    {cell_size}, {cell_size}, {cell_size}
);

ILatticeType xLatticeType = new BodyCenteredLattice();

// Beam thickness varies based on distance to boundary
IBeamThickness xBeamThickness = new GlobalFuncBeamThickness(
    delegate(Vector3 vPosition) {{
        // Thicker at boundaries, thinner at center
        float fDistance = vox{bounding_shape}.fSignedDistance(vPosition);
        float fNormalized = Math.Min(1.0f, Math.Abs(fDistance) / {max_beam}f);
        return Math.Lerp({min_beam}f, {max_beam}f, fNormalized);
    }}
);
xBeamThickness.SetBoundingVoxels(vox{bounding_shape});

Voxels voxLattice = voxGetFinalLatticeGeometry(
    xCellArray,
    xLatticeType,
    xBeamThickness,
    {params.get('subsampling', 8)}
);

Voxels voxInfilled = vox{bounding_shape}.voxBooleanIntersection(voxLattice);
"""

class AssemblyTemplate:
    """Templates for assembling multiple components"""
    
    @staticmethod
    def boolean_union(shapes: List[str]) -> str:
        """Generate code for combining shapes with Boolean union"""
        if not shapes:
            return ""
        
        code = f"// Combine components using Boolean union\n"
        code += f"Voxels voxAssembly = vox{shapes[0]};\n"
        
        for shape in shapes[1:]:
            code += f"voxAssembly = voxAssembly.voxBooleanUnion(vox{shape});\n"
        
        return code
    
    @staticmethod
    def boolean_intersection(shape1: str, shape2: str) -> str:
        """Generate code for intersection (keep only overlapping parts)"""
        return f"""
// Keep only intersection of two shapes
Voxels voxIntersection = vox{shape1}.voxBooleanIntersection(vox{shape2});
"""
    
    @staticmethod
    def boolean_difference(shape1: str, shape2: str) -> str:
        """Generate code for difference (subtract shape2 from shape1)"""
        return f"""
// Subtract shape from main geometry
Voxels voxResult = vox{shape1}.voxBooleanSubtraction(vox{shape2});
"""
    
    @staticmethod
    def offset_geometry(shape: str, offset_mm: float, operation: str = "expand") -> str:
        """Generate code for expanding or contracting geometry"""
        op_func = "voxOffsetExterior" if operation == "expand" else "voxOffsetInterior"
        return f"""
// Apply {operation} operation (offset by {offset_mm}mm)
Voxels vox{shape}Offset = vox{shape}.{op_func}({offset_mm}f);
"""
    
    @staticmethod
    def smooth_edges(shape: str, iterations: int = 1) -> str:
        """Generate code for smoothing sharp edges"""
        return f"""
// Smooth geometry edges ({iterations} iterations)
Voxels vox{shape}Smooth = vox{shape}.voxSmooth();
""" * iterations

class ExportTemplate:
    """Templates for exporting final geometry"""
    
    @staticmethod
    def export_stl(geometry_var: str, filename: str) -> str:
        """Generate code to export geometry as STL"""
        return f"""
// Convert to mesh and export as STL
Mesh mFinal = {geometry_var}.mshGetMesh();
mFinal.ExportSTL("{filename}");
Console.WriteLine($"Exported: {{Path.GetFullPath(\"{filename}\")}}\");
"""
    
    @staticmethod
    def export_voxel_grid(geometry_var: str, filename: str) -> str:
        """Generate code to export voxel representation"""
        return f"""
// Export voxel grid for analysis
{geometry_var}.ExportVoxelGrid("{filename}");
Console.WriteLine($"Voxel grid exported: {{Path.GetFullPath(\"{filename}\")}}\");
"""

class PhysicsTemplate:
    """Templates for physics analysis"""
    
    @staticmethod
    def analyze_geometry(geometry_var: str, material_props: Dict[str, float]) -> str:
        """Generate code for analyzing physical properties"""
        mass = material_props.get("density", 1.0)
        
        return f"""
// Analyze physical properties
float fVolume = {geometry_var}.fGetVolume();
float fMass = fVolume * {mass}f;  // density in g/cm³
Console.WriteLine($"Volume: {{fVolume}} mm³");
Console.WriteLine($"Mass: {{fMass}} g");

// Analyze bounding box
BBox oBBox = {geometry_var}.oBBox();
Console.WriteLine($"Dimensions: X={{oBBox.fSizeX()}}, Y={{oBBox.fSizeY()}}, Z={{oBBox.fSizeZ()}}\");
"""
    
    @staticmethod
    def stress_analysis_placeholder() -> str:
        """Generate placeholder for stress analysis (requires FEA integration)"""
        return """
// Stress analysis would require FEA integration
// Typical workflow:
// 1. Export mesh to FEA solver
// 2. Apply boundary conditions
// 3. Run simulation
// 4. Import stress results
// 5. Optimize geometry based on stress distribution

Console.WriteLine("Note: Detailed stress analysis requires FEA solver integration");
"""

class TemplateBuilder:
    """High-level template builder combining multiple components"""
    
    def __init__(self):
        self.base_shapes = BaseShapeTemplate()
        self.lattices = LatticeTemplate()
        self.assembly = AssemblyTemplate()
        self.export = ExportTemplate()
        self.physics = PhysicsTemplate()
    
    def build_complete_design(self, design_spec: Dict[str, Any]) -> str:
        """Build complete C# design code from specification"""
        
        code = """using Leap71.ShapeKernel;
using PicoGK;

namespace RobotCEM.Generated
{
    public class GeneratedDesign
    {
        public static void Task()
        {
"""
        
        # Add base shape
        if design_spec.get("base_shape"):
            shape_type = design_spec["base_shape"].get("type", "box")
            shape_name = design_spec["base_shape"].get("name", "Main")
            shape_dims = design_spec["base_shape"].get("dimensions", {})
            
            if shape_type == "box":
                code += self.base_shapes.box(shape_name, shape_dims)
            elif shape_type == "sphere":
                code += self.base_shapes.sphere(shape_name, shape_dims)
            elif shape_type == "cylinder":
                code += self.base_shapes.cylinder(shape_name, shape_dims)
            elif shape_type == "pipe":
                code += self.base_shapes.pipe(shape_name, shape_dims)
            elif shape_type == "lens":
                code += self.base_shapes.lens(shape_name, shape_dims)
            elif shape_type == "ring":
                code += self.base_shapes.ring(shape_name, shape_dims)
        
        # Add lattice infill if enabled
        if design_spec.get("lightweighting", {}).get("enabled"):
            lattice_type = design_spec["lightweighting"].get("type", "regular")
            if lattice_type == "regular":
                code += self.lattices.regular_lattice("Main", design_spec["lightweighting"])
            elif lattice_type == "conformal":
                code += self.lattices.conformal_lattice("Main", design_spec["lightweighting"])
            elif lattice_type == "gradient":
                code += self.lattices.gradient_lattice("Main", design_spec["lightweighting"])
            geometry_var = "voxInfilled"
        else:
            geometry_var = "voxMain"
        
        # Add smoothing
        code += self.assembly.smooth_edges("Main", iterations=1)
        
        # Add physics analysis
        if design_spec.get("material"):
            material_props = design_spec["material"]
            code += self.physics.analyze_geometry(geometry_var, material_props)
        
        # Export to STL
        output_file = design_spec.get("output_name", "output.stl")
        code += self.export.export_stl(geometry_var, output_file)
        
        code += """
        }
    }
}
"""
        return code
