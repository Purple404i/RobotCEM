import json
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Optional Hugging Face parser support
try:
  from .transformer_interface import HFPromptParser
except Exception:
  HFPromptParser = None

class PromptParser:
    """Parse natural language into structured specifications using Claude"""
    
    def __init__(self, hf_model_name: Optional[str] = None):
      """Initialize parser. Prefer a Hugging Face model when `hf_model_name` is provided.

      Local HF models or remote providers should be used.
      """
      self.component_database = self._load_component_db()

      self.hf_parser = None
      if hf_model_name and HFPromptParser is not None:
        try:
          self.hf_parser = HFPromptParser(model_name=hf_model_name)
          logger.info(f"Initialized HFPromptParser with {hf_model_name}")
        except Exception as e:
          logger.warning(f"Failed to initialize HF parser: {e}")
    
    def _load_component_db(self) -> Dict:
        """Common robotics components database"""
        return {
            "servos": {
                "MG996R": {
                    "type": "servo",
                    "torque_kg_cm": 11,
                    "speed_sec_60deg": 0.17,
                    "voltage": "4.8-7.2V",
                    "weight_g": 55,
                    "dimensions_mm": [40.7, 19.7, 42.9],
                    "mpn": "MG996R",
                    "typical_price": 8.50
                },
                "SG90": {
                    "type": "servo",
                    "torque_kg_cm": 1.8,
                    "speed_sec_60deg": 0.1,
                    "voltage": "4.8-6V",
                    "weight_g": 9,
                    "dimensions_mm": [22.2, 11.8, 31],
                    "mpn": "SG90",
                    "typical_price": 2.50
                }
            },
            "steppers": {
                "NEMA17": {
                    "type": "stepper",
                    "steps_per_rev": 200,
                    "holding_torque_ncm": 4000,
                    "voltage": "12V",
                    "dimensions_mm": [42, 42, 48],
                    "mpn": "17HS4401",
                    "typical_price": 12.00
                },
                "28BYJ-48": {
                    "type": "stepper",
                    "steps_per_rev": 2048,
                    "holding_torque_ncm": 300,
                    "voltage": "5V",
                    "dimensions_mm": [28, 28, 19],
                    "mpn": "28BYJ-48",
                    "typical_price": 3.00
                }
            },
            "bearings": {
                "608ZZ": {
                    "type": "bearing",
                    "bore_mm": 8,
                    "outer_diameter_mm": 22,
                    "width_mm": 7,
                    "dynamic_load_rating_n": 3450,
                    "mpn": "608ZZ",
                    "typical_price": 0.50
                }
            }
        }
    
    async def parse(self, prompt: str) -> Dict:
        """Parse prompt into structured specification"""
        
        system_prompt = """You are an expert robotics engineer who extracts precise specifications from natural language.

Extract and return ONLY a JSON object with this EXACT structure:

{
  "device_type": "robot_arm|gripper|linear_actuator|pan_tilt|custom",
  "dimensions": {
    "length_mm": ,
    "width_mm": ,
    "height_mm": ,
    "reach_mm": ,
    "stroke_mm": 
  },
  "loads": {
    "payload_kg": ,
    "max_force_n": ,
    "torque_nm": 
  },
  "motion": {
    "dof": ,
    "joint_limits_deg": [[min, max], ...],
    "max_speed": <mm/s or deg/s>,
    "acceleration": <mm/s² or deg/s²>,
    "repeatability_mm": 
  },
  "materials": ["PLA", "ABS", "PETG", "Nylon", "Aluminum_6061", "Steel", etc.],
  "manufacturing": "FDM|SLA|SLS|CNC|hybrid",
  "components": [
    {
      "type": "servo|stepper|bearing|sensor|controller",
      "name": "component name",
      "mpn": "manufacturer part number",
      "quantity": ,
      "specifications": {}
    }
  ],
  "environment": {
    "temp_min_c": ,
    "temp_max_c": ,
    "humidity_max_percent": ,
    "outdoor": 
  },
  "requirements": {
    "safety_factor": ,
    "tolerance_mm": ,
    "finish": "as_printed|sanded|painted|anodized",
    "infill_percent": <10-100>,
    "use_lattice": 
  }
}

RULES:
- Extract numbers with units and convert to standard units (mm, kg, N, etc.)
- Identify component MPNs from common robotics parts (MG996R, NEMA17, etc.)
- If information is missing, use engineering defaults
- For robot arms: estimate reach, DOF, joint limits
- For grippers: estimate jaw width, grip force
- RETURN ONLY THE JSON - NO MARKDOWN, NO EXPLANATIONS"""

        # Require a local HF parser (Anthropic removed)
        if self.hf_parser:
          logger.info("Parsing prompt with Hugging Face model...")
          spec = self.hf_parser.parse(prompt)
          return spec

        raise RuntimeError("No Hugging Face model configured for PromptParser. Pass `hf_model_name`.")
        
        # Remove markdown code blocks if present
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()
        
        try:
            spec = json.loads(content)
            logger.info(f"Parsed specification: {spec['device_type']}")
            return spec
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nContent: {content}")
            raise ValueError(f"Invalid JSON response from Claude: {str(e)}")