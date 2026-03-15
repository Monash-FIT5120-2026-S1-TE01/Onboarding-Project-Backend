from typing import Literal

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
            spf: Literal[30,50],
            uv_index: float,
            sun_screen_efficiency: float,
            skin_type: Literal[1,2,3,4,5,6],
            epsilon: float = 1e-06
    ) -> float:
        med = self.SKIN_MED_MAPPING.get(skin_type, 3)
        safe_time = int(2 * med * spf * sun_screen_efficiency / (3 * (uv_index + epsilon)))
        return safe_time

class SPFCalculator:
    @staticmethod
    async def cal(uv_index: float) -> Literal[30, 50]:
        return 30 if uv_index < 3 else 50

if __name__ == "__main__":
    pass