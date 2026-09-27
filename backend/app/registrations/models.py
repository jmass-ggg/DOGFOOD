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


class HackathonRegistration(Base):
    __tablename__ = "hackathon_registrations"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "hackathon_id", "user_id", name="pk_hackathon_registrations"
        ),
        sa.CheckConstraint(
            "participation_preference IN ('SOLO', 'LOOKING_FOR_TEAM', 'HAVE_TEAM')",
            name="ck_hackathon_registrations_participation_preference",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(eligibility_attestations) = 'object'",
            name="ck_hackathon_registrations_eligibility_attestations",
        ),
        sa.CheckConstraint(
            "NOT (eligibility_attestations ? 'age_eligibility_confirmed') OR jsonb_typeof(eligibility_attestations->'age_eligibility_confirmed') = 'boolean'",
            name="ck_hackathon_registrations_age",
        ),
        sa.CheckConstraint(
            "btrim(country_snapshot) <> ''",
            name="ck_hackathon_registrations_country_snapshot",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_hackathon_registrations_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_hackathon_registrations_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "user_id", "participant_role"],
            [
                "dogfood.hackathon_memberships.hackathon_id",
                "dogfood.hackathon_memberships.user_id",
                "dogfood.hackathon_memberships.role",
            ],
            name="fk_hackathon_registrations_participant",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "accepted_rules_version_id"],
            [
                "dogfood.hackathon_rules_versions.hackathon_id",
                "dogfood.hackathon_rules_versions.id",
            ],
            name="fk_hackathon_registrations_rules",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accepted_terms_version_id"],
            ["dogfood.platform_terms_versions.id"],
            name="fk_hackathon_registrations_terms",
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
    participant_role: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("'PARTICIPANT'::text", persisted=True), nullable=False
    )
    participation_preference: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    referral_source: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    country_snapshot: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    eligibility_attestations: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    accepted_rules_version_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    accepted_terms_version_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    rules_accepted_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    terms_accepted_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    registered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class ParticipantProfile(Base):
    __tablename__ = "participant_profiles"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "hackathon_id", "user_id", name="pk_participant_profiles"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(external_profile_urls) = 'object'",
            name="ck_participant_profiles_external_profile_urls",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_participant_profiles_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_participant_profiles_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "user_id"],
            [
                "dogfood.hackathon_registrations.hackathon_id",
                "dogfood.hackathon_registrations.user_id",
            ],
            name="fk_participant_profiles_registration",
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
    bio: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    skills: Mapped[list[str]] = mapped_column(
        postgresql.ARRAY(sa.Text()),
        nullable=False,
        server_default=sa.text("ARRAY[]::text[]"),
    )
    looking_for_roles: Mapped[list[str]] = mapped_column(
        postgresql.ARRAY(sa.Text()),
        nullable=False,
        server_default=sa.text("ARRAY[]::text[]"),
    )
    looking_for_team: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("false")
    )
    discovery_opt_in: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("false")
    )
    external_profile_urls: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
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
