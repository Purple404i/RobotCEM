"""
Advanced LLM Engine for RobotCEM

Handles natural language understanding with context awareness, 
clarification dialogs, and iterative refinement of specifications.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import re
from .prompt_parser import PromptParser

logger = logging.getLogger(__name__)


class InteractionMode(Enum):
    """Different modes of interaction with the LLM"""
    SPECIFICATION = "specification"  # Extract device specs from prompt
    CLARIFICATION = "clarification"  # Ask clarifying questions
    REFINEMENT = "refinement"        # Refine existing specs based on feedback
    OPTIMIZATION = "optimization"    # Suggest optimizations
    TROUBLESHOOTING = "troubleshooting"  # Help debug design issues


@dataclass
class ConversationContext:
    """Maintain conversation state across interactions"""
    session_id: str
    device_type: Optional[str] = None
    initial_prompt: Optional[str] = None
    specification: Optional[Dict] = None
    clarification_history: List[Dict] = None
    refinement_iterations: int = 0
    max_iterations: int = 3
    confidence_score: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.clarification_history is None:
            self.clarification_history = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LLMClarificationAgent:
    """Generates and manages clarification questions for ambiguous specs"""
    
    QUESTION_TEMPLATES = {
        "device_type": "I understand you want a {prev_guess}. Is this correct? Other options: {alternatives}",
        "dimensions": "Based on your description, I'm estimating {dimension_guess}. Does this sound right?",
        "materials": "For your use case, I'm suggesting {material}. Constraints: {constraints}. Agree?",
        "performance": "This design needs approximately {performance} to meet specs. Acceptable?",
        "budget": "Estimated cost: ${cost}. Budget OK? I can optimize for cost if needed.",
        "manufacturing": "I'm planning to manufacture this via {method}. Good for you?",
    }
    
    def __init__(self):
        self.device_categories = {
            "robot_arm": ["2-DOF", "3-DOF", "6-DOF", "collaborative"],
            "gripper": ["parallel_jaw", "suction", "multi_finger"],
            "actuator": ["linear", "rotary", "hybrid"],
            "assembly": ["3D_printer", "CNC", "robotic_cell"],
            "mechanism": ["gearbox", "bearing_assembly", "lattice_structure"],
        }
    
    def generate_clarification_questions(
        self, 
        partial_spec: Dict, 
        confidence: float,
        missing_fields: List[str]
    ) -> List[str]:
        """Generate clarification questions for uncertain fields"""
        questions = []
        
        # High priority: critical missing fields
        if confidence < 0.6:
            questions.append(
                f"Could you describe the primary function of this device?"
            )
        
        if "device_type" in missing_fields:
            device_guesses = ", ".join(self.device_categories.keys())
            questions.append(
                f"What type of device are we building? ({device_guesses})"
            )
        
        if "dimensions" in missing_fields or "reach" in missing_fields:
            questions.append(
                "What are the approximate dimensions or working space (in mm)?"
            )
        
        if "loads" in missing_fields:
            questions.append(
                "What's the expected payload or force this needs to handle?"
            )
        
        if "materials" in missing_fields:
            questions.append(
                "Any material preferences? (plastic, metal, composite, etc.)"
            )
        
        if "manufacturing" in missing_fields:
            questions.append(
                "How do you plan to manufacture this? (3D printing, CNC, assembled, etc.)"
            )
        
        return questions[:3]  # Return top 3 most important questions
    
    def assess_ambiguity(self, spec: Dict) -> Tuple[float, List[str]]:
        """
        Assess confidence level in extracted specification.
        Returns: (confidence_score: 0-1, missing_fields: List[str])
        """
        confidence = 1.0
        missing_fields = []
        
        # Check critical fields
        critical_fields = ["device_type", "dimensions", "loads", "materials"]
        for field in critical_fields:
            if field not in spec or spec[field] is None:
                missing_fields.append(field)
                confidence -= 0.15
        
        # Check secondary fields
        secondary_fields = ["manufacturing", "environment", "requirements"]
        for field in secondary_fields:
            if field not in spec or spec[field] is None:
                confidence -= 0.05
        
        # Reduce confidence if values are default/estimated
        if spec.get("dimensions", {}).get("_estimated"):
            confidence -= 0.1
        
        return max(0.0, confidence), missing_fields


class LLMRefinementEngine:
    """Refines specifications through iterative feedback and optimization suggestions"""
    
    OPTIMIZATION_RULES = {
        "lightweight": {
            "lattice_infill": 0.3,
            "target_volume_reduction": 0.4,
            "materials": ["composite", "aluminum", "titanium"],
        },
        "durable": {
            "material_safety_factor": 3.0,
            "manufacturing": "CNC",
            "materials": ["steel", "titanium"],
        },
        "cost_effective": {
            "lattice_infill": 0.2,
            "materials": ["PLA", "ABS", "aluminum"],
            "manufacturing": "FDM",
        },
        "high_precision": {
            "tolerance_mm": 0.1,
            "manufacturing": "CNC",
            "materials": ["aluminum", "steel"],
        },
        "rapid_prototyping": {
            "manufacturing": "FDM",
            "materials": ["PLA"],
            "iterative_design": True,
        }
    }
    
    def suggest_optimizations(
        self,
        current_spec: Dict,
        optimization_goal: Optional[str] = None,
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate optimization suggestions based on goals and constraints"""
        
        suggestions = {
            "material_changes": [],
            "manufacturing_changes": [],
            "geometry_changes": [],
            "component_alternatives": [],
            "estimated_improvements": {}
        }
        
        if not optimization_goal:
            return suggestions
        
        rules = self.OPTIMIZATION_RULES.get(optimization_goal, {})
        current_material = current_spec.get("materials", [None])[0]
        current_manufacturing = current_spec.get("manufacturing")
        
        # Material suggestions
        if current_material not in rules.get("materials", []):
            suggestions["material_changes"] = [
                {"from": current_material, "to": m, "benefit": optimization_goal}
                for m in rules.get("materials", [])
            ]
        
        # Manufacturing suggestions
        if current_manufacturing not in rules.get("manufacturing"):
            suggested_mfg = rules.get("manufacturing")
            suggestions["manufacturing_changes"] = {
                "from": current_manufacturing,
                "to": suggested_mfg,
                "reason": f"Better for {optimization_goal}"
            }
        
        # Geometry suggestions
        if optimization_goal == "lightweight":
            suggestions["geometry_changes"] = {
                "use_lattice": True,
                "infill_percent": rules.get("lattice_infill", 30),
                "target_reduction": rules.get("target_volume_reduction", 0.3)
            }
        
        # Estimate improvements
        suggestions["estimated_improvements"] = {
            "cost_reduction_percent": self._estimate_cost_reduction(optimization_goal),
            "weight_reduction_percent": self._estimate_weight_reduction(optimization_goal),
            "manufacturing_time_reduction_percent": self._estimate_time_reduction(optimization_goal),
        }
        
        return suggestions
    
    def _estimate_cost_reduction(self, goal: str) -> float:
        estimates = {
            "cost_effective": 0.35,
            "lightweight": 0.20,
            "durable": -0.15,
            "high_precision": -0.25,
        }
        return estimates.get(goal, 0.0)
    
    def _estimate_weight_reduction(self, goal: str) -> float:
        estimates = {
            "lightweight": 0.40,
            "cost_effective": 0.15,
            "durable": 0.05,
            "high_precision": 0.0,
        }
        return estimates.get(goal, 0.0)
    
    def _estimate_time_reduction(self, goal: str) -> float:
        estimates = {
            "rapid_prototyping": 0.60,
            "cost_effective": 0.30,
            "lightweight": 0.10,
            "durable": -0.20,
            "high_precision": -0.30,
        }
        return estimates.get(goal, 0.0)


class AdvancedLLMEngine:
    """
    Main LLM engine integrating natural language processing,
    context management, and iterative refinement
    """
    
    def __init__(self):
        self.clarification_agent = LLMClarificationAgent()
        self.refinement_engine = LLMRefinementEngine()
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
    def start_conversation(
        self,
        session_id: str,
        initial_prompt: str
    ) -> Tuple[ConversationContext, Optional[List[str]]]:
        """
        Start a new conversation session.
        
        Returns:
            (context, clarification_questions)
            - context: Conversation state
            - clarification_questions: List of questions if confidence is low
        """
        context = ConversationContext(session_id=session_id, initial_prompt=initial_prompt)
        self.conversation_contexts[session_id] = context
        
        logger.info(f"Started conversation session: {session_id}")
        logger.info(f"Initial prompt: {initial_prompt[:100]}...")
        
        return context, None
    
    async def process_prompt(
        self,
        session_id: str,
        prompt: str,
        parser: 'PromptParser'
    ) -> Dict[str, Any]:
        """
        Process user prompt through LLM pipeline with context awareness.
        
        Flow:
        1. Update context
        2. Parse prompt using PromptParser
        3. Assess confidence and ambiguities
        4. Generate clarification questions if needed
        5. Store in context
        """
        context = self.conversation_contexts.get(session_id)
        if not context:
            context = ConversationContext(session_id=session_id, initial_prompt=prompt)
            self.conversation_contexts[session_id] = context
        
        # Parse the prompt
        try:
            spec = await parser.parse(prompt)
        except Exception as e:
            logger.error(f"Failed to parse prompt: {e}")
            return {
                "success": False,
                "error": str(e),
                "clarification_needed": True,
                "questions": [
                    "I had trouble understanding your request. Could you rephrase it?",
                    "What type of device are you trying to create?",
                    "What's the main purpose or function you need?"
                ]
            }
        
        # Assess confidence
        confidence, missing_fields = self.clarification_agent.assess_ambiguity(spec)
        
        # Generate clarification questions if needed
        clarification_questions = None
        if confidence < 0.7:
            clarification_questions = self.clarification_agent.generate_clarification_questions(
                spec,
                confidence,
                missing_fields
            )
        
        # Update context
        context.specification = spec
        context.confidence_score = confidence
        context.device_type = spec.get("device_type")
        
        result = {
            "success": True,
            "specification": spec,
            "confidence_score": confidence,
            "clarification_needed": confidence < 0.7,
            "clarification_questions": clarification_questions,
            "missing_fields": missing_fields,
        }
        
        logger.info(f"Processed prompt with confidence: {confidence:.2%}")
        return result
    
    async def refine_specification(
        self,
        session_id: str,
        feedback: str,
        optimization_goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refine specification based on user feedback or optimization goal.
        """
        context = self.conversation_contexts.get(session_id)
        if not context or not context.specification:
            return {"error": "No active specification to refine"}
        
        context.refinement_iterations += 1
        if context.refinement_iterations > context.max_iterations:
            return {
                "warning": "Max refinement iterations reached",
                "final_specification": context.specification
            }
        
        # Generate optimization suggestions
        suggestions = self.refinement_engine.suggest_optimizations(
            context.specification,
            optimization_goal
        )
        
        # Apply suggestions to specification if optimization goal provided
        if optimization_goal:
            updated_spec = self._apply_optimization_suggestions(
                context.specification,
                suggestions
            )
            context.specification = updated_spec
        
        return {
            "success": True,
            "iteration": context.refinement_iterations,
            "suggestions": suggestions,
            "updated_specification": context.specification,
            "feedback_received": feedback,
        }
    
    def _apply_optimization_suggestions(
        self,
        spec: Dict,
        suggestions: Dict
    ) -> Dict:
        """Apply optimization suggestions to specification"""
        updated_spec = spec.copy()
        
        # Apply material changes
        if suggestions.get("material_changes"):
            first_suggestion = suggestions["material_changes"][0]
            updated_spec["materials"] = [first_suggestion["to"]]
            logger.info(f"Applied material change: {first_suggestion['from']} → {first_suggestion['to']}")
        
        # Apply manufacturing changes
        if suggestions.get("manufacturing_changes"):
            updated_spec["manufacturing"] = suggestions["manufacturing_changes"]["to"]
            logger.info(f"Applied manufacturing change: {suggestions['manufacturing_changes']['to']}")
        
        # Apply geometry changes
        if suggestions.get("geometry_changes"):
            if not updated_spec.get("requirements"):
                updated_spec["requirements"] = {}
            updated_spec["requirements"].update(suggestions["geometry_changes"])
            logger.info("Applied geometry changes for lightweighting")
        
        return updated_spec
    
    async def handle_design_feedback(
        self,
        session_id: str,
        feedback_type: str,  # "like", "dislike", "modify", "simplify", "complex"
        feedback_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle user feedback on current design.
        
        feedback_type options:
        - "like": User approves design
        - "dislike": User wants changes
        - "modify": Specific modifications requested
        - "simplify": Make design simpler
        - "complex": Make design more complex/featured
        """
        context = self.conversation_contexts.get(session_id)
        if not context or not context.specification:
            return {"error": "No active design"}
        
        responses = {
            "like": {
                "message": "Great! Ready to generate CAD files and BOM?",
                "next_steps": ["generate_cad", "generate_bom", "export"]
            },
            "dislike": {
                "message": "I understand. What specifically would you like to change?",
                "next_steps": ["clarification"],
                "suggestions": self.refinement_engine.suggest_optimizations(
                    context.specification
                )
            },
            "modify": {
                "message": f"Got it. Modifying design based on: {feedback_text}",
                "next_steps": ["refinement"],
            },
            "simplify": {
                "message": "Simplifying design for cost-effectiveness...",
                "next_steps": ["optimization"],
                "optimization": "cost_effective"
            },
            "complex": {
                "message": "Adding advanced features...",
                "next_steps": ["optimization"],
                "optimization": "high_precision"
            }
        }
        
        response = responses.get(feedback_type, {"error": "Unknown feedback type"})
        context.clarification_history.append({
            "type": feedback_type,
            "text": feedback_text,
            "timestamp": str(asyncio.get_event_loop().time())
        })
        
        return response
    
    def get_conversation_state(self, session_id: str) -> Optional[Dict]:
        """Retrieve full conversation state"""
        context = self.conversation_contexts.get(session_id)
        if not context:
            return None
        return context.to_dict()
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history"""
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
            logger.info(f"Cleared conversation: {session_id}")
            return True
        return False


# Global engine instance
_llm_engine = None


def get_llm_engine() -> AdvancedLLMEngine:
    """Get or create global LLM engine instance"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = AdvancedLLMEngine()
        logger.info("Initialized AdvancedLLMEngine")
    return _llm_engine
