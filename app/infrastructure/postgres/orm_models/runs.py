from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Text,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.runs import RunStatus
from app.infrastructure.postgres.base import Base

RUN_STATUS_TYPE = PostgreSQLEnum(
    RunStatus,
    name="run_status",
    values_callable=lambda enum_class: [status.value for status in enum_class],
    create_type=False,
)


class RunORM(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", name="fk_runs_project"),
        nullable=False,
    )
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", name="fk_runs_dataset"),
        nullable=False,
    )
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("models.id", name="fk_runs_model"),
        nullable=False,
    )
    status: Mapped[RunStatus] = mapped_column(
        RUN_STATUS_TYPE,
        nullable=False,
        server_default=text("'waiting'"),
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_ignored: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false(),
    )
    ignore_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
