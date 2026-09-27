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


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_teams"),
        sa.CheckConstraint(
            "(dissolved_at IS NULL AND leader_user_id IS NOT NULL) OR (dissolved_at IS NOT NULL AND leader_user_id IS NULL)",
            name="ck_teams_leader",
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_teams_event_id"),
        sa.CheckConstraint("version >= 1", name="ck_teams_version"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_teams_name"),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_teams_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["dogfood.users.id"],
            name="fk_teams_created_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["leader_user_id"],
            ["dogfood.users.id"],
            name="fk_teams_leader_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "id", "leader_user_id"],
            [
                "dogfood.team_members.hackathon_id",
                "dogfood.team_members.team_id",
                "dogfood.team_members.user_id",
            ],
            name="fk_teams_leader",
            use_alter=True,
            ondelete="NO ACTION",
            deferrable=True,
            initially="DEFERRED",
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
    created_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    leader_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    roster_locked_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    dissolved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
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


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        sa.PrimaryKeyConstraint("hackathon_id", "user_id", name="pk_team_members"),
        sa.UniqueConstraint(
            "hackathon_id", "team_id", "user_id", name="uq_team_members_team_user"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_team_members_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_team_members_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "user_id"],
            [
                "dogfood.hackathon_registrations.hackathon_id",
                "dogfood.hackathon_registrations.user_id",
            ],
            name="fk_team_members_registration",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "team_id"],
            ["dogfood.teams.hackathon_id", "dogfood.teams.id"],
            name="fk_team_members_team",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index("ix_team_members_team", "team_id", unique=False),
        {"schema": "dogfood"},
    )

    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    team_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class TeamMembershipEvent(Base):
    __tablename__ = "team_membership_events"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_team_membership_events"),
        sa.CheckConstraint(
            "event_type IN ('JOINED', 'LEFT')",
            name="ck_team_membership_events_event_type",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_team_membership_events_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_team_membership_events_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "team_id"],
            ["dogfood.teams.hackathon_id", "dogfood.teams.id"],
            name="fk_team_membership_events_team",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_team_membership_events_conflict",
            "team_id",
            "user_id",
            "event_type",
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
    team_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class TeamInvite(Base):
    __tablename__ = "team_invites"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_team_invites"),
        sa.CheckConstraint(
            "max_uses > 0 AND use_count >= 0 AND use_count <= max_uses",
            name="ck_team_invites_uses",
        ),
        sa.UniqueConstraint("token_hash", name="uq_team_invites_token"),
        sa.UniqueConstraint("id", "team_id", name="uq_team_invites_team"),
        sa.CheckConstraint(
            "invite_kind IN ('TARGETED', 'SHARE_LINK')",
            name="ck_team_invites_invite_kind",
        ),
        sa.CheckConstraint(
            "btrim(token_hash) <> ''", name="ck_team_invites_token_hash"
        ),
        sa.CheckConstraint(
            "(invite_kind = 'TARGETED' AND target_email IS NOT NULL AND btrim(target_email) <> '' AND max_uses = 1) OR (invite_kind = 'SHARE_LINK' AND target_email IS NULL)",
            name="ck_team_invites_kind",
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_team_invites_expiry"),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_team_invites_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_user_id"],
            ["dogfood.users.id"],
            name="fk_team_invites_invited_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "team_id"],
            ["dogfood.teams.hackathon_id", "dogfood.teams.id"],
            name="fk_team_invites_team",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index("ix_team_invites_team", "team_id", unique=False),
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
    team_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    invited_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    invite_kind: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    target_email: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    max_uses: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    use_count: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class TeamInviteRedemption(Base):
    __tablename__ = "team_invite_redemptions"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "invite_id", "user_id", name="pk_team_invite_redemptions"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_team_invite_redemptions_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invite_id", "team_id"],
            ["dogfood.team_invites.id", "dogfood.team_invites.team_id"],
            name="fk_team_invite_redemptions_invite_team",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        {"schema": "dogfood"},
    )

    invite_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    team_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
