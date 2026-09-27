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


class Hackathon(Base):
    __tablename__ = "hackathons"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_hackathons"),
        sa.CheckConstraint("team_min_size >= 1", name="ck_hackathons_team_min"),
        sa.CheckConstraint(
            "team_max_size IS NULL OR team_max_size >= team_min_size",
            name="ck_hackathons_team_max",
        ),
        sa.CheckConstraint(
            "minimum_reviews_per_project >= 1", name="ck_hackathons_coverage"
        ),
        sa.UniqueConstraint("slug", name="uq_hackathons_slug"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_hackathons_name"),
        sa.CheckConstraint("btrim(slug) <> ''", name="ck_hackathons_slug"),
        sa.CheckConstraint(
            "btrim(display_timezone) <> ''", name="ck_hackathons_display_timezone"
        ),
        sa.CheckConstraint(
            "lifecycle_status IN ('DRAFT', 'PUBLISHED', 'CANCELLED', 'ARCHIVED')",
            name="ck_hackathons_lifecycle_status",
        ),
        sa.CheckConstraint(
            "result_gallery_mode IN ('WINNERS_ONLY', 'ALL_PROJECTS')",
            name="ck_hackathons_result_gallery_mode",
        ),
        sa.CheckConstraint(
            "registration_start_at IS NULL OR registration_end_at IS NULL OR registration_start_at <= registration_end_at",
            name="ck_hackathons_registration_window",
        ),
        sa.CheckConstraint(
            "registration_end_at IS NULL OR submission_deadline_at IS NULL OR registration_end_at <= submission_deadline_at",
            name="ck_hackathons_registration_before_submission",
        ),
        sa.CheckConstraint(
            "hackathon_start_at IS NULL OR submission_deadline_at IS NULL OR hackathon_start_at <= submission_deadline_at",
            name="ck_hackathons_event_before_submission",
        ),
        sa.CheckConstraint(
            "submission_deadline_at IS NULL OR judging_start_at IS NULL OR submission_deadline_at <= judging_start_at",
            name="ck_hackathons_submission_before_judging",
        ),
        sa.CheckConstraint(
            "judging_start_at IS NULL OR judging_end_at IS NULL OR judging_start_at <= judging_end_at",
            name="ck_hackathons_judging_window",
        ),
        sa.CheckConstraint(
            "submission_deadline_at IS NULL OR hackathon_end_at IS NULL OR submission_deadline_at <= hackathon_end_at",
            name="ck_hackathons_submission_within_event",
        ),
        sa.CheckConstraint(
            "lifecycle_status <> 'PUBLISHED' OR (registration_start_at IS NOT NULL AND registration_end_at IS NOT NULL AND hackathon_start_at IS NOT NULL AND submission_deadline_at IS NOT NULL AND judging_start_at IS NOT NULL AND judging_end_at IS NOT NULL AND hackathon_end_at IS NOT NULL AND current_rules_version_id IS NOT NULL)",
            name="ck_hackathons_published",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathons_created_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organizer_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathons_organizer_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id", "organizer_user_id", "organizer_role", "organizer_status"],
            [
                "dogfood.hackathon_memberships.hackathon_id",
                "dogfood.hackathon_memberships.user_id",
                "dogfood.hackathon_memberships.role",
                "dogfood.hackathon_memberships.status",
            ],
            name="fk_hackathons_organizer",
            use_alter=True,
            ondelete="NO ACTION",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["id", "current_rules_version_id"],
            [
                "dogfood.hackathon_rules_versions.hackathon_id",
                "dogfood.hackathon_rules_versions.id",
            ],
            name="fk_hackathons_rules",
            use_alter=True,
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id", "current_result_publication_id"],
            [
                "dogfood.result_publications.hackathon_id",
                "dogfood.result_publications.id",
            ],
            name="fk_hackathons_publication",
            use_alter=True,
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index("ix_hackathons_lifecycle", "lifecycle_status", unique=False),
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
    organizer_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    organizer_role: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("'ORGANIZER'::text", persisted=True), nullable=False
    )
    organizer_status: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("'ACTIVE'::text", persisted=True), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    tagline: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    logo_key: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    cover_key: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    format: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    venue: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    display_timezone: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'UTC'")
    )
    lifecycle_status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'DRAFT'")
    )
    registration_start_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    registration_end_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    hackathon_start_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    submission_deadline_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    judging_start_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    judging_end_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    hackathon_end_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    team_min_size: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("1")
    )
    team_max_size: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    result_gallery_mode: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'WINNERS_ONLY'")
    )
    minimum_reviews_per_project: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("1")
    )
    current_rules_version_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    current_result_publication_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    rubric_locked_at: Mapped[datetime | None] = mapped_column(
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


class HackathonMembership(Base):
    __tablename__ = "hackathon_memberships"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "hackathon_id", "user_id", name="pk_hackathon_memberships"
        ),
        sa.UniqueConstraint(
            "hackathon_id", "user_id", "role", name="uq_hackathon_memberships_role"
        ),
        sa.UniqueConstraint(
            "hackathon_id",
            "user_id",
            "role",
            "status",
            name="uq_hackathon_memberships_role_status",
        ),
        sa.CheckConstraint(
            "role IN ('PARTICIPANT', 'JUDGE', 'HACKATHON_ADMIN', 'ORGANIZER')",
            name="ck_hackathon_memberships_role",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'BANNED', 'REVOKED')",
            name="ck_hackathon_memberships_status",
        ),
        sa.CheckConstraint(
            "status = 'ACTIVE' OR (status_changed_by_user_id IS NOT NULL AND status_reason IS NOT NULL AND btrim(status_reason) <> '')",
            name="ck_hackathon_memberships_status_reason",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_memberships_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_memberships_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["status_changed_by_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_memberships_status_changed_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_hackathon_memberships_organizer",
            "hackathon_id",
            unique=True,
            postgresql_where=sa.text("role = 'ORGANIZER'"),
        ),
        sa.Index(
            "ix_hackathon_memberships_event_role", "hackathon_id", "role", unique=False
        ),
        sa.Index("ix_hackathon_memberships_user", "user_id", unique=False),
        {"schema": "dogfood"},
    )

    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    role: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text(), nullable=False, server_default=sa.text("'ACTIVE'")
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    status_changed_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    status_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class HackathonRulesVersion(Base):
    __tablename__ = "hackathon_rules_versions"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_rules_versions"),
        sa.CheckConstraint(
            "version_number >= 1", name="ck_hackathon_rules_versions_number"
        ),
        sa.UniqueConstraint(
            "hackathon_id", "version_number", name="uq_hackathon_rules_versions_number"
        ),
        sa.UniqueConstraint(
            "hackathon_id", "id", name="uq_hackathon_rules_versions_event_id"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(eligibility_flags) = 'object'",
            name="ck_hackathon_rules_versions_eligibility_flags",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(country_lists) = 'object'",
            name="ck_hackathon_rules_versions_country_lists",
        ),
        sa.CheckConstraint(
            "btrim(rules) <> ''", name="ck_hackathon_rules_versions_rules"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_rules_versions_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_rules_versions_created_by_user_id",
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
    version_number: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    rules: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    eligibility_description: Mapped[str | None] = mapped_column(
        sa.Text(), nullable=True
    )
    eligibility_flags: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    country_lists: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class HackathonTrack(Base):
    __tablename__ = "hackathon_tracks"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_tracks"),
        sa.UniqueConstraint(
            "hackathon_id", "name_key", name="uq_hackathon_tracks_name"
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_hackathon_tracks_event_id"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_hackathon_tracks_name"),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_tracks_hackathon_id",
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
    name_key: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("lower(btrim(name))", persisted=True), nullable=False
    )
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )


class HackathonSponsor(Base):
    __tablename__ = "hackathon_sponsors"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_sponsors"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_hackathon_sponsors_name"),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_sponsors_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_hackathon_sponsors_event_order",
            "hackathon_id",
            "sort_order",
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
    name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    logo_key: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    url: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    tier: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )


class HackathonScheduleItem(Base):
    __tablename__ = "hackathon_schedule_items"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_schedule_items"),
        sa.CheckConstraint(
            "end_at IS NULL OR end_at >= start_at",
            name="ck_hackathon_schedule_items_dates",
        ),
        sa.CheckConstraint(
            "btrim(title) <> ''", name="ck_hackathon_schedule_items_title"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_schedule_items_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_hackathon_schedule_items_event_order",
            "hackathon_id",
            "sort_order",
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
    title: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    start_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    end_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    location: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    link: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )
