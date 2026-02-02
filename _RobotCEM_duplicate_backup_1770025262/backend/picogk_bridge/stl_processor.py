import trimesh
from pathlib import Path

def analyze_stl(stl_path: Path) -> dict:
    """Analyze STL file properties"""
    try:
        mesh = trimesh.load(str(stl_path))
        
        return {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "volume_mm3": float(mesh.volume),
            "volume_cm3": float(mesh.volume / 1000),
            "surface_area_mm2": float(mesh.area),
            "is_watertight": mesh.is_watertight,
            "dimensions": {
                "x": float(mesh.bounds[1][0] - mesh.bounds[0][0]),
                "y": float(mesh.bounds[1][1] - mesh.bounds[0][1]),
                "z": float(mesh.bounds[1][2] - mesh.bounds[0][2])
            }
        }
    except Exception as e:
        return {"error": str(e)}
