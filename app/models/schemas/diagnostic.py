from pydantic import BaseModel, Field
from typing import Optional, List

class BoundingBox(BaseModel):
    x_min: float = Field(ge=0, le=1)
    y_min: float = Field(ge=0, le=1)
    x_max: float = Field(ge=0, le=1)
    y_max: float = Field(ge=0, le=1)
    coordinate_space: str = "normalized_0_to_1"
    reference: str = "original_image_dimensions"

class DetectionResult(BaseModel):
    detection_id: str
    disease_label: str
    disease_name_scientific: Optional[str] = None
    disease_name_spanish: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)
    severity_level: str  # MILD | MODERATE | SEVERE
    bounding_box: BoundingBox

class DiagnosticResponse(BaseModel):
    diagnostic_id: str
    status: str
    created_at: str
    processing_time_ms: Optional[int] = None
    image_url: Optional[str] = None
    detections: List[DetectionResult] = []
    summary: dict = {}
    model_info: dict = {}
