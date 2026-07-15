from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.postgres.base import Base


class MetricDirectionORM(Base):
    __tablename__ = "metric_directions"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    maximize: Mapped[bool] = mapped_column(Boolean, nullable=False)
