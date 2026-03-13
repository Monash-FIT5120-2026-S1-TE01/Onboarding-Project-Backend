"""
For pydantic models and placeholder
"""
import os
from pydantic import BaseModel
from typing import List, Protocol

class ClothRecommendQuery(BaseModel):
    uv_level: float
    weather: str

class UVLevelQuery(BaseModel):
    city: str
    timestamp: int

class UVUsageParams(BaseModel):
    uv_level: float