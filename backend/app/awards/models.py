"""Frozen DogFood persistence mappings; database triggers are installed by Alembic.

No authorization or business workflows are implemented here.
"""

from __future__ import annotations
from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from app.core.model_base import Base


class Award(Base):
    __tablename__ = "awards"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_awards"),
        sa.CheckConstraint("rank IS NULL OR rank >= 1", name="ck_awards_rank"),
        sa.CheckConstraint(
            "(selected_project_id IS NULL AND selected_by_user_id IS NULL AND selected_at IS NULL AND selection_reason IS NULL) OR (selected_project_id IS NOT NULL AND selected_by_user_id IS NOT NULL AND selected_at IS NOT NULL)",
            name="ck_awards_selection",
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_awards_event_id"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_awards_name"),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_awards_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selected_by_user_id"],
            ["dogfood.users.id"],
            name="fk_awards_selected_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "track_id"],
            ["dogfood.hackathon_tracks.hackathon_id", "dogfood.hackathon_tracks.id"],
            name="fk_awards_track",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "selected_project_id"],
            ["dogfood.projects.hackathon_id", "dogfood.projects.id"],
            name="fk_awards_winner",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        {"schema": "dogfood"},
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )
    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    track_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    prize: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    rank: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    selected_project_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    selected_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    selected_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    selection_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
