import httpx
import os
from uv_level_monitor.core.models import OpenMeteoAPIRequestParams, OpenMeteoAPIResponseParams, WeatherGroup
from uv_level_monitor.config.config import settings
from pydantic import ValidationError

class OpenMeteoClient:
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self._open_meteo_url = settings.open_meteo_url

    async def fetch_uv_weather(self, query: OpenMeteoAPIRequestParams) -> OpenMeteoAPIResponseParams:
        params = query.model_dump(include={"latitude", "longitude", "timezone", "forecast_hours", "hourly"})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self._open_meteo_url, params=params)
                resp.raise_for_status()
                data = resp.json()

            response = OpenMeteoAPIResponseParams(**data)

            target_set  = {str(k) for k in query.hourly_params}
            compare_set = set(response.hourly.keys())

            # Find the missing keys
            missing_keys = target_set - compare_set

            # Checking the missing keys
            if missing_keys:
                missing_str = ", ".join(missing_keys)
                raise ValueError(f"[Upstream API Error] Missing requested fields: {', '.join(missing_str)}")

        except httpx.HTTPError as exc:
            # Connection error
            raise HTTPException(
                status_code = 502,
                detail = f"[Upstream API Error] Failed to connect to weather service: {str(exc)}"
            )
        except (ValueError, ValidationError) as exc:
            # Request and Response error
            raise HTTPException(
                status_code = 502,
                detail = str(exc)
            )
        return response