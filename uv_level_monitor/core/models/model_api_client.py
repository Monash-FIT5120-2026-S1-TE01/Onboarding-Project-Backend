from pydantic import (
    BaseModel,
    Field,
    computed_field,
    model_validator
)
from enum import StrEnum, Enum
from typing import (
    List,
    Literal,
    Dict,
    Union,
    Self,
    Optional
)
from functools import lru_cache

# ===================================================================
# GeocodingClient

class CityToCoordRequestParams(BaseModel):
    city: str
    format: str = "jsonv2"
    limit: int = 1

class CityToCoordResponseParams(BaseModel):
    city: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    display_name: str

class CoordToCityRequestParams(BaseModel):
    lat: float = Field(default=-37.8142454, ge=-90, le=90)
    lon: float = Field(default=144.9631732, ge=-180, le=180)
    format: str = "jsonv2"
    zoom: int = 10

class CoordToCityResponseParams(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    city: str
    country: str
    display_name: str

# ===================================================================
# OpenMeteoClient

class WeatherVariable(StrEnum):
    """
    OpenMeteoAPI hourly enum class
    """
    TEMPERATURE  = "temperature_2m"
    WEATHER_CODE = "weather_code"
    HUMIDITY = "relative_humidity_2m"
    UV_INDEX = "uv_index"

class WeatherGroup(Enum):
    """
    WMO Weather Codes mapped to broader business categories.
    """
    CLEAR = ("Clear", {0, 1})
    CLOUDY = ("Cloudy", {2, 3})
    FOG = ("Fog", {45, 48})
    DRIZZLE = ("Drizzle", {51, 53, 55, 56, 57})
    RAIN = ("Rain", {61, 63, 65, 66, 67, 80, 81, 82})
    SNOW = ("Snow", {71, 73, 75, 77, 85, 86})
    THUNDERSTORM = ("Thunderstorm", {95, 96, 99})

    def __init__(self, label: str, codes: set) -> None:
        self.label = label # Clear, Cloudy, ...
        self.codes = codes # 0, 2, ...

    @classmethod
    @lru_cache
    def from_code(cls, code: int) -> Optional[Self]:
        """
        Reverse lookup to find the category from a raw WMO code.
        Returns the Enum member or None if not found.
        """
        for group in cls:
            if code in group.codes:
                return group
        return None

class OpenMeteoAPIRequestParams(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    hourly_params: List[WeatherVariable] = Field(
        default = [v for v in WeatherVariable],
        description = "List of weather variables to retrieve"
    )
    timezone: str = "Australia/Sydney"
    forecast_hours: int = Field(default=12, ge=0)
    past_hours: int = Field(default=12, ge=0)

    @computed_field
    @property
    def hourly(self) -> str:
        """
        Transform list of params name into a string separate by comma
        """
        return ",".join(self.hourly_params)

class OpenMeteoAPIResponseParams(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: str = "Australia/Sydney"
    hourly: Dict[str, List[Union[str, float, int]]]

    @model_validator(mode="after")
    def ensure_hourly_length(self) -> Self:
        """
        Validate the length of the return value in hourly
        """

        # Standard attribute
        times = self.hourly.get("time")
        if times is None:
            raise ValueError("[Upstream API Error] Open-Meteo did not return 'time' field. Check API status.")

        # None empty checking
        target_len = len(times)
        if target_len == 0:
            raise ValueError("[Upstream API Error] Field 'time' has no data (zero length)")

        # Length mismatch checking
        for key,val in self.hourly.items():
            val_len = len(val)
            if val_len != target_len:
                raise ValueError(f"[Upstream API Error] Field '{key}' length {val_len} mismatch 'time' length {target_len}")

        return self