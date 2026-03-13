"""
The core function implementation of true logic
"""

from typing import Callable, Optional, Any, Dict
from pydantic import BaseModel, ValidationError
from uv_level_monitor.core.models import ClothRecommendQuery, UVLevelQuery
from pathlib import Path

class BaseQueryProcessor:
    """
    The basic query processor with database connection
    """
    def __init__(self, query_sql_name: str) -> None:
        # Get the path of .sql file
        project_root = Path(__file__).parent.parent
        sql_path     = project_root / "sql_queries" / query_sql_name

        # Read SQL query from .sql file
        self._sql_query = sql_path.read_text(encoding="utf-8").strip()

    async def execute_query_one(self, query: BaseModel, db_conn) -> Optional[Dict[str, Any]]:
        """
        Execute the query using the database connection and return the only result or None
        """
        # Get the parameters for each condition
        params_value = tuple(query.model_dump().values())

        # Execute the sql query
        row = await db_conn.fetchrow(self._sql_query, *params_value)

        return dict(row) if row else None

class ClothRecommender(BaseQueryProcessor):
    def __init__(self) -> None:
        # Bind the cloth recommender sql query
        super().__init__(query_sql_name="recommend_cloth.sql")

    async def recommend(self, query: ClothRecommendQuery, db_conn) -> str:
        """
        Recommend cloth base on the input condition and return the only one suggestion
        """
        # Recommend the cloth
        raw_results = await super().execute_query_one(query=query, db_conn=db_conn)

        return raw_results["sugg_text"]

class UVLevelGetter:
    """
    Class to get the UV level
    """
    pass

class UVAlert:
    """
    Class to alert the UV Level
    """
    pass

class UsageCalculator:
    def __init__(self):
        pass

    @staticmethod
    async def cal(uv_level: float) -> float:
        usage = uv_level**2

        return usage

if __name__ == "__main__":
    pass