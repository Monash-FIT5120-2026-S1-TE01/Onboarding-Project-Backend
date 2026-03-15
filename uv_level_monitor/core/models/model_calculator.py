from typing import Literal
from pydantic import BaseModel, Field

class SafeTimeCalculatorRequestParams(BaseModel):
    spf: Literal[30,50] = Field(..., description="The SPF of sunscreen")
    uv_index: float = Field(..., ge=1)
    sun_screen_efficiency: float = Field(..., ge=0., le=1.)