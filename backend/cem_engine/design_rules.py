"""Manufacturing design rules database"""

DESIGN_RULES = {
    "3d_printing": {
        "FDM": {
            "min_wall_thickness_mm": 0.8,
            "min_hole_diameter_mm": 2.0,
            "max_overhang_angle_deg": 45.0,
            "layer_height_range_mm": (0.1, 0.4),
            "support_angle_threshold_deg": 45.0,
            "bridging_max_distance_mm": 5.0,
            "min_feature_size_mm": 0.4,
            "typical_accuracy_mm": 0.2,
            "surface_roughness_um": 12
        },
        "SLA": {
            "min_wall_thickness_mm": 0.4,
            "min_hole_diameter_mm": 0.5,
            "max_overhang_angle_deg": 30.0,
            "layer_height_range_mm": (0.025, 0.1),
            "support_angle_threshold_deg": 30.0,
            "min_escape_hole_diameter_mm": 3.0,
            "min_feature_size_mm": 0.2,
            "typical_accuracy_mm": 0.05,
            "surface_roughness_um": 3
        },
        "SLS": {
            "min_wall_thickness_mm": 0.7,
            "min_hole_diameter_mm": 1.5,
            "max_overhang_angle_deg": 90.0,
            "layer_height_range_mm": (0.1, 0.15),
            "min_feature_size_mm": 0.5,
            "typical_accuracy_mm": 0.1,
            "surface_roughness_um": 8,
            "self_supporting": True
        }
    },
    "cnc_machining": {
        "min_tool_diameter_mm": 0.5,
        "min_inside_corner_radius_mm": 0.25,
        "max_depth_to_diameter_ratio": 4.0,
        "min_wall_thickness_mm": 1.0,
        "typical_tolerance_mm": 0.025,
        "surface_finish_um": 1.6
    },
    "mechanical_design": {
        "min_thread_engagement": 1.5,
        "bearing_clearance_mm": 0.05,
        "press_fit_interference_mm": 0.02,
        "sliding_fit_clearance_mm": 0.1,
        "bolt_edge_distance_factor": 2.0,
        "fillet_radius_factor": 0.2
    }
}

# Standard hardware specifications
STANDARD_HARDWARE = {
    "metric_screws": {
        "M2": {"thread_diameter": 2.0, "clearance_hole": 2.2, "tap_drill": 1.6},
        "M3": {"thread_diameter": 3.0, "clearance_hole": 3.2, "tap_drill": 2.5},
        "M4": {"thread_diameter": 4.0, "clearance_hole": 4.3, "tap_drill": 3.3},
        "M5": {"thread_diameter": 5.0, "clearance_hole": 5.3, "tap_drill": 4.2},
        "M6": {"thread_diameter": 6.0, "clearance_hole": 6.4, "tap_drill": 5.0}
    },
    "bearings": {
        "608": {"bore": 8, "od": 22, "width": 7},
        "6000": {"bore": 10, "od": 26, "width": 8},
        "6200": {"bore": 10, "od": 30, "width": 9}
    }
}