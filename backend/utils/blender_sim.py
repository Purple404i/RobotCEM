import subprocess
import os
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BlenderSimulator:
    """Interface to run Blender simulations."""

    def __init__(self, blender_path: str = "blender"):
        self.blender_path = blender_path
        self.script_path = Path("scripts/simulate_physics.py")

    async def run_simulation(self, stl_path: str, custom_script_path: Optional[str] = None) -> Dict[str, Any]:
        """Run a physics simulation on the given STL file."""
        if not os.path.exists(stl_path):
            return {"error": f"STL file not found: {stl_path}"}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_json = tmp.name

        try:
            script_to_run = custom_script_path if custom_script_path else str(self.script_path)
            cmd = [
                self.blender_path,
                "--background",
                "--python", script_to_run,
                "--",
                stl_path,
                output_json
            ]

            logger.info(f"Running Blender simulation: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"Blender failed: {stderr.decode()}")
                return {"error": "Blender simulation failed", "details": stderr.decode()}

            if not os.path.exists(output_json):
                return {"error": "Simulation output not generated"}

            with open(output_json, 'r') as f:
                results = json.load(f)

            return results
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return {"error": str(e)}
        finally:
            if os.path.exists(output_json):
                os.unlink(output_json)
