from typing import Literal
from pydantic import BaseModel, Field
from enum import IntEnum

class SafeTimeCalculatorRequestParams(BaseModel):
    spf: Literal[30,50] = Field(..., description="The SPF of sunscreen")
    uv_index: float = Field(..., ge=1)
    sun_screen_efficiency: float = Field(..., ge=0., le=1.)

class SunscreenUsageCalculatorRequestParams(BaseModel):
    cloth_sugg: str
    weight: int = Field(..., description="weight unit is kg")
    height: int = Field(..., description="height unit is cm")

class AreaPerBodyPart(IntEnum):
    """
    Percentage of are of each part of the body
    """
    face_neck = 9
    arms = 18
    legs = 36