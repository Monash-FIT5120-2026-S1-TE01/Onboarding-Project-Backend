"""
Gateway to external api
"""
# ===================================================================
# Import library

import httpx

from uv_level_monitor.core.models.model_api_client import (
    CityToCoordRequestParams,
    CityToCoordResponseParams,
    CoordToCityRequestParams,
    CoordToCityResponseParams,
    OpenMeteoAPIRequestParams,
    OpenMeteoAPIResponseParams
)
from uv_level_monitor.config.config import settings
from pydantic import ValidationError
from fastapi import HTTPException

# ===================================================================
# Geocoding

class GeocodingClient:
    """
    Forward and reverse geocoding based on Nominatim endpoints.
    """

    SEARCH_URL = settings.city_to_coord_url
    REVERSE_URL = settings.coord_to_city_url

    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout
        self.headers = {
            "User-Agent": "uv-level-monitor/1.0 (student project)",
            "Accept": "application/json",
        }

    async def city_to_coords(self, query: CityToCoordRequestParams) -> CityToCoordResponseParams:
        """
        Transform city name to coordination
        """

        params = query.model_dump()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                resp = await client.get(self.SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            if not data:
                raise ValueError(f"[Upstream API Error] City not found: {query.city}")

            best = data[0]

            response = CityToCoordResponseParams(city=query.city, **best)

        except httpx.HTTPError as exc:
            # Connection error
            raise HTTPException(
                status_code=502,
                detail=f"[Upstream API Error] Failed to connect to city to coordinate service: {str(exc)}"
            )
        except (ValueError, ValidationError) as exc:
            # Request and Response error
            raise HTTPException(
                status_code = 502,
                detail = str(exc)
            )
        return response

    async def coords_to_city(self, query: CoordToCityRequestParams) -> CoordToCityResponseParams:
        """
        Transform coordination to city name
        """

        params = query.model_dump()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                resp = await client.get(self.REVERSE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            address = data.get("address", {})
            city_name = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
            )

            if not city_name:
                raise ValueError("[Upstream API Error] No city-like location found for the coordinates")

            response = CoordToCityResponseParams(
                lat = query.lat,
                lon = query.lon,
                city = city_name,
                country = address.get("country"),
                display_name = data.get("display_name")
            )

        except httpx.HTTPError as exc:
            # Connection error
            raise HTTPException(
                status_code=502,
                detail=f"[Upstream API Error] Failed to connect to city to coordinate service: {str(exc)}"
            )
        except (ValueError, ValidationError) as exc:
            # Request and Response error
            raise HTTPException(
                status_code = 502,
                detail = str(exc)
            )
        return response

# ===================================================================
# Geocoding

class OpenMeteoClient:
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self._open_meteo_url = settings.open_meteo_url

    async def fetch_uv_weather(self, query: OpenMeteoAPIRequestParams) -> OpenMeteoAPIResponseParams:
        params = query.model_dump(include={"latitude", "longitude", "timezone", "forecast_hours", "past_hours", "hourly"})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self._open_meteo_url, params=params)
                resp.raise_for_status()
                data = resp.json()

            response = OpenMeteoAPIResponseParams(**data)


            # Check the length of the record
            times = response.hourly.get("time")
            if len(times) != query.past_hours + query.forecast_hours:
                raise ValueError(f"[Upstream API Error] Length of response mismatching the total request hours")

            # Find the missing keys
            target_set  = {str(k) for k in query.hourly_params}
            compare_set = set(response.hourly.keys())
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