"""
RobotCEM PicoGK Bridge - Fixed Executor
Properly integrates with LEAP71 PicoGK for computational engineering
"""

import subprocess
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any
import logging
import shutil

logger = logging.getLogger(__name__)

class ShapeKernelTemplate:
    """Template generator for ShapeKernel-based designs"""
    
    @staticmethod
    def generate_base_shape(shape_type: str, dimensions: Dict[str, float]) -> tuple[str, str]:
        """
        Generate C# code for BaseShape creation
        Returns: (shape_creation_code, voxel_variable_name)
        """
        voxel_name = "voxShape"
        
        shape_code = {
            "box": f"""
                // Create Box using ShapeKernel
                BaseBBox oBBox = new BaseBBox(
                    new LocalFrame(), 
                    {dimensions.get('length', 10)}f, 
                    {dimensions.get('width', 10)}f, 
                    {dimensions.get('height', 10)}f
                );
                Voxels {voxel_name} = oBBox.voxConstruct();
                Library.Log($"Created box: {{oBBox.fLengthX}}x{{oBBox.fLengthY}}x{{oBBox.fLengthZ}} mm");
""",
            "sphere": f"""
                // Create Sphere using ShapeKernel
                BaseSphere oSphere = new BaseSphere(
                    new LocalFrame(), 
                    {dimensions.get('radius', 10)}f
                );
                Voxels {voxel_name} = oSphere.voxConstruct();
                Library.Log($"Created sphere with radius {{oSphere.fRadius}} mm");
""",
            "cylinder": f"""
                // Create Cylinder using ShapeKernel
                BaseCylinder oCylinder = new BaseCylinder(
                    new LocalFrame(), 
                    {dimensions.get('radius', 5)}f, 
                    {dimensions.get('height', 20)}f
                );
                Voxels {voxel_name} = oCylinder.voxConstruct();
                Library.Log($"Created cylinder: radius {{oCylinder.fRadius}} mm, height {{oCylinder.fHeight}} mm");
""",
            "pipe": f"""
                // Create Pipe using ShapeKernel
                BasePipe oPipe = new BasePipe(
                    new LocalFrame(), 
                    {dimensions.get('outer_radius', 10)}f, 
                    {dimensions.get('inner_radius', 5)}f, 
                    {dimensions.get('height', 30)}f
                );
                Voxels {voxel_name} = oPipe.voxConstruct();
                Library.Log($"Created pipe: outer {{oPipe.fOuterRadius}} mm, inner {{oPipe.fInnerRadius}} mm");
""",
            "lens": f"""
                // Create Lens using ShapeKernel
                BaseLens oLens = new BaseLens(
                    new LocalFrame(), 
                    {dimensions.get('radius', 15)}f, 
                    {dimensions.get('thickness', 5)}f
                );
                Voxels {voxel_name} = oLens.voxConstruct();
                Library.Log($"Created lens: radius {{oLens.fRadius}} mm, thickness {{oLens.fThickness}} mm");
"""
        }
        
        return shape_code.get(shape_type, shape_code["box"]), voxel_name

    @staticmethod
    def generate_lattice_infill(base_voxel: str, beam_thickness: float, 
                                cell_size: int = 20, lattice_type: str = "BodyCentered") -> str:
        """Generate lattice infill code for lightweighting"""
        
        lattice_types = {
            "BodyCentered": "new BodyCenteredLattice()",
            "FaceCentered": "new FaceCenteredLattice()",
            "Simple": "new SimpleLattice()"
        }
        
        lattice_constructor = lattice_types.get(lattice_type, lattice_types["BodyCentered"])
        
        return f"""
                // Apply lattice infill for weight reduction
                Library.Log("Applying {lattice_type} lattice with beam thickness {beam_thickness}mm");
                
                ICellArray xCellArray = new RegularCellArray({base_voxel}, {cell_size}, {cell_size}, {cell_size});
                ILatticeType xLatticeType = {lattice_constructor};
                IBeamThickness xBeamThickness = new ConstantBeamThickness({beam_thickness}f);
                xBeamThickness.SetBoundingVoxels({base_voxel});

                uint nSubSample = 5;
                Voxels voxLattice = voxGetFinalLatticeGeometry(
                    xCellArray,
                    xLatticeType,
                    xBeamThickness,
                    nSubSample);

                // Boolean intersection to combine lattice with base shape
                Voxels voxFinal = {base_voxel} & voxLattice;
                Library.Log("Lattice infill applied successfully");
"""


class PicoGKExecutor:
    """
    Executor for running PicoGK computational engineering models
    Operates in headless mode for web integration
    """
    
    def __init__(self, csharp_project_path: str, output_dir: str):
        self.project_path = Path(csharp_project_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shape_generator = ShapeKernelTemplate()
        
        # Verify PicoGK installation
        self._verify_picogk()
    
    def _verify_picogk(self):
        """Verify that PicoGK runtime is available"""
        csproj_file = self.project_path / "RobotCEM.csproj"
        if not csproj_file.exists():
            logger.warning(f"Project file not found: {csproj_file}")
    
    async def compile_and_run(
        self, 
        csharp_code: str, 
        output_name: str,
        design_specs: Dict[str, Any] = None
    ) -> Dict:
        """
        Compile and execute C# code with PicoGK/ShapeKernel
        Runs in headless mode, exports STL for web visualization
        """
        
        logger.info(f"Starting PicoGK design generation: {output_name}")
        
        # Generate enhanced code if design specs provided
        if design_specs:
            csharp_code = self._generate_picogk_code(design_specs, output_name)
        
        # Write generated code
        code_file = self.project_path / "GeneratedDesign.cs"
        code_file.write_text(csharp_code)
        logger.info(f"Generated code written to: {code_file}")
        
        build_result = None
        run_result = None
        
        try:
            # Clean previous build
            logger.info("Cleaning previous build...")
            await self._run_command(["dotnet", "clean"], cwd=self.project_path)
            
            # Build project
            logger.info("Building C# project...")
            build_result = await self._run_command(
                ["dotnet", "build", "--configuration", "Release"],
                cwd=self.project_path
            )
            
            # Log build output
            build_log = self.output_dir / "build.log"
            with open(build_log, 'w') as f:
                f.write("=== BUILD OUTPUT ===\n")
                f.write(build_result["stdout"])
                if build_result["stderr"]:
                    f.write("\n\n=== BUILD ERRORS ===\n")
                    f.write(build_result["stderr"])
            
            if build_result["returncode"] != 0:
                error_lines = self._extract_errors(build_result)
                raise Exception(f"Build failed. See {build_log}\n{error_lines}")
            
            logger.info("Build successful!")
            
            # Run project in headless mode
            logger.info("Executing geometry generation (headless mode)...")
            run_result = await self._run_command(
                ["dotnet", "run", "--configuration", "Release", "--no-build", "--", "--headless"],
                cwd=self.project_path,
                timeout=300
            )
            
            # Log execution output
            exec_log = self.output_dir / "execution.log"
            with open(exec_log, 'w') as f:
                f.write(run_result["stdout"])
                if run_result["stderr"]:
                    f.write("\n\n=== EXECUTION ERRORS ===\n")
                    f.write(run_result["stderr"])
            
            if run_result["returncode"] != 0:
                error_msg = run_result["stderr"] or run_result["stdout"] or "Unknown error"
                raise Exception(f"Execution failed: {error_msg}")
            
            # Locate and move generated files
            stl_files = list(self.project_path.glob("*.stl"))
            if not stl_files:
                raise Exception(f"No STL files generated")
            
            output_stl = self.output_dir / f"{output_name}.stl"
            shutil.move(str(stl_files[0]), str(output_stl))
            logger.info(f"STL file moved to: {output_stl}")
            
            # Load metadata if available
            metadata = self._load_metadata(output_name)
            
            # Analyze STL
            density = design_specs.get("material_density_g_cm3", 1.25) if design_specs else 1.25
            stl_analysis = await self._analyze_stl(output_stl, density=density)
            
            return {
                "success": True,
                "stl_path": str(output_stl),
                "metadata": metadata,
                "analysis": stl_analysis,
                "stdout": run_result["stdout"],
                "build_time": run_result.get("duration", 0)
            }
            
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "stdout": run_result.get("stdout", "") if run_result else "",
                "stderr": run_result.get("stderr", "") if run_result else ""
            }
    
    def _generate_picogk_code(self, design_specs: Dict[str, Any], output_name: str) -> str:
        """Generate complete PicoGK C# code from design specifications"""
        
        device_type = design_specs.get('device_type', 'unknown')
        safety_factor = design_specs.get('safety_factor', 1.5)
        
        # Generate base shape
        base_shape_spec = design_specs.get('base_shape', {})
        shape_type = base_shape_spec.get('type', 'box')
        dimensions = base_shape_spec.get('dimensions', {})
        
        shape_code, voxel_name = self.shape_generator.generate_base_shape(
            shape_type, dimensions
        )
        
        # Generate lattice if requested
        lattice_code = ""
        final_voxel = voxel_name
        
        if design_specs.get('lightweighting', {}).get('enabled'):
            beam_thickness = design_specs['lightweighting'].get('beam_thickness', 2.0)
            cell_size = design_specs['lightweighting'].get('cell_size', 20)
            lattice_type = design_specs['lightweighting'].get('type', 'BodyCentered')
            
            lattice_code = self.shape_generator.generate_lattice_infill(
                voxel_name, beam_thickness, cell_size, lattice_type
            )
            final_voxel = "voxFinal"
        
        # Generate complete C# code
        code = f"""using Leap71.ShapeKernel;
using Leap71.LatticeLibrary;
using PicoGK;
using System;
using System.IO;
using System.Numerics;

namespace RobotCEM.Generated
{{
    public class GeneratedDesign
    {{
        public static void Task()
        {{
            try
            {{
                Library.Log("╔════════════════════════════════════════╗");
                Library.Log("║   RobotCEM Design Generation Started  ║");
                Library.Log("╚════════════════════════════════════════╝");
                
                // Design parameters
                string deviceType = "{device_type}";
                float safetyFactor = {safety_factor}f;
                
                Library.Log($"Device Type: {{deviceType}}");
                Library.Log($"Safety Factor: {{safetyFactor}}");
                Library.Log($"Voxel Size: {{Library.fVoxelSizeMM}}mm");
                
{shape_code}
{lattice_code}
                // Convert to mesh
                Library.Log("Converting voxels to triangulated mesh...");
                Mesh msh = new Mesh({final_voxel});
                
                Library.Log($"Mesh statistics:");
                Library.Log($"  - Triangles: {{msh.nTriangleCount()}}");
                Library.Log($"  - Vertices: {{msh.nVertexCount()}}");
                
                // Export STL
                string outputPath = Path.Combine(Library.strLogFolder, "{output_name}.stl");
                Library.Log($"Saving to: {{outputPath}}");
                msh.SaveToStlFile(outputPath);
                
                // Export metadata
                var metadata = new
                {{
                    DeviceType = deviceType,
                    SafetyFactor = safetyFactor,
                    VoxelSize = Library.fVoxelSizeMM,
                    Triangles = msh.nTriangleCount(),
                    Vertices = msh.nVertexCount(),
                    Timestamp = DateTime.Now.ToString("O")
                }};
                
                string metaPath = Path.Combine(Library.strLogFolder, "{output_name}_meta.json");
                File.WriteAllText(metaPath, System.Text.Json.JsonSerializer.Serialize(metadata, 
                    new System.Text.Json.JsonSerializerOptions {{ WriteIndented = true }}));
                
                Library.Log("╔════════════════════════════════════════╗");
                Library.Log("║     Generation Completed Successfully  ║");
                Library.Log("╚════════════════════════════════════════╝");
                
                // Add to viewer if not headless
                if (!Library.bHeadlessMode)
                {{
                    Library.oViewer().Add({final_voxel});
                }}
            }}
            catch (Exception ex)
            {{
                Library.Log($"ERROR: {{ex.Message}}");
                Library.Log(ex.StackTrace);
                if (!Library.bHeadlessMode)
                {{
                    Library.oViewer().SetBackgroundColor(Cp.clrWarning);
                }}
                throw;
            }}
        }}
    }}
}}
"""
        return code
    
    def _extract_errors(self, build_result: Dict) -> str:
        """Extract error messages from build output"""
        full_output = build_result["stdout"] + build_result["stderr"]
        error_lines = []
        
        for line in full_output.split('\n'):
            if any(x in line for x in ['error CS', 'error:', 'Error:', 'Cannot find']):
                error_lines.append(line)
        
        return '\n'.join(error_lines[-20:]) if error_lines else full_output[-1000:]
    
    def _load_metadata(self, output_name: str) -> Dict:
        """Load metadata JSON if available"""
        meta_file = self.project_path / f"{output_name}_meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r') as f:
                    return json.load(f)
            finally:
                meta_file.unlink()
        return {}
    
    async def _run_command(
        self,
        cmd: list,
        cwd: Path,
        timeout: Optional[int] = None
    ) -> Dict:
        """Run shell command asynchronously"""
        
        import time
        start_time = time.time()
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "duration": duration
            }
            
        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"Command timed out after {timeout}s")
    
    async def _analyze_stl(self, stl_path: Path, density: float = 1.25) -> Dict:
        """Analyze STL file properties using trimesh"""
        
        try:
            import trimesh
            
            mesh = trimesh.load(str(stl_path))
            
            bounds = mesh.bounds
            dimensions = bounds[1] - bounds[0]
            volume_cm3 = float(mesh.volume / 1000)
            mass_g = volume_cm3 * density
            
            return {
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "volume_mm3": float(mesh.volume),
                "volume_cm3": volume_cm3,
                "mass_g": mass_g,
                "surface_area_mm2": float(mesh.area),
                "bounds": {
                    "min": bounds[0].tolist(),
                    "max": bounds[1].tolist()
                },
                "dimensions_mm": dimensions.tolist(),
                "is_watertight": bool(mesh.is_watertight),
                "is_valid": bool(mesh.is_valid),
                "center_of_mass": mesh.center_mass.tolist() if hasattr(mesh, 'center_mass') else [0, 0, 0],
                "moment_of_inertia": mesh.moment_inertia.tolist() if hasattr(mesh, 'moment_inertia') else []
            }
            
        except Exception as e:
            logger.warning(f"STL analysis failed: {e}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        executor = PicoGKExecutor(
            csharp_project_path="./csharp_runtime/submodules",
            output_dir="./outputs"
        )
        
        design_specs = {
            'device_type': 'test_component',
            'safety_factor': 1.5,
            'base_shape': {
                'type': 'sphere',
                'dimensions': {'radius': 15}
            },
            'lightweighting': {
                'enabled': True,
                'beam_thickness': 2.0,
                'cell_size': 20,
                'type': 'BodyCentered'
            }
        }
        
        result = await executor.compile_and_run(
            csharp_code="",
            output_name="test_design",
            design_specs=design_specs
        )
        
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())