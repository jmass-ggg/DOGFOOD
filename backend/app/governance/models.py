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


class HackathonChangeRequest(Base):
    __tablename__ = "hackathon_change_requests"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_change_requests"),
        sa.CheckConstraint(
            "request_type IN ('DELETE_HACKATHON', 'TRANSFER_OWNERSHIP')",
            name="ck_hackathon_change_requests_request_type",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_hackathon_change_requests_status",
        ),
        sa.CheckConstraint(
            "btrim(reason) <> ''", name="ck_hackathon_change_requests_reason"
        ),
        sa.CheckConstraint(
            "(request_type = 'DELETE_HACKATHON' AND target_owner_user_id IS NULL) OR (request_type = 'TRANSFER_OWNERSHIP' AND target_owner_user_id IS NOT NULL AND target_owner_user_id <> expected_owner_user_id)",
            name="ck_hackathon_change_requests_target",
        ),
        sa.CheckConstraint(
            "(status = 'PENDING' AND reviewed_by_user_id IS NULL AND reviewed_at IS NULL AND review_reason IS NULL AND executed_at IS NULL) OR (status IN ('APPROVED','REJECTED') AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL AND review_reason IS NOT NULL AND btrim(review_reason) <> '' AND ((status = 'APPROVED' AND executed_at IS NOT NULL) OR (status = 'REJECTED' AND executed_at IS NULL)))",
            name="ck_hackathon_change_requests_review",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_change_requests_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_change_requests_requested_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["expected_owner_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_change_requests_expected_owner_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["target_owner_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_change_requests_target_owner_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_change_requests_reviewed_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_hackathon_change_requests_pending",
            "hackathon_id",
            "request_type",
            unique=True,
            postgresql_where=sa.text("status = 'PENDING'"),
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
    request_type: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    requested_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    expected_owner_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    target_owner_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    reason: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'PENDING'")
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    review_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
