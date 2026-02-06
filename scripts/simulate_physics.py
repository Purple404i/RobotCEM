import bpy
import sys
import os
import json

def simulate(stl_path, output_json):
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import STL (try new then old method)
    try:
        bpy.ops.wm.stl_import(filepath=stl_path)
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=stl_path)

    obj = bpy.context.selected_objects[0]

    # Set up physics
    bpy.ops.rigidbody.world_add()
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.mass = 1.0
    obj.rigid_body.collision_shape = 'CONVEX_HULL'

    # Add a ground plane
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, -10))
    ground = bpy.context.object
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = 'PASSIVE'

    # Run simulation for 50 frames
    bpy.context.scene.frame_end = 50

    results = {
        "initial_location": list(obj.location),
        "final_location": None,
        "fell_over": False,
        "max_velocity": 0.0
    }

    # Simple check for stability: did it move much?
    for frame in range(1, 51):
        bpy.context.scene.frame_set(frame)
        # In a real sim we'd check more things

    results["final_location"] = list(obj.location)

    # If it moved significantly in X or Y, or Z dropped a lot, it might be unstable
    if abs(results["final_location"][0] - results["initial_location"][0]) > 5.0:
        results["fell_over"] = True

    with open(output_json, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    # Args: blender --background --python scripts/simulate_physics.py -- <stl_path> <output_json>
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        if len(args) >= 2:
            simulate(args[0], args[1])
