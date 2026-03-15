from typing import Dict, Union, Literal, List
from fastapi import HTTPException, status
from .calculator import SafeTimeCalculator, SPFCalculator, SunscreenUsageCalculator
from .api_client import OpenMeteoClient, GeocodingClient
from .query_processor import ClothRecommender
from uv_level_monitor.core.models import *
from datetime import datetime

import logging
import zoneinfo

logger = logging.getLogger(__name__)

class BackendForFrontend:
    """
    Planning the task and form the result
    """
    def __init__(self):
        self._uv_weather_api = OpenMeteoClient()
        self._coord_api = GeocodingClient()
        self._spf_calculator = SPFCalculator()
        self._safe_time_calculator = SafeTimeCalculator()
        self._usage_calculator = SunscreenUsageCalculator()
        self._cloth_recommender = ClothRecommender()

        self._default_city = "melbourne"
        self._default_timezone = "Australia/Sydney"

        self._default_weight = 82
        self._default_height = 175

    async def __fetch_coord(
            self,
            city_name: str
    ) -> Dict[str, Union[float, str]]:
        """
         Fetch coord of city
        """
        response = {}

        coord_query = CityToCoordRequestParams(city=city_name)

        coord = await self._coord_api.city_to_coords(query=coord_query)

        # Display name be like: ..., ..., Australia or the country name
        if not coord or not coord.display_name.lower().endswith("australia"):
            # Downgrade to using default city name
            msg = f"[BFF Warning] Not a valid Australian city: '{city_name}', using default city: '{self._default_city}'"
            logger.warning(msg)

            coord_query = CityToCoordRequestParams(city=self._default_city)
            coord = await self._coord_api.city_to_coords(query=coord_query)

            city_name = self._default_city
            response.update({"warning": msg})

        response.update({"city": city_name, "longitude": coord.lon, "latitude": coord.lat})

        return response

    async def __fetch_uv_weather(
            self,
            latitude: float,
            longitude: float,
            timezone: str,
    ) -> Dict[str, Union[str, Dict[str, Union[str,float, List[float]]]]]:
        """
        Fetch uv weather value
        """

        response = {}

        # Set the weather variables
        weather_variable = [
            WeatherVariable.TEMPERATURE,
            WeatherVariable.WEATHER_CODE,
            WeatherVariable.UV_INDEX,
        ]

        # Get the current datetime
        try:
            time_zone_class = zoneinfo.ZoneInfo(timezone)
        except zoneinfo.ZoneInfoNotFoundError:
            msg = f"[BFF Warning] Invalid timezone format: '{timezone}', using the default timezone: '{self._default_timezone}'"
            logger.warning(msg)
            response.update({"warning": msg})
            time_zone_class = zoneinfo.ZoneInfo(self._default_timezone)
            timezone = self._default_timezone

        # Calculate the past hour
        now = datetime.now(tz=time_zone_class)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        past_hours = int((now - start_of_day).total_seconds() / 3600)

        # Calculate the forecast hour
        forecast_hours = 24 - past_hours

        # Fetch uv weather
        uv_weather_query = OpenMeteoAPIRequestParams(
            longitude = longitude,
            latitude  = latitude,
            hourly_params = weather_variable,
            timezone  = timezone,
            forecast_hours = forecast_hours,
            past_hours = past_hours
        )
        uv_weather = await self._uv_weather_api.fetch_uv_weather(query=uv_weather_query)

        # Build response
        hourly = uv_weather.hourly
        uv_index = hourly.get("uv_index")
        time = hourly.get("time")
        weather_code = int(hourly.get("weather_code")[past_hours])

        missing_items = []
        if uv_index is None:
            missing_items.append(f"uv_index({uv_index})")
        if time is None:
            missing_items.append(f"time({time})")
        if weather_code is None:
            # weather code could be zero, and not 0 = 1 = True,
            # do not use not weather_code
            missing_items.append(f"weather_code{weather_code}")
        if missing_items:
            missing_str = ", ".join(missing_items)
            logger.error(f"[BFF Error] Incomplete weather data returned from API: missing {missing_str}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Weather service is currently unavailable")

        response.update({
            "current_uv_index_time": {
                "uv_index": uv_index[past_hours],
                "datetime": now.replace(minute=0, second=0, microsecond=0, tzinfo=None).isoformat(timespec='minutes')
            },
            "past_uv_index_time": {
                "uv_index": [uv_index[i] for i in range(past_hours)],
                "datetime": [time[i] for i in range(past_hours)]
            },
            "forecast_uv_index_time": {
                "uv_index": [uv_index[i] for i in range(past_hours + 1, 24)],
                "datetime": [time[i] for i in range(past_hours + 1, 24)]
            },
            "weather_code": weather_code,
            "weather_label": WeatherGroup.from_code(code=weather_code).label,
            "temperature": hourly.get("temperature_2m")[past_hours],
            "timezone": timezone
        })

        return response

    async def __cal_spf(
            self,
            uv_index: float
    ) -> Dict[str, Literal[0, 30, 50]]:
        """
        Judge the level of SPF based on uv index
        """
        spf = await self._spf_calculator.cal(uv_index=uv_index)
        if spf is None:
            logger.error("[BFF Error] SPF calculation returned empty")
            raise HTTPException(status_code=500, detail="Failed to calculate the SPF")
        return {"spf": spf}

    async def __cal_safe_time(
            self,
            spf: Literal[30, 50],
            uv_index: float,
            sun_screen_efficiency: float,
            skin_type: Literal[1,2,3,4,5,6]
    ) -> Dict[str, float]:
        """
        Calculate the safe time
        """
        safe_time = await self._safe_time_calculator.cal(
            spf=spf, uv_index=uv_index, skin_type=skin_type,
            sun_screen_efficiency=sun_screen_efficiency
        )
        if not safe_time:
            logger.error("[BFF Error] Safe time calculation failed")
            raise HTTPException(status_code=500, detail="Safe time calculation failed")
        return {"safe_time": safe_time}

    async def __fetch_sugg_cloth(
            self,
            uv_index: float,
            weather_code: int,
            temperature: float,
            db_conn
    ) -> Dict[str, str]:
        """
        Get the cloth suggestion
        """
        query = ClothRecommendQuery(
            uv_index = uv_index,
            weather_code = weather_code,
            temperature = temperature
        )
        params = query.model_dump(include={"uv_level","temp_level","is_raining"})
        sugg_cloth = await self._cloth_recommender.recommend(db_conn=db_conn, **params)
        if not sugg_cloth:
            logger.error("[BFF Error] Failed to get the cloth suggestion")
            raise HTTPException(status_code=500, detail="Failed to get the cloth suggestion")
        return {"sugg_cloth": sugg_cloth}

    async def __cal_sunscreen_usage(
            self,
            cloth_sugg: str,
            height: int,
            weight: int
    ) -> Dict[str, Union[float, str]]:
        """
        Calculate the sunscreen usage
        """
        response = {}

        query = SunscreenUsageCalculatorRequestParams(
            cloth_sugg = cloth_sugg,
            weight = weight,
            height = height
        )
        if query.weight <= 0:
            msg = f"[BFF Warning] Invalid weight: {query.weight}, using default weight: {self._default_weight}"
            logger.warning(msg)
            response.update({"warning01": msg})
            weight = self._default_weight
        else:
            weight = query.weight

        if query.height <= 0:
            msg = f"[BFF Warning] Invalid height: {query.height}, using default height: {self._default_height}"
            logger.warning(msg)
            response.update({"warning02": msg})
            height = self._default_height
        else:
            height = query.height

        usage = self._usage_calculator.cal(cloth_sugg=query.cloth_sugg, weight=weight, height=height)
        if not usage:
            logger.error("[BFF Error] Failed in calculating the sunscreen usage")
            raise HTTPException(status_code=500, detail="Failed in calculating the sunscreen usage")
        response.update({"usage": usage})

        return response

    async def fetch_curr_status(
            self,
            query: BackendForFrontendRequestParams,
            db_conn
    ) -> BackendForFrontendResponseParams:
        """
        Fetch current status and form the output
        """
        response_dict = {}
        warnings_pool = {} # Partial warnings pool

        # Fetch the coordination
        coordination = await self.__fetch_coord(city_name=query.city_name)
        if coordination.get("warning"): warnings_pool.update({"coordination": coordination.pop("warning")})
        response_dict.update(coordination)

        # Fetch the weather
        uv_weather = await self.__fetch_uv_weather(
            latitude = coordination.get("latitude"),
            longitude = coordination.get("longitude"),
            timezone = query.timezone,
        )
        if uv_weather.get("warning"): warnings_pool.update({"timezone": uv_weather.pop("warning")})
        response_dict.update(uv_weather)

        # Calculate the SPF
        curr_uv_index = uv_weather["current_uv_index_time"]["uv_index"]
        spf = await self.__cal_spf(uv_index=curr_uv_index)
        response_dict.update(spf)

        # Calculate the safe time
        safe_time = await self.__cal_safe_time(
            spf = spf["spf"],
            uv_index = curr_uv_index,
            sun_screen_efficiency = query.sun_screen_efficiency,
            skin_type = query.skin_type
        )
        response_dict.update(safe_time)

        # Get the suggestion
        cloth_sugg = await self.__fetch_sugg_cloth(
            uv_index = curr_uv_index,
            weather_code = int(uv_weather["weather_code"]),
            temperature = float(uv_weather["temperature"]),
            db_conn = db_conn
        )
        response_dict.update(cloth_sugg)

        # Get the sunscreen usage
        usage = await self.__cal_sunscreen_usage(
            cloth_sugg = cloth_sugg.get("sugg_cloth", ""),
            weight = query.weight,
            height = query.height
        )
        if usage.get("warning01"): warnings_pool.update({"weight": usage.pop("warning01")})
        if usage.get("warning02"): warnings_pool.update({"height": usage.pop("warning02")})
        response_dict.update(usage)

        if warnings_pool: response_dict.update({"warnings": warnings_pool})

        return BackendForFrontendResponseParams(**response_dict)