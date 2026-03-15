-- Get suggestion for cloth_sugg
/*
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}

def get_uv_level_4cloth(uv: float) -> str:
    if uv < 1:   return "none"
    if uv < 3:   return "low"
    if uv < 6:   return "moderate"
    if uv < 8:   return "high"
    if uv <= 10: return "very_high"
    return "extreme"

def get_temp_level_4cloth(temp: float) -> str:
    if temp < 10:  return "cold"
    if temp < 20:  return "mild"
    return "warm"
*/

SELECT sugg_text 
FROM cloth_sugg
WHERE uv_level = $1
  AND temp_level = $2
  AND is_raining = $3
LIMIT 1;