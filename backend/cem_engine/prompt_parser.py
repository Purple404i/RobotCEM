import json
import re
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Import will be done lazily in __init__ to avoid circular imports
LLMDomainAdapter = None


class NaturalLanguageAnalyzer:
    """Analyze natural language prompts for engineering intent and constraints"""
    
    def extract_intent(self, prompt: str) -> Dict[str, Any]:
        """Extract primary engineering intent from prompt"""
        prompt_lower = prompt.lower()
        
        # Device type detection
        device_patterns = {
            "robot_arm": ["arm", "manipulator", "robotic arm", "6-dof", "articulated"],
            "gripper": ["gripper", "claw", "hand", "grasp", "clamp"],
            "actuator": ["actuator", "motor", "drive", "linear", "rotary"],
            "printer": ["3d printer", "additive", "fdm", "sla", "powder"],
            "assembly": ["assembly", "workstation", "cell", "line"],
            "mechanism": ["mechanism", "gear", "linkage", "joint", "bearing"],
            "enclosure": ["enclosure", "case", "housing", "box", "container"],
            "bracket": ["bracket", "mount", "support", "fixture", "holder"],
            "lattice": ["lattice", "infill", "porous", "cellular", "honeycomb"],
        }
        
        detected_type = "custom"
        for device_type, keywords in device_patterns.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_type = device_type
                break
        
        # Goal detection
        goal_patterns = {
            "lightweight": ["light", "weight reduction", "minimal weight", "featherweight"],
            "cost_effective": ["cheap", "affordable", "budget", "economical", "cost"],
            "durable": ["strong", "robust", "durable", "heavy duty", "rugged"],
            "high_precision": ["precise", "accuracy", "tolerance", "exact"],
            "rapid_prototyping": ["quick", "fast", "rapid", "prototype", "iterate"],
        }
        
        optimization_goals = []
        for goal, keywords in goal_patterns.items():
            if any(keyword in prompt_lower for keyword in keywords):
                optimization_goals.append(goal)
        
        return {
            "detected_device_type": detected_type,
            "optimization_goals": optimization_goals or ["balanced"],
            "prompt_length": len(prompt),
            "specificity": self._calculate_specificity(prompt),
        }
    
    def _calculate_specificity(self, prompt: str) -> float:
        """Calculate how specific the prompt is (0-1)"""
        keywords = len(prompt.split())
        has_numbers = bool(re.search(r'\d+', prompt))
        has_units = bool(re.search(r'(mm|cm|kg|n|degrees?|rpm|watts?|volts?)', prompt.lower()))
        has_constraints = any(word in prompt.lower() for word in 
                            ["budget", "cost", "max", "minimum", "at least", "no more than"])
        
        specificity = (keywords / 50) * 0.25  # Longer prompts = more specific (0.25 max)
        specificity += 0.25 if has_numbers else 0
        specificity += 0.25 if has_units else 0
        specificity += 0.25 if has_constraints else 0
        
        return min(1.0, specificity)


class PromptParser:
    """Parse natural language into structured specifications using LLM engine"""
    
    def __init__(self, hf_model_name: Optional[str] = None):
      """Initialize parser with LLM engine for advanced natural language processing."""
      self.component_database = self._load_component_db()
      self.nl_analyzer = NaturalLanguageAnalyzer()
      
      # Initialize LLM engine for advanced parsing (lazy import to avoid circular deps)
      try:
        from .llm_engine import get_llm_engine
        self.llm_engine = get_llm_engine()
        logger.info("Initialized LLM engine for prompt parsing")
      except Exception as e:
        logger.warning(f"Failed to initialize LLM engine: {e}")
        self.llm_engine = None
      
      # Initialize domain adapter for training-enhanced responses
      try:
        if LLMDomainAdapter:
          self.domain_adapter = LLMDomainAdapter()
          num_items = self.domain_adapter.load_training_data()
          if num_items > 0:
            logger.info(f"✓ Domain adapter loaded with {num_items} training items")
          else:
            logger.warning("Domain adapter initialized but no training data found")
        else:
          self.domain_adapter = None
      except Exception as e:
        logger.warning(f"Failed to initialize domain adapter: {e}")
        self.domain_adapter = None
      
      # hf_model_name is deprecated but kept for backwards compatibility
      if hf_model_name:
        logger.info(f"Note: hf_model_name parameter deprecated. Using LLM engine and training instead.")
    
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
        """Parse prompt into structured specification using LLM engine with training"""
        
        # Extract intent and analyze prompt
        intent_analysis = self.nl_analyzer.extract_intent(prompt)
        
        # Use domain adapter to enhance prompt with training data
        enhanced_prompt = prompt
        if self.domain_adapter:
          try:
            enhanced_prompt = self.domain_adapter.enhance_prompt_with_context(
                prompt, 
                intent=intent_analysis.get("optimization_goals", ["balanced"])[0]
            )
            logger.info("✓ Prompt enhanced with domain training data")
          except Exception as e:
            logger.debug(f"Domain adapter enhancement failed: {e}, using original prompt")
        
        # Use LLM engine for advanced parsing
        if self.llm_engine:
          logger.info("Parsing prompt with LLM engine (domain-adapted)...")
          
          # Start conversation session for context
          session_id = f"parse_{intent_analysis['detected_device_type']}_{int(datetime.utcnow().timestamp())}"
          context, _ = self.llm_engine.start_conversation(session_id, enhanced_prompt)
          
          # Process prompt through LLM engine
          llm_result = await self.llm_engine.process_prompt(session_id, enhanced_prompt, self)
          
          spec = {
              "device_type": llm_result.get("device_type", intent_analysis["detected_device_type"]),
              "dimensions": llm_result.get("dimensions", {}),
              "loads": llm_result.get("loads", {}),
              "motion": llm_result.get("motion", {}),
              "materials": llm_result.get("materials", ["PLA"]),
              "manufacturing": llm_result.get("manufacturing", "FDM"),
              "components": llm_result.get("components", []),
              "environment": llm_result.get("environment", {}),
              "requirements": llm_result.get("requirements", {}),
          }
          
          confidence = llm_result.get("confidence_score", intent_analysis["specificity"])
        else:
          raise RuntimeError("LLM engine not initialized. Cannot parse prompts.")
        
        # Enrich specification with intent analysis and training context
        spec["_intent_analysis"] = intent_analysis
        spec["_parsed_at"] = datetime.utcnow().isoformat()
        spec["_specificity_score"] = confidence
        spec["_domain_adapted"] = self.domain_adapter is not None
        
        logger.info(f"Parsed specification: {spec.get('device_type', 'custom')} with confidence: {confidence:.2%}")
        if self.domain_adapter:
            logger.info(f"Domain adaptation: enabled with {len(self.domain_adapter.knowledge_base)} knowledge categories")
        return spec
        
        # Enrich specification with intent analysis
        spec["_intent_analysis"] = intent_analysis
        spec["_parsed_at"] = datetime.utcnow().isoformat()
        spec["_specificity_score"] = confidence
        
        logger.info(f"Parsed specification: {spec.get('device_type', 'custom')} with confidence: {confidence:.2%}")
        return spec
