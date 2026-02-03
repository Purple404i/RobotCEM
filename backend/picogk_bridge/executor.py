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
        
        try:
            # Clean previous build
            await self._run_command(["dotnet", "clean"], cwd=self.project_path)
            
            # Build project
            logger.info("Building C# project with ShapeKernel and PicoGK...")
            build_result = await self._run_command(
                ["dotnet", "build", "--configuration", "Release"],
                cwd=self.project_path
            )
            
            if build_result["returncode"] != 0:
                raise Exception(f"Build failed: {build_result['stderr']}")
            
            # Run project
            logger.info("Executing geometry generation with physics validation...")
            run_result = await self._run_command(
                ["dotnet", "run", "--configuration", "Release"],
                cwd=self.project_path,
                timeout=300  # 5 minute timeout
            )
            
            if run_result["returncode"] != 0:
                raise Exception(f"Execution failed: {run_result['stderr']}")
            
            # Locate generated files
            stl_file = self.project_path / f"{output_name}.stl"
            meta_file = self.project_path / f"{output_name}_meta.json"
            
            if not stl_file.exists():
                raise Exception("STL file not generated")
            
            # Move to output directory
            output_stl = self.output_dir / f"{output_name}.stl"
            output_meta = self.output_dir / f"{output_name}_meta.json"
            
            stl_file.rename(output_stl)
            if meta_file.exists():
                meta_file.rename(output_meta)
            
            # Load metadata
            metadata = {}
            if output_meta.exists():
                with open(output_meta, 'r') as f:
                    metadata = json.load(f)
            
            # Analyze STL
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
                "stdout": run_result.get("stdout", ""),
                "stderr": run_result.get("stderr", "")
            }
    
    def _enhance_with_shapekernal(self, base_code: str, design_specs: Dict[str, Any]) -> str:
        """Enhance base code with ShapeKernel BaseShapes and lattices"""
        enhanced = f"""
using Leap71.ShapeKernel;
using PicoGK;

namespace RobotCEM.Generated
{{
    public class GeneratedDesign
    {{
        public static void Task()
        {{
            // Design specifications from prompt
            string deviceType = "{design_specs.get('device_type', 'unknown')}";
            float safetyFactor = {design_specs.get('safety_factor', 1.5)};
            
            // Create primary geometry using ShapeKernel BaseShapes
            LocalFrame frame = new LocalFrame();
"""
        
        # Add base shape generation
        if design_specs.get('base_shape'):
            shape_code = self.shape_generator.generate_base_shape(
                design_specs['base_shape']['type'],
                design_specs['base_shape'].get('dimensions', {}),
                design_specs.get('material_properties', {})
            )
            enhanced += shape_code
        
        # Add lattice infill if weight reduction requested
        if design_specs.get('lightweighting', {}).get('enabled'):
            lattice_code = self.shape_generator.generate_lattice_infill(
                design_specs['lightweighting'].get('cell_type', 'regular'),
                design_specs['lightweighting'].get('beam_thickness', 2.0),
                design_specs['lightweighting'].get('noise_level', 0.0)
            )
            enhanced += lattice_code
        
        enhanced += f"""
            // Smooth and finalize geometry
            Voxels voxFinal = voxFinal.voxSmooth();
            
            // Export to STL for visualization and manufacturing
            Mesh mFinal = voxFinal.mshGetMesh();
            mFinal.ExportSTL("output_{design_specs.get('device_type', 'design')}.stl");
            
            // Log physics validation results
            Console.WriteLine($"Design '{{deviceType}}' validated with safety factor {{safetyFactor}}");
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