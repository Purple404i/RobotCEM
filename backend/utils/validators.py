from pydantic import BaseModel, validator, Field
from typing import List, Optional, Dict, Any

class DimensionsModel(BaseModel):
    length_mm: Optional[float] = Field(None, ge=1, le=10000)
    width_mm: Optional[float] = Field(None, ge=1, le=10000)
    height_mm: Optional[float] = Field(None, ge=1, le=10000)
    reach_mm: Optional[float] = Field(None, ge=10, le=5000)
    stroke_mm: Optional[float] = Field(None, ge=1, le=1000)

class LoadsModel(BaseModel):
    payload_kg: Optional[float] = Field(None, ge=0, le=1000)
    max_force_n: Optional[float] = Field(None, ge=0, le=100000)
    torque_nm: Optional[float] = Field(None, ge=0, le=10000)

class ComponentModel(BaseModel):
    type: str
    name: str
    mpn: Optional[str] = None
    quantity: int = Field(ge=1, le=100)
    specifications: Dict[str, Any] = {}

class DesignSpecificationModel(BaseModel):
    device_type: str
    dimensions: DimensionsModel
    loads: LoadsModel
    materials: List[str] = Field(min_items=1, max_items=5)
    manufacturing: str
    components: List[ComponentModel] = []
    
    @validator('device_type')
    def validate_device_type(cls, v):
        allowed = ['robot_arm', 'gripper', 'linear_actuator', 'pan_tilt', 'custom']
        if v not in allowed:
            raise ValueError(f'device_type must be one of {allowed}')
        return v
    
    @validator('manufacturing')
    def validate_manufacturing(cls, v):
        allowed = ['FDM', 'SLA', 'SLS', 'CNC', 'hybrid']
        if v not in allowed:
            raise ValueError(f'manufacturing must be one of {allowed}')
        return v
    
    @validator('materials')
    def validate_materials(cls, v):
        allowed = ['PLA', 'ABS', 'PETG', 'Nylon', 'TPU', 'Carbon_Fiber_PLA', 
                   'Aluminum_6061', 'Steel_1045', 'Stainless_316']
        for material in v:
            if material not in allowed:
                raise ValueError(f'Unknown material: {material}')
        return v
