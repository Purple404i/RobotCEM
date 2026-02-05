"""
RobotCEM API Routes

Endpoints for:
- Prompt processing with LLM
- Device specification management
- Design refinement and optimization
- Workflow orchestration
- BOM and pricing
"""

from fastapi import APIRouter, HTTPException, WebSocket, Query, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import uuid
import os

from backend.cem_engine.orchestrator import EngineOrchestrator
from backend.cem_engine.llm_engine import get_llm_engine
from backend.cem_engine.prompt_parser import PromptParser
from backend.storage.database import SessionLocal

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["cem"])

# Initialize engines
_orchestrator = None
_llm_engine = get_llm_engine()


def get_orchestrator() -> EngineOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EngineOrchestrator(
            hf_model_name=None,
            csharp_project_path="csharp_runtime",
            output_dir="backend/outputs",
            db_session=SessionLocal()
        )
    return _orchestrator


# ============================================================================
# Request/Response Models
# ============================================================================

class PromptRequest(BaseModel):
    """Input: Natural language prompt from user"""
    prompt: str = Field(..., description="Natural language description of device to create")
    session_id: Optional[str] = Field(default=None, description="Session ID for context management")
    optimization_goal: Optional[str] = Field(
        default=None, 
        description="lightweight|cost_effective|durable|high_precision|rapid_prototyping"
    )


class SpecificationResponse(BaseModel):
    """Output: Parsed specification from prompt"""
    success: bool
    specification: Optional[Dict[str, Any]] = None
    confidence_score: float
    clarification_needed: bool
    clarification_questions: Optional[List[str]] = None
    missing_fields: Optional[List[str]] = None
    device_type: Optional[str] = None
    optimization_goals: Optional[List[str]] = None


class DesignFeedback(BaseModel):
    """User feedback on current design"""
    session_id: str
    feedback_type: str = Field(
        ..., 
        description="like|dislike|modify|simplify|complex"
    )
    feedback_text: Optional[str] = Field(None, description="Optional detailed feedback")


class OptimizationRequest(BaseModel):
    """Request to optimize current design"""
    session_id: str
    optimization_goal: str = Field(
        ..., 
        description="lightweight|cost_effective|durable|high_precision|rapid_prototyping"
    )
    constraints: Optional[Dict[str, Any]] = None


class RefinementResponse(BaseModel):
    """Output: Refinement suggestions and updated spec"""
    success: bool
    iteration: int
    suggestions: Dict[str, Any]
    updated_specification: Optional[Dict[str, Any]] = None
    estimated_improvements: Optional[Dict[str, str]] = None


class WorkflowExecutionRequest(BaseModel):
    """Request to execute full CEM workflow"""
    session_id: str
    output_name: str = Field(default="generated_design", description="Name for output files")
    skip_steps: Optional[List[int]] = Field(default=None, description="Steps to skip (1-8)")


class WorkflowResult(BaseModel):
    """Result of complete workflow"""
    success: bool
    workflow_id: str
    steps_completed: int
    specification: Optional[Dict[str, Any]] = None
    sourcing_summary: Optional[Dict[str, Any]] = None
    validation_report: Optional[Dict[str, Any]] = None
    generation_status: Optional[Dict[str, Any]] = None
    bom: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health", tags=["health"])
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "llm_engine": "initialized",
        "orchestrator": "ready"
    }


# ============================================================================
# Core LLM + Specification Routes
# ============================================================================

@router.post("/prompt", response_model=SpecificationResponse)
async def process_prompt(request: PromptRequest):
    """
    Process natural language prompt through LLM engine.
    
    Returns structured specification with confidence score and clarification questions if needed.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Start conversation
        _llm_engine.start_conversation(session_id, request.prompt)
        
        # Get parser and process prompt
        orchestrator = get_orchestrator()
        parser = orchestrator.parser
        
        result = await _llm_engine.process_prompt(session_id, request.prompt, parser)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to parse prompt"))
        
        spec = result.get("specification", {})
        intent = spec.get("_intent_analysis", {})
        
        return SpecificationResponse(
            success=True,
            specification=spec,
            confidence_score=result.get("confidence_score", 0.0),
            clarification_needed=result.get("clarification_needed", False),
            clarification_questions=result.get("clarification_questions"),
            missing_fields=result.get("missing_fields"),
            device_type=intent.get("detected_device_type"),
            optimization_goals=intent.get("optimization_goals")
        )
        
    except Exception as e:
        logger.error(f"Prompt processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/clarification", response_model=SpecificationResponse)
async def answer_clarification(
    session_id: str = Query(..., description="Session ID"),
    answer: str = Body(..., description="Answer to clarification question")
):
    """
    Answer clarification questions to refine specification.
    """
    try:
        orchestrator = get_orchestrator()
        parser = orchestrator.parser
        
        result = await _llm_engine.process_prompt(session_id, answer, parser)
        
        spec = result.get("specification", {})
        intent = spec.get("_intent_analysis", {})
        
        return SpecificationResponse(
            success=True,
            specification=spec,
            confidence_score=result.get("confidence_score", 0.0),
            clarification_needed=result.get("clarification_needed", False),
            clarification_questions=result.get("clarification_questions"),
            missing_fields=result.get("missing_fields"),
            device_type=intent.get("detected_device_type"),
            optimization_goals=intent.get("optimization_goals")
        )
        
    except Exception as e:
        logger.error(f"Clarification handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{session_id}")
async def get_conversation_state(session_id: str):
    """
    Retrieve full conversation state and context.
    """
    state = _llm_engine.get_conversation_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


# ============================================================================
# Design Refinement Routes
# ============================================================================

@router.post("/design/feedback")
async def provide_design_feedback(request: DesignFeedback):
    """
    Provide feedback on current design (like, dislike, modify, simplify, complex).
    """
    try:
        response = await _llm_engine.handle_design_feedback(
            request.session_id,
            request.feedback_type,
            request.feedback_text
        )
        return response
    except Exception as e:
        logger.error(f"Feedback handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/optimize", response_model=RefinementResponse)
async def optimize_design(request: OptimizationRequest):
    """
    Optimize design for specific goal (lightweight, cost_effective, durable, etc.).
    """
    try:
        result = await _llm_engine.refine_specification(
            request.session_id,
            feedback=f"Optimize for {request.optimization_goal}",
            optimization_goal=request.optimization_goal
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return RefinementResponse(
            success=result.get("success", True),
            iteration=result.get("iteration", 0),
            suggestions=result.get("suggestions", {}),
            updated_specification=result.get("updated_specification"),
            estimated_improvements=result.get("suggestions", {}).get("estimated_improvements")
        )
        
    except Exception as e:
        logger.error(f"Design optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Orchestration Routes
# ============================================================================

@router.post("/workflow/execute", response_model=WorkflowResult)
async def execute_full_workflow(request: WorkflowExecutionRequest):
    """
    Execute complete 8-step CEM workflow:
    1. Parse prompt
    2. Source components
    3. Recommend shapes
    4. Calculate lattices
    5. Validate physics
    6. Generate C# code
    7. Execute PicoGK
    8. Generate BOM
    """
    try:
        workflow_id = str(uuid.uuid4())
        conversation_state = _llm_engine.get_conversation_state(request.session_id)
        
        if not conversation_state or not conversation_state.get("specification"):
            raise HTTPException(status_code=400, detail="No specification in session")
        
        # Build prompt from specification for orchestrator
        spec = conversation_state["specification"]
        device_type = spec.get("device_type", "custom")
        
        # Execute workflow
        orchestrator = get_orchestrator()
        result = await orchestrator.run_from_prompt(
            prompt=f"Create a {device_type} device based on: {spec}",
            output_name=request.output_name
        )
        
        return WorkflowResult(
            success=result.get("generation", {}).get("success", False),
            workflow_id=workflow_id,
            steps_completed=8 if result.get("bom") else 7,
            specification=result.get("spec"),
            sourcing_summary=result.get("sourcing_summary"),
            validation_report=result.get("validation"),
            generation_status=result.get("generation"),
            bom=result.get("bom"),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return WorkflowResult(
            success=False,
            workflow_id=str(uuid.uuid4()),
            steps_completed=0,
            errors=[str(e)]
        )


# ============================================================================
# WebSocket for Real-time Interaction
# ============================================================================

@router.websocket("/ws/design/{session_id}")
async def websocket_design_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time design iteration.
    
    Supports:
    - Real-time specification updates
    - Design feedback streaming
    - Live optimization suggestions
    - Progress updates during workflow
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "refine":
                # Refinement request
                result = await _llm_engine.refine_specification(
                    session_id,
                    data.get("feedback", ""),
                    data.get("optimization_goal")
                )
                await websocket.send_json({
                    "type": "refinement_complete",
                    "data": result
                })
            
            elif message_type == "feedback":
                # Design feedback
                result = await _llm_engine.handle_design_feedback(
                    session_id,
                    data.get("feedback_type"),
                    data.get("text")
                )
                await websocket.send_json({
                    "type": "feedback_received",
                    "data": result
                })
            
            elif message_type == "status_request":
                # Get current state
                state = _llm_engine.get_conversation_state(session_id)
                await websocket.send_json({
                    "type": "status_update",
                    "data": state
                })
            
            elif message_type == "close":
                break
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)


# ============================================================================
# Test Routes
# ============================================================================

@router.get("/render/{job_id}")
async def get_blender_render(job_id: str):
    """
    Generate and return a high-quality Blender render of the model.
    """
    try:
        orchestrator = get_orchestrator()
        # Find the STL in the output dir
        stl_path = os.path.join(orchestrator.output_dir, f"{job_id}.stl")
        if not os.path.exists(stl_path):
            # Fallback to current design if job_id matches
            if orchestrator.current_design and orchestrator.current_design.get("generation", {}).get("stl_path"):
                 stl_path = orchestrator.current_design["generation"]["stl_path"]
            else:
                raise HTTPException(status_code=404, detail="STL not found for this job")

        output_image = os.path.join(orchestrator.output_dir, f"{job_id}_render.png")

        # Trigger render
        result = await orchestrator.blender_sim.render_model(stl_path, output_image)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return FileResponse(output_image)

    except Exception as e:
        logger.error(f"Rendering failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_route():
    return {"message": "Routes working"}


@router.post("/test/prompt")
async def test_prompt_parsing():
    """Test prompt parsing with sample prompt"""
    sample_prompt = "Create a lightweight 3-DOF robot arm with 500mm reach for pick-and-place operations"
    
    request = PromptRequest(
        prompt=sample_prompt,
        optimization_goal="lightweight"
    )
    
    return await process_prompt(request)
