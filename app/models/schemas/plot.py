from pydantic import BaseModel, Field
from typing import Optional

class PlotCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    area_m2: Optional[float] = None
    crop_type: str = "tomate"

class PlotResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    area_m2: Optional[float]
    crop_type: str
    is_active: bool
    created_at: str
