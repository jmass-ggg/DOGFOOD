"""Frozen DogFood persistence mappings; database triggers are installed by Alembic.

No authorization or business workflows are implemented here.
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from app.core.model_base import Base


class JudgeInvite(Base):
    __tablename__ = "judge_invites"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_judge_invites"),
        sa.UniqueConstraint("token_hash", name="uq_judge_invites_token"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED')",
            name="ck_judge_invites_status",
        ),
        sa.CheckConstraint(
            "btrim(target_email) <> ''", name="ck_judge_invites_target_email"
        ),
        sa.CheckConstraint(
            "btrim(token_hash) <> ''", name="ck_judge_invites_token_hash"
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_judge_invites_expiry"),
        sa.CheckConstraint(
            "(status = 'ACCEPTED' AND accepted_at IS NOT NULL AND accepted_by_user_id IS NOT NULL AND accepted_at < expires_at AND revoked_at IS NULL) OR (status <> 'ACCEPTED' AND accepted_at IS NULL AND accepted_by_user_id IS NULL)",
            name="ck_judge_invites_accepted",
        ),
        sa.CheckConstraint(
            "(status = 'REVOKED') = (revoked_at IS NOT NULL)",
            name="ck_judge_invites_revoked",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_judge_invites_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_user_id"],
            ["dogfood.users.id"],
            name="fk_judge_invites_invited_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accepted_by_user_id"],
            ["dogfood.users.id"],
            name="fk_judge_invites_accepted_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_judge_invites_pending",
            "hackathon_id",
            "target_email_key",
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
    target_email: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    target_email_key: Mapped[str] = mapped_column(
        sa.Text(),
        sa.Computed("lower(btrim(target_email))", persisted=True),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    invited_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'PENDING'")
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class JudgeProfile(Base):
    __tablename__ = "judge_profiles"
    __table_args__ = (
        sa.PrimaryKeyConstraint("hackathon_id", "user_id", name="pk_judge_profiles"),
        sa.CheckConstraint(
            "btrim(public_name) <> ''", name="ck_judge_profiles_public_name"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_judge_profiles_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_judge_profiles_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "user_id", "judge_role"],
            [
                "dogfood.hackathon_memberships.hackathon_id",
                "dogfood.hackathon_memberships.user_id",
                "dogfood.hackathon_memberships.role",
            ],
            name="fk_judge_profiles_judge",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        {"schema": "dogfood"},
    )

    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    judge_role: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("'JUDGE'::text", persisted=True), nullable=False
    )
    public_name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    public_bio: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    avatar_key: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    publication_consent: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("false")
    )


class JudgeAssignment(Base):
    __tablename__ = "judge_assignments"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_judge_assignments"),
        sa.UniqueConstraint(
            "judge_user_id", "project_id", name="uq_judge_assignments_judge_project"
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_judge_assignments_event_id"),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND revoked_by_user_id IS NULL AND revocation_reason IS NULL) OR (revoked_at IS NOT NULL AND revoked_by_user_id IS NOT NULL AND revocation_reason IS NOT NULL AND btrim(revocation_reason) <> '')",
            name="ck_judge_assignments_revocation",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_judge_assignments_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["judge_user_id"],
            ["dogfood.users.id"],
            name="fk_judge_assignments_judge_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_user_id"],
            ["dogfood.users.id"],
            name="fk_judge_assignments_assigned_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_user_id"],
            ["dogfood.users.id"],
            name="fk_judge_assignments_revoked_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "judge_user_id", "judge_role"],
            [
                "dogfood.hackathon_memberships.hackathon_id",
                "dogfood.hackathon_memberships.user_id",
                "dogfood.hackathon_memberships.role",
            ],
            name="fk_judge_assignments_judge",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "project_id"],
            ["dogfood.projects.hackathon_id", "dogfood.projects.id"],
            name="fk_judge_assignments_project",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_judge_assignments_judge_event",
            "judge_user_id",
            "hackathon_id",
            unique=False,
        ),
        sa.Index("ix_judge_assignments_project", "project_id", unique=False),
        sa.Index(
            "ix_judge_assignments_event_revoked",
            "hackathon_id",
            "revoked_at",
            unique=False,
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
    judge_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    judge_role: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("'JUDGE'::text", persisted=True), nullable=False
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    assigned_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    revoked_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    revocation_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)


class JudgingCriterion(Base):
    __tablename__ = "judging_criteria"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_judging_criteria"),
        sa.CheckConstraint(
            "weight_bps >= 0 AND weight_bps <= 10000", name="ck_judging_criteria_weight"
        ),
        sa.CheckConstraint(
            "max_score > 0 AND max_score <> 'NaN'::numeric",
            name="ck_judging_criteria_max_score",
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_judging_criteria_event_id"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_judging_criteria_name"),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_judging_criteria_hackathon_id",
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
    name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    weight_bps: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(sa.Numeric(12, 4), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )


class JudgeReview(Base):
    __tablename__ = "judge_reviews"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_judge_reviews"),
        sa.UniqueConstraint("assignment_id", name="uq_judge_reviews_assignment"),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_judge_reviews_event_id"),
        sa.CheckConstraint("version >= 1", name="ck_judge_reviews_version"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED')", name="ck_judge_reviews_status"
        ),
        sa.CheckConstraint(
            "(status = 'SUBMITTED') = (submitted_at IS NOT NULL)",
            name="ck_judge_reviews_submitted",
        ),
        sa.CheckConstraint(
            "(invalidated_at IS NULL AND invalidated_by_user_id IS NULL AND invalidation_reason IS NULL) OR (invalidated_at IS NOT NULL AND invalidated_by_user_id IS NOT NULL AND invalidation_reason IS NOT NULL AND btrim(invalidation_reason) <> '')",
            name="ck_judge_reviews_invalidated",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_judge_reviews_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invalidated_by_user_id"],
            ["dogfood.users.id"],
            name="fk_judge_reviews_invalidated_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "assignment_id"],
            ["dogfood.judge_assignments.hackathon_id", "dogfood.judge_assignments.id"],
            name="fk_judge_reviews_assignment",
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
    assignment_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'DRAFT'")
    )
    comment: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    invalidated_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    invalidation_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    version: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("1")
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


class JudgeScore(Base):
    __tablename__ = "judge_scores"
    __table_args__ = (
        sa.PrimaryKeyConstraint("review_id", "criterion_id", name="pk_judge_scores"),
        sa.CheckConstraint(
            "score >= 0 AND score <> 'NaN'::numeric", name="ck_judge_scores_score"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_judge_scores_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "review_id"],
            ["dogfood.judge_reviews.hackathon_id", "dogfood.judge_reviews.id"],
            name="fk_judge_scores_review",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "criterion_id"],
            ["dogfood.judging_criteria.hackathon_id", "dogfood.judging_criteria.id"],
            name="fk_judge_scores_criterion",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index("ix_judge_scores_criterion", "criterion_id", unique=False),
        {"schema": "dogfood"},
    )

    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    review_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    criterion_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    score: Mapped[Decimal] = mapped_column(sa.Numeric(12, 4), nullable=False)
    comment: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
