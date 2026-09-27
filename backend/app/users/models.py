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


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.CheckConstraint("auth_version >= 1", name="ck_users_auth_version"),
        sa.UniqueConstraint("email_key", name="uq_users_email"),
        sa.UniqueConstraint("username_key", name="uq_users_username"),
        sa.CheckConstraint("btrim(email) <> ''", name="ck_users_email"),
        sa.CheckConstraint("btrim(username) <> ''", name="ck_users_username"),
        sa.CheckConstraint("btrim(password_hash) <> ''", name="ck_users_password_hash"),
        sa.CheckConstraint("btrim(full_name) <> ''", name="ck_users_full_name"),
        {"schema": "dogfood"},
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    email_key: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("lower(btrim(email))", persisted=True), nullable=False
    )
    username: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    username_key: Mapped[str] = mapped_column(
        sa.Text(), sa.Computed("lower(btrim(username))", persisted=True), nullable=False
    )
    password_hash: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    full_name: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    country: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    is_super_admin: Mapped[bool] = mapped_column(
        sa.Boolean(), nullable=False, server_default=sa.text("false")
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    disabled_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    auth_version: Mapped[int] = mapped_column(
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


class PlatformTermsVersion(Base):
    __tablename__ = "platform_terms_versions"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_platform_terms_versions"),
        sa.UniqueConstraint("version_label", name="uq_platform_terms_versions_label"),
        sa.CheckConstraint(
            "btrim(version_label) <> ''",
            name="ck_platform_terms_versions_version_label",
        ),
        sa.CheckConstraint("btrim(body) <> ''", name="ck_platform_terms_versions_body"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["dogfood.users.id"],
            name="fk_platform_terms_versions_created_by_user_id",
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
    version_label: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("statement_timestamp()"),
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False
    )
