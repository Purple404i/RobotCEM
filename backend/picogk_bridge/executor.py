import subprocess
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PicoGKExecutor:
    def __init__(self, csharp_project_path: str, output_dir: str):
        self.project_path = Path(csharp_project_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def compile_and_run(self, csharp_code: str, output_name: str) -> Dict:
        """Compile and execute C# code, return results"""
        
        logger.info(f"Compiling design: {output_name}")
        
        # Write generated code to file
        code_file = self.project_path / "GeneratedDesign.cs"
        code_file.write_text(csharp_code)
        
        try:
            # Clean previous build
            await self._run_command(["dotnet", "clean"], cwd=self.project_path)
            
            # Build project
            logger.info("Building C# project...")
            build_result = await self._run_command(
                ["dotnet", "build", "--configuration", "Release"],
                cwd=self.project_path
            )
            
            if build_result["returncode"] != 0:
                raise Exception(f"Build failed: {build_result['stderr']}")
            
            # Run project
            logger.info("Executing geometry generation...")
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