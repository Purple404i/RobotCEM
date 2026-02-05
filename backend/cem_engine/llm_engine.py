"""
Advanced LLM Engine for RobotCEM using Aurora Ollama model.

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
from backend.utils.ollama_client import OllamaClient

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


class AdvancedLLMEngine:
    """
    Main LLM engine integrating natural language processing via Ollama (Aurora),
    context management, and iterative refinement.
    """
    
    SYSTEM_PROMPT = """You are Aurora, an expert roboticist and mechanical engineer.
Your goal is to help users design scientific and accurate robotic components.
When asked to create a device, you should provide a structured JSON specification including:
- device_type: The type of device (e.g., robot_arm, gripper, etc.)
- dimensions: Physical dimensions in mm
- loads: Expected payloads or forces
- motion: Degrees of freedom or movement range
- materials: Suggested materials
- manufacturing: Preferred manufacturing method (e.g., FDM, SLS, CNC)
- components: List of non-printable parts needed (servos, bearings, etc.)
- environment: Operating conditions

Always be scientifically accurate. If a design is physically impossible or risky, explain why and suggest improvements.
"""

    def __init__(self, model: str = "aurora"):
        self.client = OllamaClient(model=model)
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
    def start_conversation(
        self,
        session_id: str,
        initial_prompt: str
    ) -> ConversationContext:
        """Start a new conversation session."""
        context = ConversationContext(session_id=session_id, initial_prompt=initial_prompt)
        self.conversation_contexts[session_id] = context
        logger.info(f"Started conversation session: {session_id}")
        return context
    
    async def process_prompt(
        self,
        session_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Process user prompt through Aurora LLM."""
        context = self.conversation_contexts.get(session_id)
        if not context:
            context = self.start_conversation(session_id, prompt)
        
        # Prepare messages for chat
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        # Request JSON output
        response = await self.client.chat(messages, format="json")
        
        if "error" in response:
            logger.error(f"LLM Error: {response['error']}")
            return {"success": False, "error": response["error"]}
        
        try:
            content = response["message"]["content"]
            spec = json.loads(content)

            # Update context
            context.specification = spec
            context.device_type = spec.get("device_type")

            return {
                "success": True,
                "specification": spec,
                "confidence_score": 0.9, # Aurora is confident
                "clarification_needed": False
            }
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {"success": False, "error": "Invalid response format from LLM"}

    async def analyze_simulation(self, stl_data: Dict, sim_results: Dict) -> Dict[str, Any]:
        """Analyze simulation results and provide scientific insights."""
        prompt = f"""Analyze the following simulation results for a 3D model.
STL Analysis: {json.dumps(stl_data)}
Simulation Results: {json.dumps(sim_results)}

Provide a scientific analysis of why it might have failed or how it can be improved.
Output should be a JSON with 'analysis' (string) and 'suggested_fixes' (list of specific parameter changes).
"""
        response = await self.client.generate(prompt, system=self.SYSTEM_PROMPT, format="json")
        if "error" in response:
            return {"error": response["error"]}
        
        return json.loads(response["response"])

    def get_conversation_state(self, session_id: str) -> Optional[Dict]:
        """Retrieve full conversation state"""
        context = self.conversation_contexts.get(session_id)
        if not context:
            return None
        return context.to_dict()


# Global engine instance
_llm_engine = None


def get_llm_engine() -> AdvancedLLMEngine:
    """Get or create global LLM engine instance"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = AdvancedLLMEngine()
        logger.info("Initialized AdvancedLLMEngine with Aurora/Ollama")
    return _llm_engine
