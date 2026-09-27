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


class PlatformAnnouncement(Base):
    __tablename__ = "platform_announcements"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_platform_announcements"),
        sa.CheckConstraint(
            "btrim(title) <> ''", name="ck_platform_announcements_title"
        ),
        sa.CheckConstraint("btrim(body) <> ''", name="ck_platform_announcements_body"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["dogfood.users.id"],
            name="fk_platform_announcements_created_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["edited_by_user_id"],
            ["dogfood.users.id"],
            name="fk_platform_announcements_edited_by_user_id",
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
    created_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    edited_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    title: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    is_pinned: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("false")
    )
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
        server_onupdate=sa.FetchedValue(),
    )
