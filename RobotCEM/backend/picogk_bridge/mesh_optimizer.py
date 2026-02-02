import trimesh

def optimize_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Optimize mesh for 3D printing"""
    # Remove duplicate vertices
    mesh.merge_vertices()
    
    # Remove degenerate faces
    mesh.remove_degenerate_faces()
    
    # Fix normals
    mesh.fix_normals()
    
    return mesh
