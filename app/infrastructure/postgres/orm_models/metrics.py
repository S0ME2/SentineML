from sqlalchemy import (
    Double,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.postgres.base import Base


class MetricORM(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        UniqueConstraint("run_id", "name", name="uq_metrics_run_name"),
        Index("ix_metrics_name_value_run", "name", "value", "run_id"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("runs.id", name="fk_metrics_run"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("metric_directions.name", name="fk_metrics_direction"),
        nullable=False,
    )
    value: Mapped[float] = mapped_column(Double, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
