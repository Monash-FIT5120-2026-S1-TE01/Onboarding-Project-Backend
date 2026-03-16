from pydantic import BaseModel, Field
from typing import Literal, Union, Dict, List

class BackendForFrontendRequestParams(BaseModel):
    city_name: str = Field(
        default = "Melbourne",
        description = "The name of the Australian city you want to check"
    )
    timezone: str = Field(
        default = "Australia/Sydney",
        description = "The time zone in INNA format."
    )
    sun_screen_efficiency: float = Field(
        default = 0.3,
        ge = 0.1,
        le = 1.0,
        description = "The efficiency of the sunscreen"
    )
    skin_type: Literal[1,2,3,4,5,6] = Field(
        default = 3,
        description = "The type for your skin"
    )
    height: int = Field(
        default = 175,
        description = "Height in unit of cm"
    )
    weight: int = Field(
        default = 82,
        description = "Weight in unit of kg"
    )

class BackendForFrontendResponseParams(BaseModel):
    city: str
    timezone: str
    current_uv_index_time: Dict[str, Union[float, str]]
    past_uv_index_time: Dict[str, Union[List[float], List[str]]]
    forecast_uv_index_time: Dict[str, Union[List[float], List[str]]]
    weather_label: str
    temperature: float
    spf: Literal[0, 30, 50]
    sugg_cloth: str
    safe_time: int
    usage: Dict[str, float]
    warnings: Dict[str, str] = Field(default_factory=dict) # Warning pools for function downgrade