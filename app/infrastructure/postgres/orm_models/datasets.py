from sqlalchemy import Identity, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.postgres.base import Base


class DatasetORM(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_datasets_name_version"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_value: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
