"""
LLM Engine Integration Examples

Demonstrates:
1. Basic prompt processing
2. Iterative refinement with clarifications
3. Design optimization
4. Full workflow execution
5. Real-time WebSocket interaction
"""

import asyncio
import json
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Example 1: Basic Prompt Processing
# ============================================================================

async def example_basic_prompt_processing():
    """Example 1: Simple prompt → specification"""
    logger.info("=" * 70)
    logger.info("Example 1: Basic Prompt Processing")
    logger.info("=" * 70)
    
    from backend.cem_engine.prompt_parser import PromptParser, NaturalLanguageAnalyzer
    from backend.cem_engine.llm_engine import AdvancedLLMEngine
    
    # Initialize engines
    llm_engine = AdvancedLLMEngine()
    parser = PromptParser()  # Note: Requires HF model configuration
    analyzer = NaturalLanguageAnalyzer()
    
    # User's natural language prompt
    prompt = """
    I need to build a lightweight 3-DOF robotic arm for pick-and-place operations.
    The arm should have a 500mm reach, be able to handle 2kg payload, and be
    cost-effective. I'm planning to 3D print it with PLA.
    """
    
    session_id = "example_1_session"
    
    logger.info(f"User prompt: {prompt.strip()}")
    
    # Step 1: Start conversation
    context, _ = llm_engine.start_conversation(session_id, prompt)
    logger.info(f"Session started: {session_id}")
    
    # Step 2: Analyze intent before LLM processing
    intent = analyzer.extract_intent(prompt)
    logger.info(f"Intent Analysis:")
    logger.info(f"  - Detected Device Type: {intent['detected_device_type']}")
    logger.info(f"  - Optimization Goals: {intent['optimization_goals']}")
    logger.info(f"  - Specificity Score: {intent['specificity']:.2%}")
    
    # Step 3: Process through LLM
    try:
        result = await llm_engine.process_prompt(session_id, prompt, parser)
        
        if result['success']:
            spec = result['specification']
            logger.info(f"\nParsed Specification:")
            logger.info(f"  - Device Type: {spec.get('device_type', 'N/A')}")
            logger.info(f"  - Reach: {spec.get('dimensions', {}).get('reach_mm', 'N/A')}mm")
            logger.info(f"  - Payload: {spec.get('loads', {}).get('payload_kg', 'N/A')}kg")
            logger.info(f"  - Materials: {spec.get('materials', [])}")
            logger.info(f"  - Manufacturing: {spec.get('manufacturing', 'N/A')}")
            logger.info(f"\nConfidence Score: {result['confidence_score']:.2%}")
            logger.info(f"Clarification Needed: {result['clarification_needed']}")
            
            if result['clarification_questions']:
                logger.info(f"\nClarification Questions:")
                for i, q in enumerate(result['clarification_questions'], 1):
                    logger.info(f"  {i}. {q}")
        else:
            logger.error(f"Failed to process prompt: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        logger.info("Note: This example requires Hugging Face model configuration")
        logger.info("Set HF_MODEL_NAME env variable to enable")


# ============================================================================
# Example 2: Iterative Refinement with Clarifications
# ============================================================================

async def example_iterative_refinement():
    """Example 2: Ask clarifications → refine specification"""
    logger.info("\n" + "=" * 70)
    logger.info("Example 2: Iterative Refinement with Clarifications")
    logger.info("=" * 70)
    
    from backend.cem_engine.llm_engine import AdvancedLLMEngine, LLMClarificationAgent
    
    llm_engine = AdvancedLLMEngine()
    clarification_agent = LLMClarificationAgent()
    
    session_id = "example_2_session"
    
    # Simulate incomplete specification
    partial_spec = {
        "device_type": "gripper",
        "dimensions": {"reach_mm": 100},
        # Missing: loads, materials, manufacturing details
    }
    
    logger.info(f"Initial (Incomplete) Specification: {json.dumps(partial_spec, indent=2)}")
    
    # Step 1: Assess ambiguity
    confidence, missing = clarification_agent.assess_ambiguity(partial_spec)
    logger.info(f"\nConfidence Score: {confidence:.2%}")
    logger.info(f"Missing Fields: {missing}")
    
    # Step 2: Generate clarification questions
    if confidence < 0.7:
        questions = clarification_agent.generate_clarification_questions(
            partial_spec,
            confidence,
            missing
        )
        logger.info(f"\nGenerated Clarification Questions:")
        for i, q in enumerate(questions, 1):
            logger.info(f"  {i}. {q}")
        
        # Simulate user answers
        user_answers = {
            "gripper_type": "parallel_jaw",
            "grip_force": "50N",
            "max_weight": "5kg",
            "material": "aluminum",
            "manufacturing": "CNC"
        }
        
        logger.info(f"\nSimulated User Answers:")
        for key, value in user_answers.items():
            logger.info(f"  {key}: {value}")
        
        # Create enhanced specification
        enhanced_spec = {**partial_spec}
        enhanced_spec.update({
            "components": [{"type": "servo", "grip_force_n": 50}],
            "materials": ["aluminum"],
            "manufacturing": "CNC",
            "loads": {"max_force_n": 50}
        })
        
        # Re-assess
        new_confidence, _ = clarification_agent.assess_ambiguity(enhanced_spec)
        logger.info(f"\nUpdated Confidence Score: {new_confidence:.2%}")
        logger.info(f"Ready for workflow: {new_confidence > 0.8}")


# ============================================================================
# Example 3: Design Optimization
# ============================================================================

async def example_design_optimization():
    """Example 3: Optimize design for different goals"""
    logger.info("\n" + "=" * 70)
    logger.info("Example 3: Design Optimization")
    logger.info("=" * 70)
    
    from backend.cem_engine.llm_engine import LLMRefinementEngine
    
    refinement_engine = LLMRefinementEngine()
    
    # Base specification
    current_spec = {
        "device_type": "motor_bracket",
        "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 30},
        "materials": ["ABS"],
        "manufacturing": "FDM",
        "requirements": {"infill_percent": 100}
    }
    
    logger.info(f"Base Specification:")
    logger.info(f"  - Material: {current_spec['materials'][0]}")
    logger.info(f"  - Manufacturing: {current_spec['manufacturing']}")
    logger.info(f"  - Infill: {current_spec['requirements']['infill_percent']}%")
    
    # Test different optimization goals
    goals = ["lightweight", "cost_effective", "durable", "high_precision"]
    
    for goal in goals:
        logger.info(f"\n--- Optimizing for: {goal.upper()} ---")
        
        suggestions = refinement_engine.suggest_optimizations(
            current_spec,
            goal
        )
        
        if suggestions["material_changes"]:
            for change in suggestions["material_changes"]:
                logger.info(f"Material: {change['from']} → {change['to']}")
        
        if suggestions["manufacturing_changes"]:
            logger.info(f"Manufacturing: {suggestions['manufacturing_changes']['to']}")
        
        if suggestions["geometry_changes"]:
            logger.info(f"Geometry: {suggestions['geometry_changes']}")
        
        logger.info(f"Estimated Improvements:")
        for key, value in suggestions["estimated_improvements"].items():
            logger.info(f"  - {key}: {value:+.0%}")


# ============================================================================
# Example 4: Design Feedback Handling
# ============================================================================

async def example_design_feedback():
    """Example 4: Handle different types of user feedback"""
    logger.info("\n" + "=" * 70)
    logger.info("Example 4: Design Feedback Handling")
    logger.info("=" * 70)
    
    from backend.cem_engine.llm_engine import AdvancedLLMEngine
    
    llm_engine = AdvancedLLMEngine()
    session_id = "example_4_session"
    
    # Set up a dummy specification
    llm_engine.conversation_contexts[session_id] = type('obj', (object,), {
        'specification': {'device_type': 'bracket', 'materials': ['ABS']},
        'clarification_history': []
    })
    
    feedback_types = [
        ("like", None),
        ("dislike", "The design is too bulky"),
        ("modify", "Make it 20% smaller"),
        ("simplify", None),
        ("complex", None),
    ]
    
    for feedback_type, text in feedback_types:
        logger.info(f"\nFeedback Type: {feedback_type}")
        if text:
            logger.info(f"  Text: {text}")
        
        response = await llm_engine.handle_design_feedback(
            session_id,
            feedback_type,
            text
        )
        
        logger.info(f"Response: {response['message']}")
        if 'next_steps' in response:
            logger.info(f"Next Steps: {response['next_steps']}")


# ============================================================================
# Example 5: Conversation State Management
# ============================================================================

async def example_conversation_state():
    """Example 5: Manage and retrieve conversation state"""
    logger.info("\n" + "=" * 70)
    logger.info("Example 5: Conversation State Management")
    logger.info("=" * 70)
    
    from backend.cem_engine.llm_engine import AdvancedLLMEngine, ConversationContext
    
    llm_engine = AdvancedLLMEngine()
    session_id = "example_5_session"
    
    # Create conversation
    initial_prompt = "Build a 2kg gripper with low cost"
    context, _ = llm_engine.start_conversation(session_id, initial_prompt)
    
    logger.info(f"Created session: {session_id}")
    logger.info(f"Initial prompt: {initial_prompt}")
    
    # Simulate some refinements
    state = llm_engine.get_conversation_state(session_id)
    logger.info(f"\nCurrent State:")
    logger.info(f"  - Session ID: {state['session_id']}")
    logger.info(f"  - Device Type: {state['device_type']}")
    logger.info(f"  - Refinements: {state['refinement_iterations']}")
    logger.info(f"  - Confidence: {state['confidence_score']:.2%}")
    
    # Add to history
    context.clarification_history.append({
        "type": "clarification",
        "question": "Parallel jaw or suction?",
        "answer": "Parallel jaw"
    })
    
    state = llm_engine.get_conversation_state(session_id)
    logger.info(f"\nAfter adding history:")
    logger.info(f"  - History items: {len(state['clarification_history'])}")
    
    # Clear session
    llm_engine.clear_conversation(session_id)
    logger.info(f"\nCleared session: {session_id}")
    
    state = llm_engine.get_conversation_state(session_id)
    logger.info(f"Session after clear: {state}")


# ============================================================================
# Example 6: Integration with CEM Orchestrator
# ============================================================================

async def example_with_orchestrator():
    """Example 6: Full workflow from prompt to result"""
    logger.info("\n" + "=" * 70)
    logger.info("Example 6: Full Workflow Integration")
    logger.info("=" * 70)
    
    from backend.cem_engine.llm_engine import AdvancedLLMEngine
    from backend.cem_engine.orchestrator import EngineOrchestrator
    
    llm_engine = AdvancedLLMEngine()
    orchestrator = EngineOrchestrator(csharp_project_path="csharp_runtime")
    
    session_id = "example_6_session"
    prompt = "Create a lightweight drone landing pad with aluminum frame"
    
    logger.info(f"User Prompt: {prompt}")
    
    # Step 1: LLM processes the prompt
    logger.info("\nStep 1: LLM Processing...")
    llm_engine.start_conversation(session_id, prompt)
    
    try:
        result = await llm_engine.process_prompt(session_id, prompt, orchestrator.parser)
        
        if result['success']:
            spec = result['specification']
            logger.info(f"✓ Specification parsed with {result['confidence_score']:.0%} confidence")
            
            # Step 2-8: Orchestrator workflow
            logger.info("\nStep 2-8: CEM Orchestrator Workflow...")
            logger.info("  Step 2: Sourcing components...")
            logger.info("  Step 3: Recommending shapes...")
            logger.info("  Step 4: Calculating lattice...")
            logger.info("  Step 5: Validating physics...")
            logger.info("  Step 6: Generating C# code...")
            logger.info("  Step 7: Executing PicoGK...")
            logger.info("  Step 8: Generating BOM...")
            
            logger.info("\n✓ Workflow would complete with:")
            logger.info("  - STL file for 3D printing")
            logger.info("  - CAD representation")
            logger.info("  - Bill of Materials with pricing")
            logger.info("  - Design analysis reports")
        else:
            logger.error(f"Processing failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Note: Full workflow requires Hugging Face model and C# toolchain")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run all examples"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "LLM Engine Integration Examples" + " " * 21 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    examples = [
        ("Basic Prompt Processing", example_basic_prompt_processing),
        ("Iterative Refinement", example_iterative_refinement),
        ("Design Optimization", example_design_optimization),
        ("Design Feedback", example_design_feedback),
        ("Conversation State", example_conversation_state),
        ("Full Workflow", example_with_orchestrator),
    ]
    
    for name, example_fn in examples:
        try:
            await example_fn()
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
        
        logger.info("\n")


if __name__ == "__main__":
    asyncio.run(main())
