from pathlib import Path
from typing import Optional, Dict, Any, Tuple

class BaseQueryProcessor:
    """
    The basic query processor with database connection
    """
    def __init__(self, query_sql_name: str) -> None:
        # Get the path of .sql file
        project_root = Path(__file__).parent.parent.parent
        sql_path = project_root / "sql_queries" / query_sql_name

        # Read SQL query from .sql file
        self._sql_query = sql_path.read_text(encoding="utf-8").strip()

    async def execute_query_one(self, params: Tuple[Any, ...], db_conn) -> Optional[Dict[str, Any]]:
        """
        Execute the query using the database connection and return the only result or None
        """
        # Execute the sql query (assuming asyncpg or similar)
        row = await db_conn.fetchrow(self._sql_query, *params) # Need using position input

        return dict(row) if row else None

class ClothRecommender(BaseQueryProcessor):
    def __init__(self) -> None:
        # Bind the cloth recommender sql query
        super().__init__(query_sql_name="recommend_cloth.sql")

    async def recommend(self, uv_level: str, temp_level: str, is_raining: bool, db_conn) -> str:
        """
        Recommend cloth base on the input condition and return the only one suggestion
        """
        params_tuple = (uv_level, temp_level, is_raining)

        raw_results = await super().execute_query_one(params=params_tuple, db_conn=db_conn)

        if raw_results is None: return "No suggestion."

        return raw_results.get("sugg_text", "No suggestion.")