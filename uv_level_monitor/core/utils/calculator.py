import re
import asyncio
from typing import Literal, Dict
from uv_level_monitor.core.models import AreaPerBodyPart

class SafeTimeCalculator:
    SKIN_MED_MAPPING = {
        1: 220,
        2: 320,
        3: 400,
        4: 500,
        5: 750,
        6: 1200
    }

    async def cal(
            self,
            spf: Literal[0, 30,50],
            uv_index: float,
            sun_screen_efficiency: float,
            skin_type: Literal[1,2,3,4,5,6],
            epsilon: float = 1e-06
    ) -> float:
        med = self.SKIN_MED_MAPPING.get(skin_type, 3)
        if spf == 0: safe_time = round(2 * med * sun_screen_efficiency / (3 * (uv_index + epsilon)))
        else: safe_time = round(2 * med * spf * sun_screen_efficiency / (3 * (uv_index + epsilon)))
        return safe_time

class SPFCalculator:
    @staticmethod
    async def cal(uv_index: float) -> Literal[0, 30, 50]:
        if uv_index < 2: return 0
        if uv_index < 3: return 30
        return 50

class SunscreenUsageCalculator:
    __pattern_1 = re.compile(pattern=r"[,.]")
    __pattern_2 = re.compile(pattern=r"[ ]{2,}")
    __pattern_arm = re.compile(pattern=r" long sleeves ")
    __pattern_leg = re.compile(pattern=r" long pants ")

    @staticmethod
    def mosteller_equation(
            weight: int,
            height: int
    ) -> int:
        """
        Calculate the area of body, m -> cm
        """
        # round((weight * height / 3600) ** 0.5 * 10000)
        return round((weight * height) ** 0.5 * 500 / 3) # Simplified equation

    @staticmethod
    def usage_equation(
            cover_area: float # In cm2
    ) -> float:
        """
        Calculate the usage
        """
        cover_area_mg = cover_area * 2
        cover_area_ml = cover_area_mg / 1000

        return cover_area_ml

    def get_cloth_type(
            self,
            cloth_sugg: str
    ) -> Dict[str, bool]:
        """
        Get the cloth type from cloth suggestion
        """
        # Cleaning
        clean_cloth_sugg_1 = re.sub(pattern=self.__pattern_1, repl=" ", string=cloth_sugg) # Clean comma
        clean_cloth_sugg_2 = re.sub(pattern=self.__pattern_2, repl=" ", string=clean_cloth_sugg_1) # Merge space
        clean_cloth_sugg_3 = f" {clean_cloth_sugg_2.strip().lower()} "

        # Finding
        need_arm = not re.search(pattern=self.__pattern_arm, string=clean_cloth_sugg_3)
        need_leg = not re.search(pattern=self.__pattern_leg, string=clean_cloth_sugg_3)

        return {"need_arm": need_arm, "need_leg": need_leg}

    def cal(
            self,
            cloth_sugg: str,
            height: int,
            weight: int
    ) -> Dict[str, float]:
        """
        Calculate the sunscreen usage based on equation
        """
        # Get the cloth type
        condition = self.get_cloth_type(cloth_sugg=cloth_sugg)

        # Calculate area (cm)
        area = self.mosteller_equation(weight=weight, height=height)

        # Calculate total usage
        total_usage = self.usage_equation(cover_area=area)

        # Calculate partial usage
        face_neck = round(float(AreaPerBodyPart.face_neck) * total_usage / 100, 2)
        arm_leg = 0
        if condition.get("need_arm", True):
            arm = float(AreaPerBodyPart.arms) * total_usage / 100
            arm_leg += arm
        if condition.get("need_leg", True):
            leg = float(AreaPerBodyPart.legs) * total_usage / 100
            arm_leg += leg
        arm_leg = round(arm_leg, 2)

        return {"face_neck": face_neck, "arm_leg": arm_leg, "total": face_neck + arm_leg}

if __name__ == "__main__":
    pass