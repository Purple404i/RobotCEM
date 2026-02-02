from typing import Dict, Any
import copy
import logging

logger = logging.getLogger(__name__)


def _upgrade_material(spec: Dict[str, Any], material_db: Dict) -> Dict[str, Any]:
    """Switch to a stronger material when structural failures occur."""
    new_spec = copy.deepcopy(spec)
    preferred = material_db.get("MATERIAL_SELECTION_GUIDE", None)

    # Fallback mapping if guide not present
    fallback = ["Carbon_Fiber_PLA", "Nylon", "Aluminum_6061", "Steel_1045"]

    current = spec.get("materials", [None])[0]
    candidates = fallback

    for m in candidates:
        if m != current:
            new_spec["materials"] = [m]
            logger.info(f"Auto-fix: switching material to {m}")
            return new_spec

    return new_spec


def _increase_dimensions(spec: Dict[str, Any], factor: float = 1.2) -> Dict[str, Any]:
    new_spec = copy.deepcopy(spec)
    dims = new_spec.setdefault("dimensions", {})
    for k, v in list(dims.items()):
        try:
            if isinstance(v, (int, float)):
                dims[k] = v * factor
        except Exception:
            continue

    # Also increase wall thickness if present
    if "wall_thickness" in new_spec:
        try:
            new_spec["wall_thickness"] = new_spec["wall_thickness"] * factor
        except Exception:
            pass

    logger.info(f"Auto-fix: increased dimensions by {factor}x")
    return new_spec


def _upgrade_components(spec: Dict[str, Any]) -> Dict[str, Any]:
    new_spec = copy.deepcopy(spec)
    comps = new_spec.setdefault("components", [])
    for c in comps:
        if c.get("type") == "servo":
            # If no MPN try to set a stronger default
            if not c.get("mpn"):
                c["mpn"] = "MG996R"
                c["estimated_cost"] = 8.5
                logger.info("Auto-fix: set servo MPN to MG996R")
    return new_spec


def propose_fixes(spec: Dict[str, Any], validation_report: Dict[str, Any], material_db: Dict) -> Dict[str, Any]:
    """Return a modified spec attempting to fix errors found by validators."""
    new_spec = spec

    # Structural problems -> increase thickness/diameter or change material
    struct = validation_report.get("structural", {})
    if struct and struct.get("errors"):
        new_spec = _increase_dimensions(new_spec, factor=1.3)
        new_spec = _upgrade_material(new_spec, material_db)

    # Thermal issues -> pick higher temp material
    thermal = validation_report.get("thermal", {})
    if thermal and thermal.get("errors"):
        new_spec = _upgrade_material(new_spec, material_db)

    # Component issues -> upgrade components
    if struct and struct.get("warnings"):
        new_spec = _upgrade_components(new_spec)

    return new_spec
