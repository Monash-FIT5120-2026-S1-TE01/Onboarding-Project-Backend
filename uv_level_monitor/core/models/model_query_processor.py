from pydantic import BaseModel, computed_field
from .model_api_client import WeatherGroup

class ClothRecommendQuery(BaseModel):
    uv_index: float
    weather_code: int
    temperature: float

    @computed_field
    @property
    def uv_level(self) -> str:
        if self.uv_index < 1:   return "none"
        if self.uv_index < 3:   return "low"
        if self.uv_index < 6:   return "moderate"
        if self.uv_index < 8:   return "high"
        if self.uv_index <= 10: return "very_high"
        return "extreme"

    @computed_field
    @property
    def temp_level(self) -> str:
        """
        Get the temperature level
        """
        if self.temperature < 10:  return "cold"
        if self.temperature < 20:  return "mild"
        return "warm"

    @computed_field
    @property
    def is_raining(self) -> bool:
        """
        Judging whether you need umbrella
        """
        group = WeatherGroup.from_code(code=self.weather_code)
        return group == WeatherGroup.RAIN