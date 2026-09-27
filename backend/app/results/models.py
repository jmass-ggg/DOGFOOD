"""Frozen DogFood persistence mappings; database triggers are installed by Alembic.

No authorization or business workflows are implemented here.
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from app.core.model_base import Base


class ResultPublication(Base):
    __tablename__ = "result_publications"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_result_publications"),
        sa.CheckConstraint(
            "publication_number >= 1", name="ck_result_publications_number"
        ),
        sa.CheckConstraint(
            "(publication_number = 1 AND supersedes_publication_id IS NULL AND correction_reason IS NULL) OR (publication_number > 1 AND supersedes_publication_id IS NOT NULL AND supersedes_publication_id <> id AND correction_reason IS NOT NULL AND btrim(correction_reason) <> '')",
            name="ck_result_publications_correction",
        ),
        sa.UniqueConstraint(
            "hackathon_id", "publication_number", name="uq_result_publications_number"
        ),
        sa.UniqueConstraint(
            "supersedes_publication_id", name="uq_result_publications_supersedes"
        ),
        sa.UniqueConstraint(
            "hackathon_id", "id", name="uq_result_publications_event_id"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(calculation_snapshot) = 'object'",
            name="ck_result_publications_calculation_snapshot",
        ),
        sa.CheckConstraint(
            "btrim(scoring_method) <> ''", name="ck_result_publications_scoring_method"
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_result_publications_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["published_by_user_id"],
            ["dogfood.users.id"],
            name="fk_result_publications_published_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "supersedes_publication_id"],
            [
                "dogfood.result_publications.hackathon_id",
                "dogfood.result_publications.id",
            ],
            name="fk_result_publications_supersedes",
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
    publication_number: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    supersedes_publication_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    published_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    scoring_method: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    calculation_snapshot: Mapped[dict[str, Any]] = mapped_column(
        postgresql.JSONB(), nullable=False
    )
    correction_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)


class ResultEntry(Base):
    __tablename__ = "result_entries"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "publication_id", "project_id", name="pk_result_entries"
        ),
        sa.CheckConstraint(
            "final_score >= 0 AND final_score <= 100 AND final_score <> 'NaN'::numeric",
            name="ck_result_entries_score",
        ),
        sa.CheckConstraint("review_count >= 1", name="ck_result_entries_review_count"),
        sa.CheckConstraint("rank >= 1", name="ck_result_entries_rank"),
        sa.CheckConstraint(
            "btrim(project_name_snapshot) <> ''",
            name="ck_result_entries_project_name_snapshot",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_result_entries_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "publication_id"],
            [
                "dogfood.result_publications.hackathon_id",
                "dogfood.result_publications.id",
            ],
            name="fk_result_entries_publication",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "project_id"],
            ["dogfood.projects.hackathon_id", "dogfood.projects.id"],
            name="fk_result_entries_project",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        {"schema": "dogfood"},
    )

    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    publication_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    final_score: Mapped[Decimal] = mapped_column(sa.Numeric(9, 6), nullable=False)
    review_count: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    rank: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    project_name_snapshot: Mapped[str] = mapped_column(sa.Text(), nullable=False)


class ResultAward(Base):
    __tablename__ = "result_awards"
    __table_args__ = (
        sa.PrimaryKeyConstraint("publication_id", "award_id", name="pk_result_awards"),
        sa.CheckConstraint(
            "btrim(award_name_snapshot) <> ''",
            name="ck_result_awards_award_name_snapshot",
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["dogfood.hackathons.id"],
            name="fk_result_awards_hackathon_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selected_by_user_id"],
            ["dogfood.users.id"],
            name="fk_result_awards_selected_by_user_id",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "publication_id"],
            [
                "dogfood.result_publications.hackathon_id",
                "dogfood.result_publications.id",
            ],
            name="fk_result_awards_publication",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hackathon_id", "award_id"],
            ["dogfood.awards.hackathon_id", "dogfood.awards.id"],
            name="fk_result_awards_award",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publication_id", "project_id"],
            [
                "dogfood.result_entries.publication_id",
                "dogfood.result_entries.project_id",
            ],
            name="fk_result_awards_entry",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        {"schema": "dogfood"},
    )

    hackathon_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    publication_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    award_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
    award_name_snapshot: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    prize_snapshot: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    selected_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
