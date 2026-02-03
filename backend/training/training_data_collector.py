"""
Training data collector for LLM and CEM engines.
Extracts knowledge from LEAP 71 documentation and robotics examples.
"""

import json
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TrainingDataCollector:
    """Collects and structures training data for LLM and CEM engines"""
    
    def __init__(self):
        self.shape_kernel_docs = {}
        self.lattice_library_docs = {}
        self.picogk_docs = {}
        self.robotics_rules = {}
        
    def collect_shape_kernel_knowledge(self) -> List[Dict[str, Any]]:
        """Extract ShapeKernel knowledge for training"""
        knowledge = []
        
        # Base shapes training data
        base_shapes_data = [
            {
                "shape": "BaseBox",
                "description": "Rectangular box primitive",
                "parameters": ["length", "width", "height"],
                "use_cases": ["housings", "structural frames", "brackets"],
                "manufacturing": ["3D printing", "CNC"],
                "lattice_compatible": True,
                "example": "For a motor housing, use BaseBox with dimensions 100x80x60 mm",
                "training_text": "BaseBox is used for rectangular geometries. It takes three parameters: length, width, and height. Ideal for housings, frames, and structural components. Compatible with lattice infill for weight reduction."
            },
            {
                "shape": "BaseSphere",
                "description": "Spherical primitive",
                "parameters": ["radius"],
                "use_cases": ["bearing components", "connector heads", "rounded tips"],
                "manufacturing": ["3D printing", "CNC", "SLS"],
                "lattice_compatible": True,
                "example": "Create a spherical bearing housing with 25mm radius",
                "training_text": "BaseSphere creates spherical geometry. Takes a radius parameter. Used for bearing components, connector heads, and rounded features. Can be combined with lattices for optimized structures."
            },
            {
                "shape": "BaseCylinder",
                "description": "Cylindrical primitive",
                "parameters": ["radius", "height"],
                "use_cases": ["shafts", "connectors", "tubes", "posts"],
                "manufacturing": ["3D printing", "CNC", "turning"],
                "lattice_compatible": True,
                "example": "Motor shaft: BaseCylinder with 5mm radius, 50mm height",
                "training_text": "BaseCylinder creates cylindrical geometries. Parameters: radius and height. Used for shafts, connectors, tubes, and mounting posts. Excellent for rotational components and lattice infill."
            },
            {
                "shape": "BasePipe",
                "description": "Hollow cylindrical primitive (tube)",
                "parameters": ["outer_radius", "inner_radius", "height"],
                "use_cases": ["tubes", "manifolds", "cable routing", "fluid channels"],
                "manufacturing": ["3D printing", "CNC"],
                "lattice_compatible": False,
                "example": "Cooling manifold: BasePipe outer=15mm, inner=10mm, height=80mm",
                "training_text": "BasePipe creates hollow cylindrical geometry. Parameters: outer_radius, inner_radius, height. Used for manifolds, tubing, fluid channels, and cable routing."
            },
            {
                "shape": "BaseLens",
                "description": "Lens-shaped primitive (convex)",
                "parameters": ["radius", "thickness"],
                "use_cases": ["optical components", "curved mounts", "aesthetic features"],
                "manufacturing": ["3D printing SLA", "CNC polishing"],
                "lattice_compatible": True,
                "example": "Camera lens mount with 20mm radius, 5mm thickness",
                "training_text": "BaseLens creates lens-shaped geometry. Parameters: radius and thickness. Used for optical components, curved mounts, and aesthetic features in optical systems."
            },
            {
                "shape": "BaseRing",
                "description": "Ring/annular primitive",
                "parameters": ["outer_radius", "inner_radius", "thickness"],
                "use_cases": ["bearings", "seals", "connector rings", "washers"],
                "manufacturing": ["3D printing", "turning", "casting"],
                "lattice_compatible": True,
                "example": "Bearing ring: outer=13mm, inner=8mm, thickness=7mm",
                "training_text": "BaseRing creates ring-shaped geometry. Parameters: outer_radius, inner_radius, thickness. Used for bearing components, seals, connector rings, and washers."
            }
        ]
        
        for shape_data in base_shapes_data:
            knowledge.append({
                "type": "base_shape",
                "category": "shape_kernel",
                "title": f"ShapeKernel {shape_data['shape']}",
                "content": shape_data["training_text"],
                "metadata": shape_data,
                "intent": "geometry_design",
                "tags": ["baseshape", "shapekernel", "geometry", shape_data["shape"]]
            })
        
        return knowledge
    
    def collect_lattice_library_knowledge(self) -> List[Dict[str, Any]]:
        """Extract Lattice Library knowledge for training"""
        knowledge = []
        
        lattice_types = [
            {
                "type": "BodyCenteredLattice",
                "description": "Standard body-centered cubic lattice",
                "structure": "Connects corner vertices diagonally with center point",
                "weight_reduction": "30-40%",
                "strength": "Good structural strength",
                "use_cases": ["load-bearing structures", "structural optimization"],
                "training_text": "BodyCenteredLattice uses standard crystallographic structure connecting corner vertices with center points. Provides 30-40% weight reduction while maintaining structural integrity. Ideal for load-bearing components and optimization."
            },
            {
                "type": "OctahedronLattice",
                "description": "Octahedron-based lattice",
                "structure": "Beam structure based on octahedral unit cells",
                "weight_reduction": "25-35%",
                "strength": "Balanced strength and weight",
                "use_cases": ["impact resistant structures", "energy absorption"],
                "training_text": "OctahedronLattice uses octahedral unit cell structure. Provides 25-35% weight reduction with balanced strength. Better impact absorption compared to body-centered lattices."
            },
            {
                "type": "RegularCellArray",
                "description": "Uniform periodic lattice array",
                "structure": "Regular repeating unit cells",
                "weight_reduction": "20-30%",
                "strength": "Predictable and uniform",
                "use_cases": ["mass-produced components", "consistent properties"],
                "training_text": "RegularCellArray creates uniform periodic lattice structures. Cell dimensions can be customized. Supports noise/randomization for improved damping. Weight reduction 20-30% with consistent properties."
            },
            {
                "type": "ConformalCellArray",
                "description": "Lattice conformal to surface geometry",
                "structure": "Adaptive cells following object boundaries",
                "weight_reduction": "25-40%",
                "strength": "High, especially at surfaces",
                "use_cases": ["complex shaped components", "optimized geometry"],
                "training_text": "ConformalCellArray adapts lattice cells to follow the surface of complex shapes. Provides 25-40% weight reduction while maintaining surface integrity. Best for optimized complex geometries."
            }
        ]
        
        for lattice in lattice_types:
            knowledge.append({
                "type": "lattice_type",
                "category": "lattice_library",
                "title": f"Lattice Library {lattice['type']}",
                "content": lattice["training_text"],
                "metadata": lattice,
                "intent": "weight_optimization",
                "tags": ["lattice", "optimization", "weight_reduction", lattice["type"]]
            })
        
        # Cell array training
        cell_array_data = [
            {
                "name": "Cell size optimization",
                "rule": "Cell size should be 10-50x the beam thickness for optimal results",
                "training_text": "When designing lattice structures, maintain cell size between 10-50x the beam thickness. This ensures optimal structural properties and printability."
            },
            {
                "name": "Beam thickness distribution",
                "rule": "Vary beam thickness based on local stress: higher stress = thicker beams",
                "training_text": "Apply gradient beam thickness distribution based on stress analysis. High-stress areas use thicker beams (1.5-2mm), low-stress areas use thinner beams (0.5-1mm)."
            },
            {
                "name": "Manufacturing constraints",
                "rule": "Minimum beam thickness must be ≥0.5mm for FDM, ≥0.3mm for SLA",
                "training_text": "Manufacturing process constraints: FDM requires minimum 0.5mm beam thickness, SLA requires 0.3mm minimum, SLS allows 0.7mm minimum."
            }
        ]
        
        for rule_data in cell_array_data:
            knowledge.append({
                "type": "lattice_rule",
                "category": "lattice_library",
                "title": f"Lattice Rule: {rule_data['name']}",
                "content": rule_data["training_text"],
                "metadata": rule_data,
                "intent": "manufacturing_optimization",
                "tags": ["lattice", "manufacturing", "constraints"]
            })
        
        return knowledge
    
    def collect_robotics_domain_knowledge(self) -> List[Dict[str, Any]]:
        """Extract robotics domain knowledge for training"""
        knowledge = []
        
        robotics_rules = [
            {
                "domain": "gripper_design",
                "rules": [
                    "Payload capacity: minimum 2x safety factor on load",
                    "Jaw width: typically 20-150mm depending on application",
                    "Stroke: 10-100mm for parallel grippers",
                    "Material: Al6061 for frames, stainless for jaws",
                    "Grip force: 50-500N depending on payload"
                ],
                "training_text": "Gripper Design Rules: Apply 2x safety factor minimum. Jaw width ranges 20-150mm. Parallel gripper stroke 10-100mm. Use Al6061 for frames, stainless steel for contact surfaces. Grip force 50-500N based on payload."
            },
            {
                "domain": "robot_arm",
                "rules": [
                    "Reach: typically 500-2500mm for industrial arms",
                    "Payload: 1-500kg depending on reach",
                    "DOF: 3-6 for most industrial applications",
                    "Joint types: revolute or linear depending on workspace",
                    "Material: carbon fiber for links, Al for joints"
                ],
                "training_text": "Robot Arm Design: Typical reach 500-2500mm. Payload inversely proportional to reach. Standard 6-DOF configuration. Use revolute joints for articulation, carbon fiber for light links. Maintain 2-3x safety factor."
            },
            {
                "domain": "actuator_selection",
                "rules": [
                    "Servo: smooth motion, high precision, low power",
                    "Stepper: open-loop, medium torque, cost-effective",
                    "Brushless motor: high efficiency, needs controller",
                    "Linear actuator: for sliding/extension motions",
                    "Pneumatic: high force, lower precision"
                ],
                "training_text": "Actuator Selection: Servo motors for precision and smooth control. Stepper motors for cost-effective open-loop applications. Brushless motors for efficiency and speed. Linear actuators for extension motions. Pneumatics for extreme force needs."
            },
            {
                "domain": "bearing_selection",
                "rules": [
                    "Load rating: minimum 2x dynamic load capacity",
                    "Type: ball bearing for low friction, roller for heavy loads",
                    "Bore: typically 5-50mm for robotics",
                    "Material: stainless for corrosive environments",
                    "Preload: light preload for precision, no preload for low friction"
                ],
                "training_text": "Bearing Selection: Choose dynamic load rating 2x minimum. Ball bearings for low friction, roller bearings for heavy loads. Stainless steel for harsh environments. Apply light preload for precision applications."
            },
            {
                "domain": "material_selection",
                "rules": [
                    "3D print: PLA (low cost), ABS (impact), PETG (balance), Nylon (durability)",
                    "CNC: Al6061 (light), Steel (strong), Brass (precision)",
                    "Cost vs strength: PLA ($5/kg) vs Steel ($3/kg but heavier)",
                    "Weight: carbon fiber (-40% vs Al), titanium (+50% cost)",
                    "Tolerance: FDM ±0.3mm, SLA ±0.1mm, CNC ±0.05mm"
                ],
                "training_text": "Material Selection: 3D printing use PLA for prototypes, ABS for impact, PETG for balanced properties, Nylon for durability. CNC use Al6061 for light structures, Steel for high strength. Consider cost-weight tradeoffs. Tolerance FDM ±0.3mm, SLA ±0.1mm, CNC ±0.05mm."
            }
        ]
        
        for domain_rule in robotics_rules:
            knowledge.append({
                "type": "domain_rule",
                "category": "robotics",
                "domain": domain_rule["domain"],
                "title": f"Robotics Domain: {domain_rule['domain']}",
                "content": domain_rule["training_text"],
                "metadata": domain_rule,
                "intent": "component_selection",
                "tags": ["robotics", domain_rule["domain"], "engineering_rules"]
            })
        
        return knowledge
    
    def collect_cem_optimization_rules(self) -> List[Dict[str, Any]]:
        """Extract CEM optimization rules for training"""
        knowledge = []
        
        optimization_strategies = [
            {
                "goal": "lightweight",
                "rules": [
                    "Apply lattice infill 20-40%",
                    "Reduce wall thickness from 3mm to 1.5-2mm",
                    "Use lighter materials (PLA > ABS > PETG > Al)",
                    "Minimize feature count and complexity",
                    "Apply topology optimization to remove dead material"
                ],
                "estimated_improvement": "30-50% weight reduction",
                "cost_impact": "5-15% cost increase",
                "training_text": "Lightweight optimization: Apply 20-40% lattice infill using BodyCentric or Octahedron types. Reduce wall thickness to 1.5-2mm minimum. Use PLA/ABS for 3D print. Remove non-load-bearing features. Achieves 30-50% weight reduction with 5-15% cost increase."
            },
            {
                "goal": "cost_effective",
                "rules": [
                    "Use FDM printing (cheapest)",
                    "Minimize support material",
                    "Standard tolerance ±0.3mm",
                    "No infill (0%) for non-structural parts",
                    "Consolidate multiple parts where possible"
                ],
                "estimated_improvement": "35-50% cost reduction",
                "weight_impact": "10-20% heavier",
                "training_text": "Cost-effective optimization: Use FDM printing on PLA material. Minimize supports with optimal orientation. Accept standard ±0.3mm tolerance. Use 0% infill for non-load bearing parts. Consolidate parts when possible. Achieves 35-50% cost reduction with acceptable weight."
            },
            {
                "goal": "durable",
                "rules": [
                    "Apply 3.0x safety factor (vs standard 2.0x)",
                    "Use PETG or Nylon materials",
                    "Wall thickness: minimum 2.5-3mm",
                    "Chamfer all edges (1-2mm radius)",
                    "Add reinforcing ribs at stress concentrations"
                ],
                "estimated_improvement": "2x lifespan typical",
                "cost_impact": "20-30% cost increase",
                "training_text": "Durable design: Apply 3.0x safety factor instead of 2.0x. Use PETG or Nylon for high-stress applications. Wall thickness 2.5-3mm minimum. Add 1-2mm edge chamfers to reduce stress concentration. Reinforcing ribs at corners and joints. Achieves 2x typical lifespan."
            },
            {
                "goal": "high_precision",
                "rules": [
                    "Use SLA or CNC manufacturing",
                    "Tolerance ±0.1mm (SLA) or ±0.05mm (CNC)",
                    "Avoid draft angles in 3D models",
                    "Post-process: polishing for SLA, deburring for CNC",
                    "Tight tolerances on mating surfaces only"
                ],
                "estimated_improvement": "±0.05-0.1mm achievable",
                "cost_impact": "50-200% cost increase",
                "training_text": "High precision: SLA provides ±0.1mm tolerance, CNC provides ±0.05mm. Apply tight tolerances only to critical mating surfaces. Post-process polishing required. Cost increases 50-200% for precision. Best for optical and critical assemblies."
            },
            {
                "goal": "rapid_prototyping",
                "rules": [
                    "FDM printing fastest turnaround",
                    "Standard tolerances ±0.3mm",
                    "Design for minimal supports",
                    "Use thick walls for strength (2-3mm)",
                    "Iterative design with 24-48hr cycles"
                ],
                "estimated_improvement": "24-48hr turnaround",
                "cost_impact": "Minimal vs production",
                "training_text": "Rapid prototyping: FDM printing on PLA for fastest 24-48hr turnaround. Design for 45° overhangs to minimize supports. Use 2-3mm walls for test strength. Accept ±0.3mm tolerance for iteration cycles."
            }
        ]
        
        for strategy in optimization_strategies:
            knowledge.append({
                "type": "optimization_strategy",
                "category": "cem",
                "goal": strategy["goal"],
                "title": f"CEM Optimization: {strategy['goal']}",
                "content": strategy["training_text"],
                "metadata": strategy,
                "intent": "design_optimization",
                "tags": ["cem", "optimization", strategy["goal"], "engineering_strategy"]
            })
        
        return knowledge
    
    def collect_all_knowledge(self) -> List[Dict[str, Any]]:
        """Collect all training knowledge"""
        all_knowledge = []
        
        logger.info("Collecting ShapeKernel knowledge...")
        all_knowledge.extend(self.collect_shape_kernel_knowledge())
        
        logger.info("Collecting Lattice Library knowledge...")
        all_knowledge.extend(self.collect_lattice_library_knowledge())
        
        logger.info("Collecting robotics domain knowledge...")
        all_knowledge.extend(self.collect_robotics_domain_knowledge())
        
        logger.info("Collecting CEM optimization rules...")
        all_knowledge.extend(self.collect_cem_optimization_rules())
        
        logger.info(f"Total knowledge items collected: {len(all_knowledge)}")
        return all_knowledge
    
    def save_training_data(self, knowledge: List[Dict], output_path: str = "backend/training/training_data.json"):
        """Save training data to JSON file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(knowledge, f, indent=2)
        logger.info(f"Training data saved to {output_path}")
        return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = TrainingDataCollector()
    knowledge = collector.collect_all_knowledge()
    output_file = collector.save_training_data(knowledge)
    
    print(f"\n✅ Collected {len(knowledge)} training items")
    print(f"📁 Saved to: {output_file}")
    print(f"\nKnowledge breakdown:")
    categories = {}
    for item in knowledge:
        cat = item.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count} items")
