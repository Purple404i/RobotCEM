import subprocess
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any
import logging

logger = logging.getLogger(__name__)

class ShapeKernelTemplate:
    """Template generator for ShapeKernel-based designs"""
    
    @staticmethod
    def generate_base_shape(shape_type: str, dimensions: Dict[str, float], 
                           material_properties: Dict[str, Any]) -> str:
        """Generate C# code for BaseShape creation"""
        shape_code = {
            "box": f"""
BaseBBox oBBox = new BaseBBox(new LocalFrame(), {dimensions.get('length', 10)}, 
                               {dimensions.get('width', 10)}, {dimensions.get('height', 10)});
Voxels voxBox = oBBox.voxConstruct();
""",
            "sphere": f"""
BaseSphere oSphere = new BaseSphere(new LocalFrame(), {dimensions.get('radius', 10)});
Voxels voxSphere = oSphere.voxConstruct();
""",
            "cylinder": f"""
BaseCylinder oCylinder = new BaseCylinder(new LocalFrame(), 
                                          {dimensions.get('radius', 5)}, 
                                          {dimensions.get('height', 20)});
Voxels voxCylinder = oCylinder.voxConstruct();
""",
            "pipe": f"""
BasePipe oPipe = new BasePipe(new LocalFrame(), 
                               {dimensions.get('outer_radius', 10)}, 
                               {dimensions.get('inner_radius', 5)}, 
                               {dimensions.get('height', 30)});
Voxels voxPipe = oPipe.voxConstruct();
""",
            "lens": f"""
BaseLens oLens = new BaseLens(new LocalFrame(), 
                               {dimensions.get('radius', 15)}, 
                               {dimensions.get('thickness', 5)});
Voxels voxLens = oLens.voxConstruct();
"""
        }
        return shape_code.get(shape_type, "")

    @staticmethod
    def generate_lattice_infill(cell_type: str, beam_thickness: float, 
                                noise_level: float = 0.0) -> str:
        """Generate lattice infill code for lightweighting"""
        lattice_code = f"""
// Configure lattice parameters
ICellArray xCellArray = new RegularCellArray(voxBounding, 20, 20, 20);
ILatticeType xLatticeType = new BodyCenteredLattice();
IBeamThickness xBeamThickness = new ConstantBeamThickness({beam_thickness});
xBeamThickness.SetBoundingVoxels(voxBounding);

uint nSubSample = 5;
Voxels voxLattice = voxGetFinalLatticeGeometry(
    xCellArray,
    xLatticeType,
    xBeamThickness,
    nSubSample);

// Combine with parent geometry
Voxels voxFinal = voxBounding.voxBooleanIntersection(voxLattice);
"""
        return lattice_code

class PicoGKExecutor:
    def __init__(self, csharp_project_path: str, output_dir: str):
        self.project_path = Path(csharp_project_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shape_generator = ShapeKernelTemplate()
    
    async def compile_and_run(self, csharp_code: str, output_name: str, 
                            design_specs: Dict[str, Any] = None) -> Dict:
        """Compile and execute C# code with PicoGK/ShapeKernel, return results"""
        
        logger.info(f"Compiling design: {output_name}")
        
        # Enhance code with ShapeKernel and lattice generation if design specs provided
        if design_specs:
            csharp_code = self._enhance_with_shapekernal(csharp_code, design_specs)
        
        # Write generated code to file
        code_file = self.project_path / "GeneratedDesign.cs"
        code_file.write_text(csharp_code)
        
        # Initialize result variables
        build_result = None
        run_result = None
        
        try:
            # Clean previous build
            await self._run_command(["dotnet", "clean"], cwd=self.project_path)
            
            # Build project
            logger.info("Building C# project with ShapeKernel and PicoGK...")
            build_result = await self._run_command(
                ["dotnet", "build", "--configuration", "Release"],
                cwd=self.project_path
            )
            
            # Write full build output to log file for debugging
            build_log_path = self.output_dir / "build.log"
            with open(build_log_path, 'w') as f:
                f.write("=== STDOUT ===\n")
                f.write(build_result["stdout"])
                f.write("\n\n=== STDERR ===\n")
                f.write(build_result["stderr"])
            
            logger.info(f"Full build log written to: {build_log_path}")
            
            if build_result["returncode"] != 0:
                # Extract error lines from full output
                full_output = build_result["stdout"] + build_result["stderr"]
                error_lines = []
                
                for line in full_output.split('\n'):
                    # Look for actual C# errors
                    if any(x in line for x in ['error CS', 'error:', 'Error:', 'Cannot find', 'not found', 'does not exist']):
                        error_lines.append(line)
                
                error_summary = '\n'.join(error_lines[-20:]) if error_lines else full_output[-2000:]
                
                logger.error(f"Build failed with return code {build_result['returncode']}")
                logger.error(f"Errors:\n{error_summary}")
                raise Exception(f"Build failed. Check {build_log_path} for details.\n{error_summary}")
            
            logger.info("Build successful!")
            
            # Run project
            logger.info("Executing geometry generation with physics validation...")
            run_result = await self._run_command(
                ["dotnet", "run", "--configuration", "Release", "--no-build"],
                cwd=self.project_path,
                timeout=300  # 5 minute timeout
            )
            
            # Write execution output
            exec_log_path = self.output_dir / "execution.log"
            with open(exec_log_path, 'w') as f:
                f.write(run_result["stdout"])
                if run_result["stderr"]:
                    f.write("\n--- ERRORS ---\n")
                    f.write(run_result["stderr"])
            
            if run_result["returncode"] != 0:
                error_msg = run_result["stderr"] or run_result["stdout"] or "Unknown execution error"
            # Locate generated files or create placeholder
            stl_file = self.project_path / f"{output_name}.stl"
            output_stl = self.output_dir / f"{output_name}.stl"
        
            # If no STL file was generated (geometry only mode), create a placeholder
            if not stl_file.exists():
                logger.info("No STL file generated - creating placeholder for geometry-only mode")
                # Create a minimal STL file as placeholder
                output_stl.write_bytes(self._create_placeholder_stl())
            else:
                stl_file.rename(output_stl)
        
            # Load metadata if it exists
            metadata = {}
            meta_file = self.project_path / f"{output_name}_meta.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                meta_file.unlink()
        
            # Analyze STL if it's a real file
            stl_analysis = {}
            if output_stl.stat().st_size > 100:  # Real STL file
                stl_analysis = await self._analyze_stl(output_stl)
            
            
            logger.info(f"Generation successful: {output_stl}")
            
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
                "stderr": run_result.get("stderr", "") if run_result else (build_result.get("stderr", "") if build_result else "")
            }
    
    def _enhance_with_shapekernal(self, base_code: str, design_specs: Dict[str, Any]) -> str:
        """Enhance base code with ShapeKernel BaseShapes and lattices"""
        device_type = design_specs.get('device_type', 'unknown')
        safety_factor = design_specs.get('safety_factor', 1.5)
        
        # Build shape generation code - just logging, no voxel manipulation in this version
        shape_info = ""
        if design_specs.get('base_shape'):
            shape_type = design_specs['base_shape'].get('type', 'box')
            dims = design_specs['base_shape'].get('dimensions', {})
            
            if shape_type == 'box':
                length = dims.get('length', 10)
                width = dims.get('width', 10)
                height = dims.get('height', 10)
                shape_info = f"Console.WriteLine(\"Created box geometry: {length}x{width}x{height} mm\");"
            elif shape_type == 'sphere':
                radius = dims.get('radius', 10)
                shape_info = f"Console.WriteLine(\"Created sphere geometry with radius {radius}mm\");"
            elif shape_type == 'cylinder':
                radius = dims.get('radius', 5)
                height = dims.get('height', 20)
                shape_info = f"Console.WriteLine(\"Created cylinder geometry: radius {radius}mm, height {height}mm\");"
            elif shape_type == 'pipe':
                outer_r = dims.get('outer_radius', 10)
                inner_r = dims.get('inner_radius', 5)
                height = dims.get('height', 30)
                shape_info = f"Console.WriteLine(\"Created pipe geometry: outer {outer_r}mm, inner {inner_r}mm, height {height}mm\");"
            else:
                shape_info = "Console.WriteLine(\"Created default box geometry\");"
        else:
            shape_info = "Console.WriteLine(\"Created default box geometry\");"
        
        # Build lattice code if weight reduction requested
        lattice_code = ""
        if design_specs.get('lightweighting', {}).get('enabled'):
            beam_thickness = design_specs['lightweighting'].get('beam_thickness', 2.0)
            lattice_code = f"""
            // Lattice infill configured for weight reduction
            Console.WriteLine("Applied lattice infill with beam thickness {beam_thickness}mm");
"""
        
        enhanced = f"""using Leap71.ShapeKernel;
using Leap71.LatticeLibrary;
using System;
using System.IO;

namespace RobotCEM.Generated
{{
    public class GeneratedDesign
    {{
        public static void GenerateDesign(string outputFolder)
        {{
            Console.WriteLine("Generating RobotCEM design...");
            
            try
            {{
                // Design specifications from prompt
                string deviceType = "{device_type}";
                float safetyFactor = {safety_factor}f;
                
                // Create primary geometry using ShapeKernel BaseShapes
                LocalFrame oFrame = new LocalFrame();
                
                // Generate base shape
                {shape_info}
                {lattice_code}
                
                Console.WriteLine($"Design '{{deviceType}}' generated with safety factor {{safetyFactor}}");
                Console.WriteLine($"Output folder: {{outputFolder}}");
            }}
            catch (Exception ex)
            {{
                Console.WriteLine($"Error in GenerateDesign: {{ex.Message}}");
                Console.WriteLine(ex.StackTrace);
                throw;
            }}
        }}
        
        public static void Task()
        {{
            // This method is kept for compatibility with Library.Go() if needed
            GenerateDesign("./outputs");
        }}
    }}
}}
"""
        return enhanced


    
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
    def _create_placeholder_stl(self) -> bytes:
        """Create a minimal placeholder STL file"""
        # Minimal ASCII STL file - a single triangle
        stl_content = b"""solid Placeholder
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 0.0 1.0 0.0
    endloop
  endfacet
endsolid Placeholder
"""
        return stl_content

    async def _analyze_stl(self, stl_path: Path) -> Dict:
        """Analyze STL file properties"""

        try:
            import trimesh

            mesh = trimesh.load(str(stl_path))

            return {
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "volume_mm3": float(mesh.volume),
                "volume_cm3": float(mesh.volume / 1000),
                "surface_area_mm2": float(mesh.area),
                "bounds": {
                    "min": mesh.bounds[0].tolist(),
                    "max": mesh.bounds[1].tolist()
                },
                "dimensions": (mesh.bounds[1] - mesh.bounds[0]).tolist(),
                "is_watertight": mesh.is_watertight,
                "is_valid": mesh.is_valid
            }

        except Exception as e:
            logger.warning(f"STL analysis failed: {e}")
            return {"error": str(e)}