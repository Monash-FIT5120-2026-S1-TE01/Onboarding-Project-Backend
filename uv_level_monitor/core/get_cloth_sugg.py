
# Rain code reference from the dataformat document
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}

# Based on different UV, temperature and weather tpye
CLOTH_SUGG_ID_MAP = {
    ("low",       "cold", True):  1,
    ("low",       "cold", False): 2,
    ("low",       "mild", True):  3,
    ("low",       "mild", False): 4,
    ("low",       "warm", True):  5,
    ("low",       "warm", False): 6,
    ("moderate",  "cold", True):  7,
    ("moderate",  "cold", False): 8,
    ("moderate",  "mild", True):  9,
    ("moderate",  "mild", False): 10,
    ("moderate",  "warm", True):  11,
    ("moderate",  "warm", False): 12,
    ("high",      "cold", True):  13,
    ("high",      "cold", False): 14,
    ("high",      "mild", True):  15,
    ("high",      "mild", False): 16,
    ("high",      "warm", True):  17,
    ("high",      "warm", False): 18,
    ("very_high", "cold", True):  19,
    ("very_high", "cold", False): 20,
    ("very_high", "mild", True):  21,
    ("very_high", "mild", False): 22,
    ("very_high", "warm", True):  23,
    ("very_high", "warm", False): 24,
    ("extreme",   "cold", True):  25,
    ("extreme",   "cold", False): 26,
    ("extreme",   "mild", True):  27,
    ("extreme",   "mild", False): 28,
    ("extreme",   "warm", True):  29,
    ("extreme",   "warm", False): 30,
}
# Select xxx from cloth_sugg
# where uvi = low and tem = cold and umb = true
# 1. recommandation uv level 

class SuggestionRequest(BaseModel):
    uv_index: float
    temperature: float
    weather_code: int

def get_uv_level(uv: float) -> str:
    if uv < 1:   return "none"
    if uv < 3:   return "low"
    if uv < 6:   return "moderate"
    if uv < 8:   return "high"
    if uv <= 10: return "very_high"
    return "extreme"

def get_temp_level(temp: float) -> str:
    if temp < 10:  return "cold"
    if temp < 20:  return "mild"
    return "warm"

@app.post("/suggestion")
def suggestion(req: SuggestionRequest):
    uv_level   = get_uv_level(req.uv_index)
    temp_level = get_temp_level(req.temperature)
    is_raining = req.weather_code in RAIN_CODES

    if uv_level == "none":
        return {
            "sugg_id": None,
            "sugg_text": "UV index is minimal, no special protection needed."
        }

    sugg_id = CLOTH_SUGG_ID_MAP[(uv_level, temp_level, is_raining)]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT sugg_text FROM cloth_sugg WHERE sugg_id = %s", (sugg_id,))
    row = cur.fetchone()
    conn.close()

    return {
        "sugg_id": sugg_id,
        "sugg_text": row[0]
    }