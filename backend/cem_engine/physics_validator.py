import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class PhysicsValidator:
    """Validate designs against physics and engineering principles"""
    
    def __init__(self, material_db: Dict, design_rules: Dict):
        self.material_db = material_db
        self.design_rules = design_rules
    
    def validate_structural(self, spec: Dict) -> Dict:
        """Validate structural integrity"""
        
        errors = []
        warnings = []
        
        if spec.get("device_type") == "robot_arm":
            result = self._validate_cantilever_arm(spec)
            errors.extend(result["errors"])
            warnings.extend(result["warnings"])
        
        elif spec.get("device_type") == "gripper":
            result = self._validate_gripper(spec)
            errors.extend(result["errors"])
            warnings.extend(result["warnings"])
        
        return {
            "structural_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_cantilever_arm(self, spec: Dict) -> Dict:
        """Validate robot arm as cantilever beam"""
        
        errors = []
        warnings = []
        
        reach = spec["dimensions"].get("reach_mm", 0)
        payload = spec["loads"].get("payload_kg", 0)
        material = spec["materials"][0] if spec.get("materials") else "PLA"
        
        if material not in self.material_db:
            errors.append(f"Unknown material: {material}")
            return {"errors": errors, "warnings": warnings}
        
        mat = self.material_db[material]
        
        # Simplified beam deflection
        # Assume circular cross-section, diameter = reach/10
        diameter = reach / 10  # mm
        
        # Moment of inertia for hollow tube
        wall_thickness = 3  # mm
        outer_radius = diameter / 2
        inner_radius = outer_radius - wall_thickness
        
        I = np.pi / 4 * (outer_radius**4 - inner_radius**4)  # mm^4
        
        # Force at end
        F = payload * 9.81  # N
        L = reach  # mm
        E = mat["elastic_modulus"]  # MPa = N/mm²
        
        # Deflection = F*L³ / (3*E*I)
        deflection = (F * L**3) / (3 * E * I)  # mm
        
        if deflection > reach * 0.05:  # More than 5% of reach
            errors.append(f"Excessive deflection: {deflection:.1f}mm ({deflection/reach*100:.1f}% of reach)")
        elif deflection > reach * 0.02:
            warnings.append(f"Significant deflection expected: {deflection:.1f}mm")
        
        # Stress check
        # Max bending moment at base
        M = F * L  # N·mm
        c = outer_radius  # mm
        
        stress = (M * c) / I  # MPa
        
        safety_factor = spec.get("requirements", {}).get("safety_factor", 2.0)
        allowable_stress = mat["yield_strength"] / safety_factor
        
        if stress > allowable_stress:
            errors.append(
                f"Stress failure: {stress:.1f} MPa > allowable {allowable_stress:.1f} MPa. "
                f"Increase diameter, add ribs, or use stronger material."
            )
        elif stress > allowable_stress * 0.8:
            warnings.append(f"High stress: {stress:.1f} MPa (80% of allowable)")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_gripper(self, spec: Dict) -> Dict:
        """Validate gripper mechanics"""
        
        errors = []
        warnings = []
        
        # Check if servo torque is sufficient for grip force
        components = spec.get("components", [])
        servos = [c for c in components if c.get("type") == "servo"]
        
        if not servos:
            warnings.append("No servo specified for gripper actuation")
            return {"errors": errors, "warnings": warnings}
        
        # Simplified grip force calculation
        servo_torque = 10  # kg·cm (typical for MG996R)
        jaw_length = spec["dimensions"].get("length_mm", 50)
        lever_arm = jaw_length / 10  # cm
        
        grip_force = servo_torque / lever_arm  # kg
        required_force = spec["loads"].get("payload_kg", 0) * 1.5  # 1.5x safety
        
        if grip_force < required_force:
            errors.append(
                f"Insufficient grip force: {grip_force:.1f}kg < required {required_force:.1f}kg. "
                f"Use stronger servo or increase mechanical advantage."
            )
        
        return {"errors": errors, "warnings": warnings}
    
    def validate_thermal(self, spec: Dict) -> Dict:
        """Validate thermal constraints"""
        
        errors = []
        warnings = []
        
        temp_max = spec.get("environment", {}).get("temp_max_c", 25)
        material = spec["materials"][0] if spec.get("materials") else "PLA"
        
        if material in self.material_db:
            mat_max_temp = self.material_db[material].get("max_temp", 1000)
            
            if temp_max > mat_max_temp:
                errors.append(
                    f"Operating temperature {temp_max}°C exceeds material limit {mat_max_temp}°C. "
                    f"Use heat-resistant material or add cooling."
                )
            elif temp_max > mat_max_temp * 0.8:
                warnings.append(
                    f"Operating near material limit: {temp_max}°C (limit: {mat_max_temp}°C)"
                )
        
        return {
            "thermal_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def validate_manufacturing(self, spec: Dict) -> Dict:
        """Validate manufacturing feasibility"""
        
        errors = []
        warnings = []
        
        method = spec.get("manufacturing", "FDM")
        
        if method in self.design_rules.get("3d_printing", {}):
            rules = self.design_rules["3d_printing"][method]
            
            # Check minimum features
            # This would be more detailed with actual geometry analysis
            
            tolerance = spec.get("requirements", {}).get("tolerance_mm", 0.1)
            
            if tolerance < 0.05 and method == "FDM":
                warnings.append(
                    f"Tolerance {tolerance}mm difficult with FDM. Consider SLA or post-machining."
                )
        
        return {
            "manufacturing_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }