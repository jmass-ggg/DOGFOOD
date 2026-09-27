"""Frozen DogFood persistence mappings; database triggers are installed by Alembic.

No authorization or business workflows are implemented here.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from app.core.model_base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        sa.CheckConstraint("btrim(action) <> ''", name="ck_audit_events_action"),
        sa.CheckConstraint(
            "btrim(entity_type) <> ''", name="ck_audit_events_entity_type"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(before_data) = 'object'", name="ck_audit_events_before_data"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(after_data) = 'object'", name="ck_audit_events_after_data"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_audit_events_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["dogfood.users.id"],
            name="fk_audit_events_actor_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_audit_events_event_time", "hackathon_id", "created_at", unique=False
        ),
        sa.Index("ix_audit_events_entity", "entity_type", "entity_id", unique=False),
        {"schema": "dogfood"},
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )
    hackathon_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    action: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    before_data: Mapped[dict[str, Any] | None] = mapped_column(
        postgresql.JSONB(none_as_null=True), nullable=True
    )
    after_data: Mapped[dict[str, Any] | None] = mapped_column(
        postgresql.JSONB(none_as_null=True), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
