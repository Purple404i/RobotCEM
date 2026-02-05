from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from pathlib import Path
import uuid
import os

from ..cem_engine.orchestrator import EngineOrchestrator
from ..intelligence.market_search import search_part
from ..config import CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Robot CEM Studio API", version="1.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator
orchestrator = EngineOrchestrator(
    csharp_project_path=CONFIG["csharp_project_path"],
    output_dir=CONFIG["output_dir"]
)
logger.info("✓ Engine Orchestrator initialized")

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = {}

class DesignStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: str
    specification: Optional[Dict] = None
    validation: Optional[Dict] = None
    stl_url: Optional[str] = None
    bom: Optional[Dict] = None
    simulation: Optional[Dict] = None
    scientific_analysis: Optional[Dict] = None
    error: Optional[str] = None

# In-memory job storage
jobs_db: Dict[str, DesignStatus] = {}

@app.get("/")
async def root():
    return {"message": "Robot CEM Studio API v1.1.0", "status": "operational"}

@app.post("/api/generate")
async def generate_design(request: GenerateRequest):
    job_id = str(uuid.uuid4())
    
    jobs_db[job_id] = DesignStatus(
        job_id=job_id,
        status="queued",
        progress=0,
        current_step="Initializing workflow"
    )
    
    asyncio.create_task(process_design_job(job_id, request))
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/status/{job_id}", response_model=DesignStatus)
async def get_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]

@app.get("/api/search")
async def market_search(q: str = Query(..., min_length=2)):
    """Search for components using DuckDuckGo"""
    try:
        results = search_part(q)
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/render/{job_id}")
async def get_render(job_id: str):
    """Serve the Blender simulation render"""
    render_path = Path(CONFIG["output_dir"]) / job_id / f"{job_id}_render.png"
    if not render_path.exists():
        # Check if there is any png in the directory
        job_dir = Path(CONFIG["output_dir"]) / job_id
        if job_dir.exists():
            pngs = list(job_dir.glob("*.png"))
            if pngs:
                render_path = pngs[0]
            else:
                raise HTTPException(status_code=404, detail="Render not found")
        else:
            raise HTTPException(status_code=404, detail="Job directory not found")

    return FileResponse(render_path)

@app.get("/api/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = Path(CONFIG["output_dir"]) / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

async def process_design_job(job_id: str, request: GenerateRequest):
    try:
        jobs_db[job_id].status = "processing"
        jobs_db[job_id].current_step = "Executing Aurora Orchestrator"
        jobs_db[job_id].progress = 10

        # Run the full orchestrator loop
        result = await orchestrator.run_from_prompt(
            request.prompt,
            output_name=job_id
        )
        
        # Update job record with results
        jobs_db[job_id].status = "completed"
        jobs_db[job_id].progress = 100
        jobs_db[job_id].current_step = "Design completed"
        jobs_db[job_id].specification = result.get("spec")
        jobs_db[job_id].validation = result.get("validation")
        jobs_db[job_id].bom = result.get("bom")
        jobs_db[job_id].simulation = result.get("simulation")
        jobs_db[job_id].scientific_analysis = result.get("scientific_analysis")

        if result.get("generation", {}).get("success"):
            jobs_db[job_id].stl_url = f"/api/download/{job_id}/{job_id}.stl"
        else:
            jobs_db[job_id].error = result.get("generation", {}).get("error")
            jobs_db[job_id].status = "failed"

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs_db[job_id].status = "failed"
        jobs_db[job_id].error = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
