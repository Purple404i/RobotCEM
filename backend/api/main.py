from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from pathlib import Path
import uuid

from ..cem_engine.core import CEMEngine, DesignSpecification
from ..cem_engine.llm_engine import get_llm_engine
from ..cem_engine.code_generator import CSharpCodeGenerator
from ..picogk_bridge.executor import PicoGKExecutor
from ..intelligence.material_pricing import MaterialPricingEngine
from ..tools.routes import router as tools_router
from ..config import CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Robot CEM API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Tool Server routes
app.include_router(tools_router)

# Initialize engines with config from config.py
# Use LLM engine instead of HuggingFace models
llm_engine = get_llm_engine()
logger.info("✓ LLM engine initialized")

cem_engine = CEMEngine(None, CONFIG)
code_generator = CSharpCodeGenerator(CONFIG["template_dir"])
picogk_executor = PicoGKExecutor(
    CONFIG["csharp_project_path"],
    CONFIG["output_dir"]
)
material_engine = MaterialPricingEngine(CONFIG)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

manager = ConnectionManager()

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = {}

class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str

class DesignStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: str
    specification: Optional[Dict] = None
    validation: Optional[Dict] = None
    stl_url: Optional[str] = None
    bom: Optional[Dict] = None
    error: Optional[str] = None

# In-memory job storage (use Redis in production)
jobs_db: Dict[str, DesignStatus] = {}

# Routes
@app.get("/")
async def root():
    return {"message": "Robot CEM API v1.0.0", "status": "operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engines": {
        "cem": "ready",
        "picogk": "ready",
        "material_pricing": "ready"
    }}

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_design(request: GenerateRequest):
    """Start design generation job"""
    
    job_id = str(uuid.uuid4())
    
    jobs_db[job_id] = DesignStatus(
        job_id=job_id,
        status="queued",
        progress=0,
        current_step="Initializing"
    )
    logger.info(f"Job {job_id} enqueued by user {request.user_id}")
    
    # Start background task
    task = asyncio.create_task(process_design_job(job_id, request))
    logger.info(f"Background task started for job {job_id}: {task.get_name() if hasattr(task, 'get_name') else task}")
    
    return GenerateResponse(
        job_id=job_id,
        status="queued",
        message="Design generation started"
    )

@app.get("/api/status/{job_id}", response_model=DesignStatus)
async def get_status(job_id: str):
    """Get job status"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs_db[job_id]

@app.get("/api/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """Download generated STL or other files"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    file_path = Path(CONFIG["output_dir"]) / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for real-time updates"""
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.get("/api/materials")
async def list_materials():
    """List available materials with properties"""
    return cem_engine.material_database

@app.post("/api/validate")
async def validate_specification(spec: Dict):
    """Validate a design specification"""
    
    design_spec = DesignSpecification(**spec)
    validation = cem_engine.validate_design(design_spec)
    
    return {
        "is_valid": validation.is_valid,
        "errors": validation.errors,
        "warnings": validation.warnings,
        "suggested_fixes": validation.suggested_fixes
    }

@app.post("/api/component-price")
async def get_component_price(mpn: str, quantity: int = 1):
    """Get real-time component pricing"""
    
    price = await material_engine.get_component_pricing(mpn, quantity)
    
    if not price:
        raise HTTPException(status_code=404, detail="Component not found")
    
    return {
        "mpn": price.mpn,
        "supplier": price.supplier,
        "price_usd": price.price_usd,
        "stock": price.stock_quantity,
        "moq": price.moq,
        "lead_time_days": price.lead_time_days
    }

async def process_design_job(job_id: str, request: GenerateRequest):
    """Background task to process design generation"""
    
    try:
        # Update status
        await update_job_status(
            job_id, "parsing", 10, "Parsing prompt..."
        )
        
        # 1. Parse prompt
        spec = await cem_engine.parse_prompt(request.prompt)
        
        jobs_db[job_id].specification = spec.to_dict()
        
        await update_job_status(
            job_id, "validating", 20, "Validating design..."
        )
        
        # 2. Validate
        validation = cem_engine.validate_design(spec)
        
        jobs_db[job_id].validation = {
            "is_valid": validation.is_valid,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "suggested_fixes": validation.suggested_fixes
        }
        
        if not validation.is_valid:
            raise Exception(f"Validation failed: {', '.join(validation.errors)}")
        
        await update_job_status(
            job_id, "optimizing", 30, "Optimizing design..."
        )
        
        # 3. Optimize
        optimized_spec = cem_engine.optimize_design(spec)
        
        await update_job_status(
            job_id, "generating_code", 40, "Generating C# code..."
        )
        
        # 4. Generate C# code
        csharp_code = code_generator.generate(
            optimized_spec.to_dict(),
            optimized_spec.device_type
        )
        
        await update_job_status(
            job_id, "compiling", 50, "Compiling geometry..."
        )
        
        # 5. Execute PicoGK
        result = await picogk_executor.compile_and_run(
            csharp_code,
            job_id
        )
        
        if not result["success"]:
            raise Exception(f"PicoGK execution failed: {result.get('error')}")
        
        await update_job_status(
            job_id, "calculating_bom", 80, "Calculating Bill of Materials..."
        )
        
        # 6. Generate BOM
        bom = await material_engine.generate_bom(
            optimized_spec.to_dict(),
            result["analysis"]
        )
        
        jobs_db[job_id].bom = bom
        
        await update_job_status(
            job_id, "completed", 100, "Design complete!"
        )
        
        jobs_db[job_id].stl_url = f"/api/download/{job_id}/{job_id}.stl"
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        
        jobs_db[job_id].status = "failed"
        jobs_db[job_id].error = str(e)
        
        # Notify via WebSocket
        if request.user_id:
            await manager.send_message({
                "type": "job_failed",
                "job_id": job_id,
                "error": str(e)
            }, request.user_id)

async def update_job_status(job_id: str, status: str, progress: int, step: str):
    """Update job status and notify via WebSocket"""
    
    jobs_db[job_id].status = status
    jobs_db[job_id].progress = progress
    jobs_db[job_id].current_step = step
    
    # Find user_id for this job (in production, store this mapping)
    # For now, just log
    logger.info(f"Job {job_id}: {progress}% - {step}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)