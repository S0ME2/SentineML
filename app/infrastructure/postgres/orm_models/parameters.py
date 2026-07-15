from sqlalchemy import ForeignKey, Identity, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.postgres.base import Base


class ParameterORM(Base):
    __tablename__ = "parameters"
    __table_args__ = (
        UniqueConstraint("run_id", "name", name="uq_parameters_run_name"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("runs.id", name="fk_parameters_run", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    value_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
