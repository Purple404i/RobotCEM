from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class GenerateRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = {}

class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str
