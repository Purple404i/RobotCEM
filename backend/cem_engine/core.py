import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from anthropic import Anthropic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DesignSpecification:
    device_type: str
    dimensions: Dict[str, float]
    loads: Dict[str, float]
    motion_constraints: Dict[str, Any]
    material_preferences: List[str]
    manufacturing_method: str
    components: List[Dict[str, Any]]
    environmental_conditions: Dict[str, float]
    safety_factor: float
    tolerance: float
    finish_requirements: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggested_fixes: List[str]

class CEMEngine:
    def __init__(self, anthropic_api_key: str, config: dict):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.config = config
        self.design_rules = self._load_design_rules()
        self.material_database = self._load_material_database()
        self.physics_models = self._load_physics_models()
        
    def _load_design_rules(self) -> Dict:
        """Load manufacturing and design constraints"""
        return {
            "3d_printing": {
                "FDM": {
                    "min_wall_thickness": 0.8,  # mm
                    "min_hole_diameter": 2.0,
                    "max_overhang_angle": 45.0,  # degrees
                    "layer_height_range": (0.1, 0.4),
                    "support_angle_threshold": 45.0,
                    "bridging_max_distance": 5.0
                },
                "SLA": {
                    "min_wall_thickness": 0.4,
                    "min_hole_diameter": 0.5,
                    "max_overhang_angle": 30.0,
                    "layer_height_range": (0.025, 0.1),
                    "support_angle_threshold": 30.0,
                    "min_escape_hole_diameter": 3.0
                },
                "SLS": {
                    "min_wall_thickness": 0.7,
                    "min_hole_diameter": 1.5,
                    "max_overhang_angle": 90.0,  # Self-supporting
                    "layer_height_range": (0.1, 0.15),
                    "min_feature_size": 0.5
                }
            },
            "cnc_machining": {
                "min_tool_diameter": 0.5,
                "min_inside_corner_radius": 0.25,
                "max_depth_to_diameter_ratio": 4.0,
                "min_wall_thickness": 1.0
            },
            "mechanical": {
                "min_thread_engagement": 1.5,  # x diameter
                "bearing_clearance": 0.05,     # mm
                "press_fit_interference": 0.02,
                "sliding_fit_clearance": 0.1,
                "bolt_edge_distance": 2.0      # x diameter
            }
        }
    
    def _load_material_database(self) -> Dict:
        """Material properties database"""
        return {
            "PLA": {
                "density": 1.25,              # g/cm³
                "tensile_strength": 50,       # MPa
                "yield_strength": 40,         # MPa
                "elastic_modulus": 3500,      # MPa
                "poisson_ratio": 0.36,
                "thermal_expansion": 68,      # μm/m·°C
                "max_temp": 60,               # °C
                "cost_per_kg": 20,            # USD
                "printability": "excellent"
            },
            "ABS": {
                "density": 1.05,
                "tensile_strength": 40,
                "yield_strength": 35,
                "elastic_modulus": 2300,
                "poisson_ratio": 0.35,
                "thermal_expansion": 90,
                "max_temp": 98,
                "cost_per_kg": 25,
                "printability": "good"
            },
            "PETG": {
                "density": 1.27,
                "tensile_strength": 53,
                "yield_strength": 45,
                "elastic_modulus": 2070,
                "poisson_ratio": 0.38,
                "thermal_expansion": 60,
                "max_temp": 73,
                "cost_per_kg": 30,
                "printability": "good"
            },
            "Nylon": {
                "density": 1.14,
                "tensile_strength": 75,
                "yield_strength": 45,
                "elastic_modulus": 1600,
                "poisson_ratio": 0.39,
                "thermal_expansion": 80,
                "max_temp": 178,
                "cost_per_kg": 80,
                "printability": "moderate"
            },
            "Aluminum_6061": {
                "density": 2.70,
                "tensile_strength": 310,
                "yield_strength": 276,
                "elastic_modulus": 68900,
                "poisson_ratio": 0.33,
                "thermal_expansion": 23.6,
                "max_temp": 582,
                "cost_per_kg": 15,
                "machinability": "excellent"
            },
            "Steel_1045": {
                "density": 7.85,
                "tensile_strength": 620,
                "yield_strength": 450,
                "elastic_modulus": 205000,
                "poisson_ratio": 0.29,
                "thermal_expansion": 11.5,
                "max_temp": 1500,
                "cost_per_kg": 5,
                "machinability": "good"
            }
        }
    
    def _load_physics_models(self) -> Dict:
        """Physics simulation models"""
        return {
            "beam_deflection": self._beam_deflection_model,
            "stress_concentration": self._stress_concentration_model,
            "thermal_expansion": self._thermal_expansion_model,
            "fatigue_life": self._fatigue_life_model
        }
    
    async def parse_prompt(self, user_prompt: str) -> DesignSpecification:
        """Parse natural language into structured engineering specification"""
        
        system_prompt = """You are an expert engineering specification extractor.
        
        Extract the following from the user's prompt and return ONLY valid JSON:
        
        {
          "device_type": "robot_arm|gripper|drone|mechanism|custom",
          "dimensions": {
            "length": <mm>,
            "width": <mm>,
            "height": <mm>,
            "reach": <mm>,  // for arms
            "stroke": <mm>  // for linear actuators
          },
          "loads": {
            "payload": <kg>,
            "max_force": <N>,
            "torque": <N·m>
          },
          "motion_constraints": {
            "dof": <number>,  // degrees of freedom
            "joint_limits": [<deg>, <deg>],
            "speed": <mm/s or deg/s>,
            "acceleration": <mm/s² or deg/s²>,
            "repeatability": <mm>
          },
          "material_preferences": ["PLA", "ABS", "Aluminum", etc.],
          "manufacturing_method": "FDM|SLA|SLS|CNC|hybrid",
          "components": [
            {
              "type": "servo|stepper|bearing|sensor",
              "mpn": "part_number",
              "quantity": <int>,
              "specifications": {}
            }
          ],
          "environmental_conditions": {
            "temp_min": <°C>,
            "temp_max": <°C>,
            "humidity": <%>,
            "outdoor": <bool>
          },
          "safety_factor": <float>,  // default 2.0
          "tolerance": <mm>,  // default 0.1
          "finish_requirements": "as_printed|sanded|painted|anodized"
        }
        
        If information is missing, make engineering assumptions and note them.
        Return ONLY the JSON object, no markdown, no explanations."""
        
        logger.info(f"Parsing prompt: {user_prompt[:100]}...")
        
        response = await asyncio.to_thread(
            self.client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"{system_prompt}\n\nUser prompt:\n{user_prompt}"
            }]
        )
        
        # Extract JSON from response
        content = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        
        spec_dict = json.loads(content)
        
        # Create specification object
        spec = DesignSpecification(
            device_type=spec_dict.get("device_type", "custom"),
            dimensions=spec_dict.get("dimensions", {}),
            loads=spec_dict.get("loads", {}),
            motion_constraints=spec_dict.get("motion_constraints", {}),
            material_preferences=spec_dict.get("material_preferences", ["PLA"]),
            manufacturing_method=spec_dict.get("manufacturing_method", "FDM"),
            components=spec_dict.get("components", []),
            environmental_conditions=spec_dict.get("environmental_conditions", {}),
            safety_factor=spec_dict.get("safety_factor", 2.0),
            tolerance=spec_dict.get("tolerance", 0.1),
            finish_requirements=spec_dict.get("finish_requirements", "as_printed")
        )
        
        logger.info(f"Extracted specification: {spec.device_type}")
        return spec
    
    def validate_design(self, spec: DesignSpecification) -> ValidationResult:
        """Validate design against physics and manufacturing constraints"""
        
        errors = []
        warnings = []
        suggested_fixes = []
        
        # 1. Material validation
        for material in spec.material_preferences:
            if material not in self.material_database:
                errors.append(f"Unknown material: {material}")
                suggested_fixes.append(f"Use one of: {', '.join(self.material_database.keys())}")
        
        # 2. Manufacturing constraints
        method = spec.manufacturing_method
        if method not in self.design_rules.get("3d_printing", {}):
            warnings.append(f"Manufacturing method {method} not fully validated")
        
        # 3. Structural validation
        if "payload" in spec.loads and spec.material_preferences:
            material = spec.material_preferences[0]
            if material in self.material_database:
                mat_props = self.material_database[material]
                
                # Rough stress check (simplified)
                if "length" in spec.dimensions:
                    length = spec.dimensions["length"] / 1000  # Convert to meters
                    payload = spec.loads["payload"]
                    
                    # Cantilever beam approximation
                    max_stress = (payload * 9.81 * length) / 0.001  # Rough estimate
                    allowable_stress = mat_props["yield_strength"] / spec.safety_factor
                    
                    if max_stress > allowable_stress:
                        errors.append(f"Structural failure likely: stress {max_stress:.1f} MPa > allowable {allowable_stress:.1f} MPa")
                        suggested_fixes.append("Increase cross-section, add ribs, or use stronger material")
        
        # 4. Thermal validation
        if "temp_max" in spec.environmental_conditions:
            temp = spec.environmental_conditions["temp_max"]
            material = spec.material_preferences[0] if spec.material_preferences else None
            
            if material and material in self.material_database:
                max_temp = self.material_database[material].get("max_temp", 1000)
                if temp > max_temp:
                    errors.append(f"Operating temperature {temp}°C exceeds material limit {max_temp}°C")
                    suggested_fixes.append(f"Use heat-resistant material or add cooling")
        
        # 5. Tolerance validation
        if spec.tolerance < 0.05:
            warnings.append("Tolerance < 0.05mm may be difficult to achieve with FDM")
            suggested_fixes.append("Consider SLA/SLS or post-machining")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggested_fixes=suggested_fixes
        )
    
    def optimize_design(self, spec: DesignSpecification) -> DesignSpecification:
        """Automatically optimize design parameters"""
        
        optimized_spec = spec
        
        # Material selection optimization
        if spec.loads.get("payload", 0) > 0:
            best_material = self._select_optimal_material(spec)
            if best_material:
                optimized_spec.material_preferences = [best_material] + spec.material_preferences
        
        # Add structural reinforcement suggestions
        if spec.device_type == "robot_arm" and spec.dimensions.get("length", 0) > 150:
            # Long arms need lattice structures
            optimized_spec.motion_constraints["use_lattice"] = True
        
        return optimized_spec
    
    def _select_optimal_material(self, spec: DesignSpecification) -> Optional[str]:
        """Select best material based on requirements"""
        
        scores = {}
        
        for material, props in self.material_database.items():
            score = 0
            
            # Strength-to-weight ratio
            if "payload" in spec.loads:
                strength_weight_ratio = props["tensile_strength"] / props["density"]
                score += strength_weight_ratio * 10
            
            # Cost factor
            score -= props.get("cost_per_kg", 50) * 0.5
            
            # Temperature resistance
            if "temp_max" in spec.environmental_conditions:
                if props.get("max_temp", 0) > spec.environmental_conditions["temp_max"]:
                    score += 20
            
            # Printability
            if spec.manufacturing_method == "FDM":
                if props.get("printability") == "excellent":
                    score += 30
                elif props.get("printability") == "good":
                    score += 15
            
            scores[material] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    # Physics models
    def _beam_deflection_model(self, length, load, material, cross_section):
        """Calculate beam deflection"""
        E = self.material_database[material]["elastic_modulus"] * 1e6  # Convert to Pa
        I = cross_section["moment_of_inertia"]
        deflection = (load * 9.81 * (length/1000)**3) / (3 * E * I)
        return deflection * 1000  # Convert to mm
    
    def _stress_concentration_model(self, nominal_stress, geometry_factor):
        """Calculate stress concentration"""
        return nominal_stress * geometry_factor
    
    def _thermal_expansion_model(self, material, length, delta_T):
        """Calculate thermal expansion"""
        alpha = self.material_database[material]["thermal_expansion"] * 1e-6
        return alpha * length * delta_T
    
    def _fatigue_life_model(self, material, stress_amplitude, mean_stress):
        """Estimate fatigue life (simplified S-N curve)"""
        S_f = self.material_database[material]["tensile_strength"] * 0.5  # Endurance limit
        if stress_amplitude < S_f:
            return float('inf')  # Infinite life
        else:
            # Basquin equation (simplified)
            N = (S_f / stress_amplitude) ** 8
            return N
    
    async def generate_report(self, spec: DesignSpecification, validation: ValidationResult) -> str:
        """Generate detailed engineering report"""
        
        report = f"""
# Engineering Design Report
Generated: {asyncio.get_event_loop().time()}

## Device Specification
- Type: {spec.device_type}
- Dimensions: {spec.dimensions}
- Loads: {spec.loads}
- Materials: {', '.join(spec.material_preferences)}
- Manufacturing: {spec.manufacturing_method}

## Validation Results
Status: {'✓ PASS' if validation.is_valid else '✗ FAIL'}

### Errors
{chr(10).join('- ' + e for e in validation.errors) if validation.errors else 'None'}

### Warnings
{chr(10).join('- ' + w for w in validation.warnings) if validation.warnings else 'None'}

### Suggested Fixes
{chr(10).join('- ' + f for f in validation.suggested_fixes) if validation.suggested_fixes else 'None'}

## Material Properties
"""
        
        for material in spec.material_preferences:
            if material in self.material_database:
                props = self.material_database[material]
                report += f"\n### {material}\n"
                report += f"- Density: {props['density']} g/cm³\n"
                report += f"- Tensile Strength: {props['tensile_strength']} MPa\n"
                report += f"- Elastic Modulus: {props['elastic_modulus']} MPa\n"
                report += f"- Max Temperature: {props.get('max_temp', 'N/A')}°C\n"
        
        return report