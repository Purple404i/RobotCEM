import subprocess
import os
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

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

    async def render_model(self, stl_path: str, output_image: str) -> Dict[str, Any]:
        """Render a high-quality image of the STL model using Blender."""
        if not os.path.exists(stl_path):
            return {"error": f"STL file not found: {stl_path}"}

        render_script = f"""
import bpy
import sys

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import STL
try:
    bpy.ops.wm.stl_import(filepath={repr(stl_path)})
except AttributeError:
    bpy.ops.import_mesh.stl(filepath={repr(stl_path)})

obj = bpy.context.selected_objects[0]
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# Material
mat = bpy.data.materials.new(name="AuroraMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes["Principled BSDF"].inputs[0].default_value = (0.2, 0.5, 1.0, 1.0) # Blue
nodes["Principled BSDF"].inputs[7].default_value = 0.8 # Metallic
obj.data.materials.append(mat)

# Studio Lights
bpy.ops.object.light_add(type='AREA', radius=5, location=(10, 10, 10))
bpy.ops.object.light_add(type='AREA', radius=5, location=(-10, -10, 10))

# Camera setup
bpy.ops.object.camera_add(location=(15, -15, 15), rotation=(0.78, 0, 0.78))
bpy.context.scene.camera = bpy.context.object

# Render settings
bpy.context.scene.render.filepath = {repr(output_image)}
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.ops.render.render(write_still=True)
"""

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(render_script)
            script_path = f.name

        try:
            cmd = [
                self.blender_path,
                "--background",
                "--python", script_path
            ]

            logger.info(f"Rendering in Blender: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                return {"error": "Render failed", "details": stderr.decode()}

            return {"success": True, "image_path": output_image}
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)
