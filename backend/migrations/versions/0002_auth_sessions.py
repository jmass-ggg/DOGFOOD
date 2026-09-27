"""Owner-approved authentication sessions, after the frozen 33-table T2 baseline."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_auth_sessions"
down_revision = "0001_dogfood_v1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("auth_version", sa.Integer(), nullable=False),
        sa.Column(
            "generation", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_sessions"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dogfood.users.id"],
            name="fk_auth_sessions_user",
            ondelete="RESTRICT",
            deferrable=False,
        ),
        sa.CheckConstraint("auth_version >= 1", name="ck_auth_sessions_auth_version"),
        sa.CheckConstraint("generation >= 0", name="ck_auth_sessions_generation"),
        sa.CheckConstraint("expires_at > created_at", name="ck_auth_sessions_expiry"),
        schema="dogfood",
    )
    op.create_index(
        "ix_auth_sessions_user", "auth_sessions", ["user_id"], schema="dogfood"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.auth_sessions FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at()"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.auth_sessions FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','user_id','auth_version','expires_at','created_at')"
    )


def downgrade():
    op.drop_table("auth_sessions", schema="dogfood")
