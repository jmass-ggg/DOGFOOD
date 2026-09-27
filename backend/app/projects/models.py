"""Frozen DogFood persistence mappings; database triggers are installed by Alembic.

No authorization or business workflows are implemented here.
"""

from __future__ import annotations
from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.model_base import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.UniqueConstraint("team_id", name="uq_projects_team"),
        sa.UniqueConstraint("id", "team_id", name="uq_projects_id_team"),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_projects_event_id"),
        sa.CheckConstraint("version >= 1", name="ck_projects_version"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_projects_name"),
        sa.CheckConstraint("btrim(tagline) <> ''", name="ck_projects_tagline"),
        sa.CheckConstraint(
            "(deleted_at IS NULL) = (deleted_by_user_id IS NULL)",
            name="ck_projects_deleted",
        ),
        sa.CheckConstraint(
            "(disqualified_at IS NULL AND disqualified_by_user_id IS NULL AND disqualification_reason IS NULL) OR (disqualified_at IS NOT NULL AND disqualified_by_user_id IS NOT NULL AND disqualification_reason IS NOT NULL AND btrim(disqualification_reason) <> '')",
            name="ck_projects_disqualified",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_projects_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            ["dogfood.users.id"],
            name="fk_projects_submitted_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by_user_id"],
            ["dogfood.users.id"],
            name="fk_projects_deleted_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["disqualified_by_user_id"],
            ["dogfood.users.id"],
            name="fk_projects_disqualified_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "team_id"],
            ["dogfood.teams.hackathon_id", "dogfood.teams.id"],
            name="fk_projects_team",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "track_id"],
            ["dogfood.hackathon_tracks.hackathon_id", "dogfood.hackathon_tracks.id"],
            name="fk_projects_track",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index("ix_projects_track", "track_id", unique=False),
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
    track_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    submitted_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    tagline: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    inspiration: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    what_it_does: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    how_it_was_built: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    challenges: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    accomplishments: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    what_we_learned: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    whats_next: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    deleted_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    disqualified_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    disqualified_by_user_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    disqualification_reason: Mapped[str | None] = mapped_column(
        sa.Text(), nullable=True
    )
    version: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("1")
    )

    # Explicit read-only navigation avoids implicit reparenting/cascading writes.
    links: Mapped[list[ProjectLink]] = relationship(
        "ProjectLink", viewonly=True, lazy="raise"
    )
    media: Mapped[list[ProjectMedia]] = relationship(
        "ProjectMedia", viewonly=True, lazy="raise"
    )
    technologies: Mapped[list[ProjectTechnology]] = relationship(
        "ProjectTechnology", viewonly=True, lazy="raise"
    )


class ProjectSubmissionMember(Base):
    __tablename__ = "project_submission_members"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "project_id", "user_id", name="pk_project_submission_members"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_project_submission_members_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "team_id"],
            ["dogfood.projects.id", "dogfood.projects.team_id"],
            name="fk_project_submission_members_project_team",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_project_submission_members_leader",
            "project_id",
            unique=True,
            postgresql_where=sa.text("was_leader"),
        ),
        {"schema": "dogfood"},
    )

    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    team_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    was_leader: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )


class ProjectLink(Base):
    __tablename__ = "project_links"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_project_links"),
        sa.CheckConstraint(
            "link_type IN ('GITHUB', 'LIVE_DEMO', 'YOUTUBE', 'GOOGLE_DRIVE', 'ONEDRIVE', 'OTHER')",
            name="ck_project_links_link_type",
        ),
        sa.CheckConstraint(
            "url ~ '^https://[^[:space:]]+$'", name="ck_project_links_https"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["dogfood.projects.id"],
            name="fk_project_links_project_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_project_links_project_order", "project_id", "sort_order", unique=False
        ),
        {"schema": "dogfood"},
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    link_type: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    url: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    label: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )


class ProjectMedia(Base):
    __tablename__ = "project_media"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_project_media"),
        sa.CheckConstraint("size_bytes > 0", name="ck_project_media_size"),
        sa.CheckConstraint("mime_type LIKE 'image/%'", name="ck_project_media_image"),
        sa.CheckConstraint(
            "btrim(storage_key) <> ''", name="ck_project_media_storage_key"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["dogfood.projects.id"],
            name="fk_project_media_project_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.Index(
            "ix_project_media_project_order", "project_id", "sort_order", unique=False
        ),
        {"schema": "dogfood"},
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    mime_type: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False)
    caption: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer(), nullable=False, server_default=sa.text("0")
    )


class ProjectTechnology(Base):
    __tablename__ = "project_technologies"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "project_id", "normalized_key", name="pk_project_technologies"
        ),
        sa.CheckConstraint(
            "btrim(display_name) <> ''", name="ck_project_technologies_display_name"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["dogfood.projects.id"],
            name="fk_project_technologies_project_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        {"schema": "dogfood"},
    )

    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    normalized_key: Mapped[str] = mapped_column(
        sa.Text(),
        sa.Computed("lower(btrim(display_name))", persisted=True),
        primary_key=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
