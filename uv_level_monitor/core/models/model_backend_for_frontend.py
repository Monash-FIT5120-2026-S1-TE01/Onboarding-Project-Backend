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
        default = 0.8,
        ge = 0.1,
        le = 1.0,
        description = "The efficiency of the sunscreen"
    )
    skin_type: Literal[1,2,3,4,5,6] = Field(
        default = 3,
        description = "The type for your skin"
    )

class BackendForFrontendResponseParams(BaseModel):
    city: str
    timezone: str
    current_uv_index_time: Dict[str, Union[float, str]]
    past_uv_index_time: Dict[str, Union[List[float], List[str]]]
    forecast_uv_index_time: Dict[str, Union[List[float], List[str]]]
    weather_label: str
    temperature: float
    spf: Literal[30, 50]
    sugg_cloth: str
    warnings: Dict[str, str] = Field(default_factory=dict) # Warning pools for function downgrade