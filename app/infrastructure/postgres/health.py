from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class SQLAlchemyDatabaseHealthCheck:
    def __init__(self, engine: Engine):
        self._engine = engine

    def is_healthy(self) -> bool:
        try:
            with self._engine.connect() as connection:
                return connection.scalar(text("SELECT 1")) == 1
        except SQLAlchemyError:
            return False
