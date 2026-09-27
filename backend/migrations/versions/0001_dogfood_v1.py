"""Install the frozen DogFood V1 schema.

Revision ID: 0001_dogfood_v1
Revises: none

Tables/constraints/indexes use Alembic operations. PostgreSQL trigger functions
and triggers are explicit versioned DDL. Never import mutable application models
or load the root reference SQL from this historical migration.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_dogfood_v1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA dogfood")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "email_key",
            sa.Text(),
            sa.Computed("lower(btrim(email))", persisted=True),
            nullable=False,
        ),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column(
            "username_key",
            sa.Text(),
            sa.Computed("lower(btrim(username))", persisted=True),
            nullable=False,
        ),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column(
            "is_super_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "auth_version", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
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
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.CheckConstraint("auth_version >= 1", name="ck_users_auth_version"),
        sa.UniqueConstraint("email_key", name="uq_users_email"),
        sa.UniqueConstraint("username_key", name="uq_users_username"),
        sa.CheckConstraint("btrim(email) <> ''", name="ck_users_email"),
        sa.CheckConstraint("btrim(username) <> ''", name="ck_users_username"),
        sa.CheckConstraint("btrim(password_hash) <> ''", name="ck_users_password_hash"),
        sa.CheckConstraint("btrim(full_name) <> ''", name="ck_users_full_name"),
        schema="dogfood",
    )
    op.create_table(
        "platform_terms_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("version_label", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_platform_terms_versions"),
        sa.UniqueConstraint("version_label", name="uq_platform_terms_versions_label"),
        sa.CheckConstraint(
            "btrim(version_label) <> ''",
            name="ck_platform_terms_versions_version_label",
        ),
        sa.CheckConstraint("btrim(body) <> ''", name="ck_platform_terms_versions_body"),
        schema="dogfood",
    )
    op.create_table(
        "hackathons",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organizer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "organizer_role",
            sa.Text(),
            sa.Computed("'ORGANIZER'::text", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "organizer_status",
            sa.Text(),
            sa.Computed("'ACTIVE'::text", persisted=True),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_key", sa.Text(), nullable=True),
        sa.Column("cover_key", sa.Text(), nullable=True),
        sa.Column("format", sa.Text(), nullable=True),
        sa.Column("venue", sa.Text(), nullable=True),
        sa.Column(
            "display_timezone",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'UTC'"),
        ),
        sa.Column(
            "lifecycle_status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("registration_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registration_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hackathon_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("judging_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("judging_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hackathon_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "team_min_size", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("team_max_size", sa.Integer(), nullable=True),
        sa.Column(
            "result_gallery_mode",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'WINNERS_ONLY'"),
        ),
        sa.Column(
            "minimum_reviews_per_project",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "current_rules_version_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "current_result_publication_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("rubric_locked_at", sa.DateTime(timezone=True), nullable=True),
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
        schema="dogfood",
    )
    op.create_table(
        "hackathon_memberships",
        sa.Column(
            "hackathon_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'ACTIVE'")
        ),
        sa.Column(
            "status_changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column(
            "status_changed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "hackathon_rules_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("rules", sa.Text(), nullable=False),
        sa.Column("eligibility_description", sa.Text(), nullable=True),
        sa.Column(
            "eligibility_flags",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "country_lists",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "hackathon_tracks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "name_key",
            sa.Text(),
            sa.Computed("lower(btrim(name))", persisted=True),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_tracks"),
        sa.UniqueConstraint(
            "hackathon_id", "name_key", name="uq_hackathon_tracks_name"
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_hackathon_tracks_event_id"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_hackathon_tracks_name"),
        schema="dogfood",
    )
    op.create_table(
        "hackathon_sponsors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("logo_key", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("tier", sa.Text(), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_sponsors"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_hackathon_sponsors_name"),
        schema="dogfood",
    )
    op.create_table(
        "hackathon_schedule_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_hackathon_schedule_items"),
        sa.CheckConstraint(
            "end_at IS NULL OR end_at >= start_at",
            name="ck_hackathon_schedule_items_dates",
        ),
        sa.CheckConstraint(
            "btrim(title) <> ''", name="ck_hackathon_schedule_items_title"
        ),
        schema="dogfood",
    )
    op.create_table(
        "platform_announcements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edited_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_platform_announcements"),
        sa.CheckConstraint(
            "btrim(title) <> ''", name="ck_platform_announcements_title"
        ),
        sa.CheckConstraint("btrim(body) <> ''", name="ck_platform_announcements_body"),
        schema="dogfood",
    )
    op.create_table(
        "hackathon_change_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", sa.Text(), nullable=False),
        sa.Column(
            "requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "expected_owner_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("target_owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'PENDING'")
        ),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("before_data", postgresql.JSONB(), nullable=True),
        sa.Column("after_data", postgresql.JSONB(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        sa.CheckConstraint("btrim(action) <> ''", name="ck_audit_events_action"),
        sa.CheckConstraint(
            "btrim(entity_type) <> ''", name="ck_audit_events_entity_type"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(before_data) = 'object'", name="ck_audit_events_before_data"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(after_data) = 'object'", name="ck_audit_events_after_data"
        ),
        schema="dogfood",
    )
    op.create_table(
        "hackathon_registrations",
        sa.Column(
            "hackathon_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "participant_role",
            sa.Text(),
            sa.Computed("'PARTICIPANT'::text", persisted=True),
            nullable=False,
        ),
        sa.Column("participation_preference", sa.Text(), nullable=False),
        sa.Column("referral_source", sa.Text(), nullable=True),
        sa.Column("country_snapshot", sa.Text(), nullable=False),
        sa.Column(
            "eligibility_attestations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "accepted_rules_version_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "accepted_terms_version_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "rules_accepted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column(
            "terms_accepted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "participant_profiles",
        sa.Column(
            "hackathon_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column(
            "skills",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "looking_for_roles",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "looking_for_team",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "discovery_opt_in",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "external_profile_urls",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
        sa.PrimaryKeyConstraint(
            "hackathon_id", "user_id", name="pk_participant_profiles"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(external_profile_urls) = 'object'",
            name="ck_participant_profiles_external_profile_urls",
        ),
        schema="dogfood",
    )
    op.create_table(
        "teams",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leader_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("roster_locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dissolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
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
        sa.PrimaryKeyConstraint("id", name="pk_teams"),
        sa.CheckConstraint(
            "(dissolved_at IS NULL AND leader_user_id IS NOT NULL) OR (dissolved_at IS NOT NULL AND leader_user_id IS NULL)",
            name="ck_teams_leader",
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_teams_event_id"),
        sa.CheckConstraint("version >= 1", name="ck_teams_version"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_teams_name"),
        schema="dogfood",
    )
    op.create_table(
        "team_members",
        sa.Column(
            "hackathon_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.PrimaryKeyConstraint("hackathon_id", "user_id", name="pk_team_members"),
        sa.UniqueConstraint(
            "hackathon_id", "team_id", "user_id", name="uq_team_members_team_user"
        ),
        schema="dogfood",
    )
    op.create_table(
        "team_membership_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_team_membership_events"),
        sa.CheckConstraint(
            "event_type IN ('JOINED', 'LEFT')",
            name="ck_team_membership_events_event_type",
        ),
        schema="dogfood",
    )
    op.create_table(
        "team_invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("invite_kind", sa.Text(), nullable=False),
        sa.Column("target_email", sa.Text(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column(
            "use_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "team_invite_redemptions",
        sa.Column(
            "invite_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "redeemed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.PrimaryKeyConstraint(
            "invite_id", "user_id", name="pk_team_invite_redemptions"
        ),
        schema="dogfood",
    )
    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "submitted_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("tagline", sa.Text(), nullable=False),
        sa.Column("inspiration", sa.Text(), nullable=False),
        sa.Column("what_it_does", sa.Text(), nullable=False),
        sa.Column("how_it_was_built", sa.Text(), nullable=False),
        sa.Column("challenges", sa.Text(), nullable=False),
        sa.Column("accomplishments", sa.Text(), nullable=False),
        sa.Column("what_we_learned", sa.Text(), nullable=False),
        sa.Column("whats_next", sa.Text(), nullable=False),
        sa.Column(
            "submitted_at",
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("disqualified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "disqualified_by_user_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("disqualification_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
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
        schema="dogfood",
    )
    op.create_table(
        "project_submission_members",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("was_leader", sa.Boolean(), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.PrimaryKeyConstraint(
            "project_id", "user_id", name="pk_project_submission_members"
        ),
        schema="dogfood",
    )
    op.create_table(
        "project_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("link_type", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_links"),
        sa.CheckConstraint(
            "link_type IN ('GITHUB', 'LIVE_DEMO', 'YOUTUBE', 'GOOGLE_DRIVE', 'ONEDRIVE', 'OTHER')",
            name="ck_project_links_link_type",
        ),
        sa.CheckConstraint(
            "url ~ '^https://[^[:space:]]+$'", name="ck_project_links_https"
        ),
        schema="dogfood",
    )
    op.create_table(
        "project_media",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_media"),
        sa.CheckConstraint("size_bytes > 0", name="ck_project_media_size"),
        sa.CheckConstraint("mime_type LIKE 'image/%'", name="ck_project_media_image"),
        sa.CheckConstraint(
            "btrim(storage_key) <> ''", name="ck_project_media_storage_key"
        ),
        schema="dogfood",
    )
    op.create_table(
        "project_technologies",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "normalized_key",
            sa.Text(),
            sa.Computed("lower(btrim(display_name))", persisted=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint(
            "project_id", "normalized_key", name="pk_project_technologies"
        ),
        sa.CheckConstraint(
            "btrim(display_name) <> ''", name="ck_project_technologies_display_name"
        ),
        schema="dogfood",
    )
    op.create_table(
        "judge_invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_email", sa.Text(), nullable=False),
        sa.Column(
            "target_email_key",
            sa.Text(),
            sa.Computed("lower(btrim(target_email))", persisted=True),
            nullable=False,
        ),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'PENDING'")
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "judge_profiles",
        sa.Column(
            "hackathon_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "judge_role",
            sa.Text(),
            sa.Computed("'JUDGE'::text", persisted=True),
            nullable=False,
        ),
        sa.Column("public_name", sa.Text(), nullable=False),
        sa.Column("public_bio", sa.Text(), nullable=True),
        sa.Column("avatar_key", sa.Text(), nullable=True),
        sa.Column(
            "publication_consent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("hackathon_id", "user_id", name="pk_judge_profiles"),
        sa.CheckConstraint(
            "btrim(public_name) <> ''", name="ck_judge_profiles_public_name"
        ),
        schema="dogfood",
    )
    op.create_table(
        "judge_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("judge_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "judge_role",
            sa.Text(),
            sa.Computed("'JUDGE'::text", persisted=True),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_judge_assignments"),
        sa.UniqueConstraint(
            "judge_user_id", "project_id", name="uq_judge_assignments_judge_project"
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_judge_assignments_event_id"),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND revoked_by_user_id IS NULL AND revocation_reason IS NULL) OR (revoked_at IS NOT NULL AND revoked_by_user_id IS NOT NULL AND revocation_reason IS NOT NULL AND btrim(revocation_reason) <> '')",
            name="ck_judge_assignments_revocation",
        ),
        schema="dogfood",
    )
    op.create_table(
        "judging_criteria",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("weight_bps", sa.Integer(), nullable=False),
        sa.Column("max_score", sa.Numeric(12, 4), nullable=False),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
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
        schema="dogfood",
    )
    op.create_table(
        "judge_reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default=sa.text("'DRAFT'")
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "invalidated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
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
        schema="dogfood",
    )
    op.create_table(
        "judge_scores",
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "review_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "criterion_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("score", sa.Numeric(12, 4), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("review_id", "criterion_id", name="pk_judge_scores"),
        sa.CheckConstraint(
            "score >= 0 AND score <> 'NaN'::numeric", name="ck_judge_scores_score"
        ),
        schema="dogfood",
    )
    op.create_table(
        "awards",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prize", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("selected_project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selected_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("selection_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_awards"),
        sa.CheckConstraint("rank IS NULL OR rank >= 1", name="ck_awards_rank"),
        sa.CheckConstraint(
            "(selected_project_id IS NULL AND selected_by_user_id IS NULL AND selected_at IS NULL AND selection_reason IS NULL) OR (selected_project_id IS NOT NULL AND selected_by_user_id IS NOT NULL AND selected_at IS NOT NULL)",
            name="ck_awards_selection",
        ),
        sa.UniqueConstraint("hackathon_id", "id", name="uq_awards_event_id"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_awards_name"),
        schema="dogfood",
    )
    op.create_table(
        "result_publications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_number", sa.Integer(), nullable=False),
        sa.Column(
            "supersedes_publication_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "published_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("statement_timestamp()"),
        ),
        sa.Column("scoring_method", sa.Text(), nullable=False),
        sa.Column("calculation_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("correction_reason", sa.Text(), nullable=True),
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
        schema="dogfood",
    )
    op.create_table(
        "result_entries",
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "publication_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("final_score", sa.Numeric(9, 6), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("project_name_snapshot", sa.Text(), nullable=False),
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
        schema="dogfood",
    )
    op.create_table(
        "result_awards",
        sa.Column("hackathon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "publication_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "award_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("award_name_snapshot", sa.Text(), nullable=False),
        sa.Column("prize_snapshot", sa.Text(), nullable=True),
        sa.Column("selected_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("publication_id", "award_id", name="pk_result_awards"),
        sa.CheckConstraint(
            "btrim(award_name_snapshot) <> ''",
            name="ck_result_awards_award_name_snapshot",
        ),
        schema="dogfood",
    )
    # Add references after all tables exist, including the two deliberate cycles.
    op.create_foreign_key(
        "fk_platform_terms_versions_created_by_user_id",
        "platform_terms_versions",
        "users",
        ["created_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathons_created_by_user_id",
        "hackathons",
        "users",
        ["created_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathons_organizer_user_id",
        "hackathons",
        "users",
        ["organizer_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathons_organizer",
        "hackathons",
        "hackathon_memberships",
        ["id", "organizer_user_id", "organizer_role", "organizer_status"],
        ["hackathon_id", "user_id", "role", "status"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="NO ACTION",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_hackathons_rules",
        "hackathons",
        "hackathon_rules_versions",
        ["id", "current_rules_version_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathons_publication",
        "hackathons",
        "result_publications",
        ["id", "current_result_publication_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_memberships_hackathon_id",
        "hackathon_memberships",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_memberships_user_id",
        "hackathon_memberships",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_memberships_status_changed_by_user_id",
        "hackathon_memberships",
        "users",
        ["status_changed_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_rules_versions_hackathon_id",
        "hackathon_rules_versions",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_rules_versions_created_by_user_id",
        "hackathon_rules_versions",
        "users",
        ["created_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_tracks_hackathon_id",
        "hackathon_tracks",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_sponsors_hackathon_id",
        "hackathon_sponsors",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_schedule_items_hackathon_id",
        "hackathon_schedule_items",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_platform_announcements_created_by_user_id",
        "platform_announcements",
        "users",
        ["created_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_platform_announcements_edited_by_user_id",
        "platform_announcements",
        "users",
        ["edited_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_change_requests_hackathon_id",
        "hackathon_change_requests",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_change_requests_requested_by_user_id",
        "hackathon_change_requests",
        "users",
        ["requested_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_change_requests_expected_owner_user_id",
        "hackathon_change_requests",
        "users",
        ["expected_owner_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_change_requests_target_owner_user_id",
        "hackathon_change_requests",
        "users",
        ["target_owner_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_change_requests_reviewed_by_user_id",
        "hackathon_change_requests",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_audit_events_hackathon_id",
        "audit_events",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_audit_events_actor_user_id",
        "audit_events",
        "users",
        ["actor_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_registrations_hackathon_id",
        "hackathon_registrations",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_registrations_user_id",
        "hackathon_registrations",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_registrations_participant",
        "hackathon_registrations",
        "hackathon_memberships",
        ["hackathon_id", "user_id", "participant_role"],
        ["hackathon_id", "user_id", "role"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_registrations_rules",
        "hackathon_registrations",
        "hackathon_rules_versions",
        ["hackathon_id", "accepted_rules_version_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_hackathon_registrations_terms",
        "hackathon_registrations",
        "platform_terms_versions",
        ["accepted_terms_version_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_participant_profiles_hackathon_id",
        "participant_profiles",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_participant_profiles_user_id",
        "participant_profiles",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_participant_profiles_registration",
        "participant_profiles",
        "hackathon_registrations",
        ["hackathon_id", "user_id"],
        ["hackathon_id", "user_id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_teams_hackathon_id",
        "teams",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_teams_created_by_user_id",
        "teams",
        "users",
        ["created_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_teams_leader_user_id",
        "teams",
        "users",
        ["leader_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_teams_leader",
        "teams",
        "team_members",
        ["hackathon_id", "id", "leader_user_id"],
        ["hackathon_id", "team_id", "user_id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="NO ACTION",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_team_members_hackathon_id",
        "team_members",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_members_user_id",
        "team_members",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_members_registration",
        "team_members",
        "hackathon_registrations",
        ["hackathon_id", "user_id"],
        ["hackathon_id", "user_id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_members_team",
        "team_members",
        "teams",
        ["hackathon_id", "team_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_membership_events_hackathon_id",
        "team_membership_events",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_membership_events_user_id",
        "team_membership_events",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_membership_events_team",
        "team_membership_events",
        "teams",
        ["hackathon_id", "team_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_invites_hackathon_id",
        "team_invites",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_invites_invited_by_user_id",
        "team_invites",
        "users",
        ["invited_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_invites_team",
        "team_invites",
        "teams",
        ["hackathon_id", "team_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_invite_redemptions_user_id",
        "team_invite_redemptions",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_team_invite_redemptions_invite_team",
        "team_invite_redemptions",
        "team_invites",
        ["invite_id", "team_id"],
        ["id", "team_id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_projects_hackathon_id",
        "projects",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_projects_submitted_by_user_id",
        "projects",
        "users",
        ["submitted_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_projects_deleted_by_user_id",
        "projects",
        "users",
        ["deleted_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_projects_disqualified_by_user_id",
        "projects",
        "users",
        ["disqualified_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_projects_team",
        "projects",
        "teams",
        ["hackathon_id", "team_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_projects_track",
        "projects",
        "hackathon_tracks",
        ["hackathon_id", "track_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_project_submission_members_user_id",
        "project_submission_members",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_project_submission_members_project_team",
        "project_submission_members",
        "projects",
        ["project_id", "team_id"],
        ["id", "team_id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_project_links_project_id",
        "project_links",
        "projects",
        ["project_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_project_media_project_id",
        "project_media",
        "projects",
        ["project_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_project_technologies_project_id",
        "project_technologies",
        "projects",
        ["project_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_invites_hackathon_id",
        "judge_invites",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_invites_invited_by_user_id",
        "judge_invites",
        "users",
        ["invited_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_invites_accepted_by_user_id",
        "judge_invites",
        "users",
        ["accepted_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_profiles_hackathon_id",
        "judge_profiles",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_profiles_user_id",
        "judge_profiles",
        "users",
        ["user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_profiles_judge",
        "judge_profiles",
        "hackathon_memberships",
        ["hackathon_id", "user_id", "judge_role"],
        ["hackathon_id", "user_id", "role"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_assignments_hackathon_id",
        "judge_assignments",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_assignments_judge_user_id",
        "judge_assignments",
        "users",
        ["judge_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_assignments_assigned_by_user_id",
        "judge_assignments",
        "users",
        ["assigned_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_assignments_revoked_by_user_id",
        "judge_assignments",
        "users",
        ["revoked_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_assignments_judge",
        "judge_assignments",
        "hackathon_memberships",
        ["hackathon_id", "judge_user_id", "judge_role"],
        ["hackathon_id", "user_id", "role"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_assignments_project",
        "judge_assignments",
        "projects",
        ["hackathon_id", "project_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judging_criteria_hackathon_id",
        "judging_criteria",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_reviews_hackathon_id",
        "judge_reviews",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_reviews_invalidated_by_user_id",
        "judge_reviews",
        "users",
        ["invalidated_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_reviews_assignment",
        "judge_reviews",
        "judge_assignments",
        ["hackathon_id", "assignment_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_scores_hackathon_id",
        "judge_scores",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_scores_review",
        "judge_scores",
        "judge_reviews",
        ["hackathon_id", "review_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_judge_scores_criterion",
        "judge_scores",
        "judging_criteria",
        ["hackathon_id", "criterion_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_awards_hackathon_id",
        "awards",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_awards_selected_by_user_id",
        "awards",
        "users",
        ["selected_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_awards_track",
        "awards",
        "hackathon_tracks",
        ["hackathon_id", "track_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_awards_winner",
        "awards",
        "projects",
        ["hackathon_id", "selected_project_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_publications_hackathon_id",
        "result_publications",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_publications_published_by_user_id",
        "result_publications",
        "users",
        ["published_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_publications_supersedes",
        "result_publications",
        "result_publications",
        ["hackathon_id", "supersedes_publication_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_entries_hackathon_id",
        "result_entries",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_entries_publication",
        "result_entries",
        "result_publications",
        ["hackathon_id", "publication_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_entries_project",
        "result_entries",
        "projects",
        ["hackathon_id", "project_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_awards_hackathon_id",
        "result_awards",
        "hackathons",
        ["hackathon_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_awards_selected_by_user_id",
        "result_awards",
        "users",
        ["selected_by_user_id"],
        ["id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_awards_publication",
        "result_awards",
        "result_publications",
        ["hackathon_id", "publication_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_awards_award",
        "result_awards",
        "awards",
        ["hackathon_id", "award_id"],
        ["hackathon_id", "id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_foreign_key(
        "fk_result_awards_entry",
        "result_awards",
        "result_entries",
        ["publication_id", "project_id"],
        ["publication_id", "project_id"],
        source_schema="dogfood",
        referent_schema="dogfood",
        ondelete="RESTRICT",
        deferrable=False,
    )
    op.create_index(
        "ix_hackathon_memberships_organizer",
        "hackathon_memberships",
        ["hackathon_id"],
        unique=True,
        schema="dogfood",
        postgresql_where=sa.text("role = 'ORGANIZER'"),
    )
    op.create_index(
        "ix_hackathon_memberships_event_role",
        "hackathon_memberships",
        ["hackathon_id", "role"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_hackathon_memberships_user",
        "hackathon_memberships",
        ["user_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_hackathons_lifecycle",
        "hackathons",
        ["lifecycle_status"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_team_members_team",
        "team_members",
        ["team_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_team_membership_events_conflict",
        "team_membership_events",
        ["team_id", "user_id", "event_type"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_team_invites_team",
        "team_invites",
        ["team_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_projects_track", "projects", ["track_id"], unique=False, schema="dogfood"
    )
    op.create_index(
        "ix_judge_invites_pending",
        "judge_invites",
        ["hackathon_id", "target_email_key"],
        unique=True,
        schema="dogfood",
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_index(
        "ix_hackathon_change_requests_pending",
        "hackathon_change_requests",
        ["hackathon_id", "request_type"],
        unique=True,
        schema="dogfood",
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_index(
        "ix_judge_assignments_judge_event",
        "judge_assignments",
        ["judge_user_id", "hackathon_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_judge_assignments_project",
        "judge_assignments",
        ["project_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_judge_assignments_event_revoked",
        "judge_assignments",
        ["hackathon_id", "revoked_at"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_judge_scores_criterion",
        "judge_scores",
        ["criterion_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_audit_events_event_time",
        "audit_events",
        ["hackathon_id", "created_at"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_audit_events_entity",
        "audit_events",
        ["entity_type", "entity_id"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_hackathon_sponsors_event_order",
        "hackathon_sponsors",
        ["hackathon_id", "sort_order"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_hackathon_schedule_items_event_order",
        "hackathon_schedule_items",
        ["hackathon_id", "sort_order"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_project_links_project_order",
        "project_links",
        ["project_id", "sort_order"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_project_media_project_order",
        "project_media",
        ["project_id", "sort_order"],
        unique=False,
        schema="dogfood",
    )
    op.create_index(
        "ix_project_submission_members_leader",
        "project_submission_members",
        ["project_id"],
        unique=True,
        schema="dogfood",
        postgresql_where=sa.text("was_leader"),
    )
    op.execute(r"""
CREATE FUNCTION dogfood.touch_updated_at() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
BEGIN NEW.updated_at := statement_timestamp(); RETURN NEW; END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.reject_history_mutation() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
BEGIN RAISE EXCEPTION 'immutable history: %', TG_TABLE_NAME USING ERRCODE = '23514'; END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_identity() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE col text;
BEGIN
  FOREACH col IN ARRAY TG_ARGV LOOP
    IF to_jsonb(NEW)->col IS DISTINCT FROM to_jsonb(OLD)->col THEN
      RAISE EXCEPTION 'immutable identity: %.%', TG_TABLE_NAME, col USING ERRCODE = '23514';
    END IF;
  END LOOP;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.record_membership_event() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO dogfood.team_membership_events(hackathon_id, team_id, user_id, event_type)
    VALUES (NEW.hackathon_id, NEW.team_id, NEW.user_id, 'JOINED');
    RETURN NEW;
  END IF;
  INSERT INTO dogfood.team_membership_events(hackathon_id, team_id, user_id, event_type)
  VALUES (OLD.hackathon_id, OLD.team_id, OLD.user_id, 'LEFT');
  RETURN OLD;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_rubric_mutation() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE event_id uuid; h dogfood.hackathons%ROWTYPE;
BEGIN
  IF TG_OP = 'DELETE' THEN event_id := OLD.hackathon_id; ELSE event_id := NEW.hackathon_id; END IF;
  SELECT * INTO STRICT h FROM dogfood.hackathons WHERE id = event_id FOR UPDATE;
  IF h.rubric_locked_at IS NOT NULL OR h.judging_start_at <= clock_timestamp() THEN
    RAISE EXCEPTION 'rubric is frozen' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'UPDATE' AND EXISTS (
    SELECT 1 FROM dogfood.judge_scores WHERE criterion_id = OLD.id AND score > NEW.max_score
  ) THEN RAISE EXCEPTION 'criterion maximum below existing score' USING ERRCODE = '23514'; END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_hackathon_state() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE n integer; total bigint; p dogfood.result_publications%ROWTYPE;
BEGIN
  IF OLD.rubric_locked_at IS NOT NULL AND NEW.rubric_locked_at IS DISTINCT FROM OLD.rubric_locked_at THEN
    RAISE EXCEPTION 'rubric lock is permanent' USING ERRCODE = '23514';
  END IF;
  IF OLD.rubric_locked_at IS NOT NULL OR OLD.judging_start_at <= clock_timestamp() THEN
    IF NEW.minimum_reviews_per_project <> OLD.minimum_reviews_per_project THEN
      RAISE EXCEPTION 'review coverage is frozen' USING ERRCODE = '23514';
    END IF;
    IF NEW.judging_start_at IS DISTINCT FROM OLD.judging_start_at THEN
      RAISE EXCEPTION 'cannot reschedule frozen judging start' USING ERRCODE = '23514';
    END IF;
  END IF;
  IF OLD.rubric_locked_at IS NULL AND NEW.rubric_locked_at IS NOT NULL THEN
    SELECT count(*), coalesce(sum(weight_bps),0) INTO n,total
    FROM dogfood.judging_criteria WHERE hackathon_id = OLD.id;
    IF n = 0 OR total <> 10000 THEN
      RAISE EXCEPTION 'rubric requires criteria totaling 10000 bps' USING ERRCODE = '23514';
    END IF;
  END IF;
  IF NEW.current_result_publication_id IS DISTINCT FROM OLD.current_result_publication_id THEN
    IF NEW.current_result_publication_id IS NULL THEN
      RAISE EXCEPTION 'cannot clear publication pointer' USING ERRCODE = '23514';
    END IF;
    SELECT * INTO STRICT p FROM dogfood.result_publications
    WHERE id = NEW.current_result_publication_id AND hackathon_id = OLD.id;
    IF p.supersedes_publication_id IS DISTINCT FROM OLD.current_result_publication_id THEN
      RAISE EXCEPTION 'publication must extend current chain' USING ERRCODE = '23514';
    END IF;
    IF p.calculation_snapshot->'minimum_reviews_per_project' IS DISTINCT FROM to_jsonb(NEW.minimum_reviews_per_project) THEN
      RAISE EXCEPTION 'snapshot review coverage does not match event' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_score_write() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE event_id uuid; rid uuid; r dogfood.judge_reviews%ROWTYPE; maximum numeric;
BEGIN
  IF TG_OP = 'DELETE' THEN event_id := OLD.hackathon_id; rid := OLD.review_id;
  ELSE event_id := NEW.hackathon_id; rid := NEW.review_id; END IF;
  PERFORM 1 FROM dogfood.hackathons WHERE id = event_id FOR SHARE;
  SELECT * INTO STRICT r FROM dogfood.judge_reviews WHERE id = rid AND hackathon_id = event_id FOR UPDATE;
  IF r.status = 'SUBMITTED' THEN
    RAISE EXCEPTION 'move review to draft before changing scores' USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  SELECT max_score INTO STRICT maximum FROM dogfood.judging_criteria
  WHERE id = NEW.criterion_id AND hackathon_id = event_id;
  IF NEW.score < 0 OR NEW.score > maximum OR NEW.score = 'NaN'::numeric THEN
    RAISE EXCEPTION 'score outside criterion range' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.validate_submitted_review() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE h dogfood.hackathons%ROWTYPE; n integer; total bigint; scores integer;
BEGIN
  IF NEW.status <> 'SUBMITTED' THEN RETURN NEW; END IF;
  SELECT * INTO STRICT h FROM dogfood.hackathons WHERE id = NEW.hackathon_id FOR SHARE;
  SELECT count(*), coalesce(sum(weight_bps),0) INTO n,total
  FROM dogfood.judging_criteria WHERE hackathon_id = NEW.hackathon_id;
  SELECT count(*) INTO scores FROM dogfood.judge_scores WHERE review_id = NEW.id;
  IF h.rubric_locked_at IS NULL OR n = 0 OR total <> 10000 OR scores <> n THEN
    RAISE EXCEPTION 'submitted review requires complete frozen rubric' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_judge_invite_acceptance() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
BEGIN
  IF NEW.status = 'ACCEPTED' AND (TG_OP = 'INSERT' OR OLD.status <> 'ACCEPTED') THEN
    IF TG_OP = 'UPDATE' AND OLD.status <> 'PENDING' THEN
      RAISE EXCEPTION 'only pending invitation can be accepted' USING ERRCODE = '23514';
    END IF;
    IF NEW.expires_at <= clock_timestamp() THEN
      RAISE EXCEPTION 'invitation expired' USING ERRCODE = '23514';
    END IF;
  END IF;
  IF TG_OP = 'UPDATE' AND OLD.status IN ('EXPIRED','REVOKED','ACCEPTED') AND NEW.status <> OLD.status THEN
    RAISE EXCEPTION 'invitation terminal state cannot be reopened' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_publication_chain() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE h dogfood.hackathons%ROWTYPE; previous_number integer;
BEGIN
  SELECT * INTO STRICT h FROM dogfood.hackathons WHERE id = NEW.hackathon_id FOR UPDATE;
  IF NEW.supersedes_publication_id IS DISTINCT FROM h.current_result_publication_id THEN
    RAISE EXCEPTION 'publication must supersede current pointer' USING ERRCODE = '23514';
  END IF;
  previous_number := 0;
  IF h.current_result_publication_id IS NOT NULL THEN
    SELECT publication_number INTO STRICT previous_number FROM dogfood.result_publications WHERE id = h.current_result_publication_id;
  END IF;
  IF NEW.publication_number <> previous_number + 1 THEN
    RAISE EXCEPTION 'publication numbers must be consecutive' USING ERRCODE = '23514';
  END IF;
  IF NEW.calculation_snapshot->'minimum_reviews_per_project' IS DISTINCT FROM to_jsonb(h.minimum_reviews_per_project) THEN
    RAISE EXCEPTION 'snapshot requires configured review coverage' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
""")
    op.execute(r"""
CREATE FUNCTION dogfood.guard_publication_children() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
DECLARE current_id uuid; p dogfood.result_publications%ROWTYPE;
BEGIN
  SELECT current_result_publication_id INTO current_id FROM dogfood.hackathons WHERE id = NEW.hackathon_id FOR UPDATE;
  SELECT * INTO STRICT p FROM dogfood.result_publications WHERE id = NEW.publication_id AND hackathon_id = NEW.hackathon_id;
  IF current_id = p.id OR EXISTS (SELECT 1 FROM dogfood.result_publications WHERE supersedes_publication_id = p.id) THEN
    RAISE EXCEPTION 'publication is sealed' USING ERRCODE = '23514';
  END IF;
  IF TG_TABLE_NAME = 'result_entries' AND (to_jsonb(NEW)->>'review_count')::integer < (p.calculation_snapshot->>'minimum_reviews_per_project')::integer THEN
    RAISE EXCEPTION 'result entry below configured coverage' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
""")
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.users FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.users FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','created_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.platform_terms_versions FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.hackathons FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathons FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','created_at','created_by_user_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_memberships FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','user_id','joined_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.hackathon_rules_versions FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_tracks FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_sponsors FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_schedule_items FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.platform_announcements FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.platform_announcements FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','created_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_change_requests FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.audit_events FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.hackathon_registrations FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.participant_profiles FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.participant_profiles FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','created_at','user_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.teams FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.teams FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','created_by_user_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.team_members FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','team_id','user_id','joined_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.team_membership_events FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.team_invites FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','team_id','invited_by_user_id','token_hash','invite_kind','target_email');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.team_invite_redemptions FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.projects FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.projects FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','team_id','submitted_by_user_id','submitted_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.project_submission_members FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.project_links FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','project_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.project_media FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','project_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.project_technologies FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('project_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_invites FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','target_email','invited_by_user_id','token_hash','expires_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_profiles FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','user_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_assignments FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','judge_user_id','project_id','assigned_by_user_id','assigned_at');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judging_criteria FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.judge_reviews FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_reviews FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','assignment_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_scores FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','review_id','criterion_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.awards FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.result_publications FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.result_entries FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.result_awards FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_record_history AFTER INSERT OR DELETE ON dogfood.team_members FOR EACH ROW EXECUTE FUNCTION dogfood.record_membership_event();"
    )
    op.execute(
        "CREATE TRIGGER tr_rubric_guard BEFORE INSERT OR UPDATE OR DELETE ON dogfood.judging_criteria FOR EACH ROW EXECUTE FUNCTION dogfood.guard_rubric_mutation();"
    )
    op.execute(
        "CREATE TRIGGER tr_state_guard BEFORE UPDATE ON dogfood.hackathons FOR EACH ROW EXECUTE FUNCTION dogfood.guard_hackathon_state();"
    )
    op.execute(
        "CREATE TRIGGER tr_score_guard BEFORE INSERT OR UPDATE OR DELETE ON dogfood.judge_scores FOR EACH ROW EXECUTE FUNCTION dogfood.guard_score_write();"
    )
    op.execute(
        "CREATE TRIGGER tr_submit_guard BEFORE INSERT OR UPDATE ON dogfood.judge_reviews FOR EACH ROW EXECUTE FUNCTION dogfood.validate_submitted_review();"
    )
    op.execute(
        "CREATE TRIGGER tr_accept_guard BEFORE INSERT OR UPDATE ON dogfood.judge_invites FOR EACH ROW EXECUTE FUNCTION dogfood.guard_judge_invite_acceptance();"
    )
    op.execute(
        "CREATE TRIGGER tr_chain_guard BEFORE INSERT ON dogfood.result_publications FOR EACH ROW EXECUTE FUNCTION dogfood.guard_publication_chain();"
    )
    op.execute(
        "CREATE TRIGGER tr_children_guard BEFORE INSERT ON dogfood.result_entries FOR EACH ROW EXECUTE FUNCTION dogfood.guard_publication_children();"
    )
    op.execute(
        "CREATE TRIGGER tr_children_guard BEFORE INSERT ON dogfood.result_awards FOR EACH ROW EXECUTE FUNCTION dogfood.guard_publication_children();"
    )


def downgrade() -> None:
    """Development rollback: remove only objects owned by this revision."""
    op.execute("DROP TRIGGER tr_children_guard ON dogfood.result_awards")
    op.execute("DROP TRIGGER tr_children_guard ON dogfood.result_entries")
    op.execute("DROP TRIGGER tr_chain_guard ON dogfood.result_publications")
    op.execute("DROP TRIGGER tr_accept_guard ON dogfood.judge_invites")
    op.execute("DROP TRIGGER tr_submit_guard ON dogfood.judge_reviews")
    op.execute("DROP TRIGGER tr_score_guard ON dogfood.judge_scores")
    op.execute("DROP TRIGGER tr_state_guard ON dogfood.hackathons")
    op.execute("DROP TRIGGER tr_rubric_guard ON dogfood.judging_criteria")
    op.execute("DROP TRIGGER tr_record_history ON dogfood.team_members")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.result_awards")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.result_entries")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.result_publications")
    op.execute("DROP TRIGGER tr_identity ON dogfood.awards")
    op.execute("DROP TRIGGER tr_identity ON dogfood.judge_scores")
    op.execute("DROP TRIGGER tr_identity ON dogfood.judge_reviews")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.judge_reviews")
    op.execute("DROP TRIGGER tr_identity ON dogfood.judging_criteria")
    op.execute("DROP TRIGGER tr_identity ON dogfood.judge_assignments")
    op.execute("DROP TRIGGER tr_identity ON dogfood.judge_profiles")
    op.execute("DROP TRIGGER tr_identity ON dogfood.judge_invites")
    op.execute("DROP TRIGGER tr_identity ON dogfood.project_technologies")
    op.execute("DROP TRIGGER tr_identity ON dogfood.project_media")
    op.execute("DROP TRIGGER tr_identity ON dogfood.project_links")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.project_submission_members")
    op.execute("DROP TRIGGER tr_identity ON dogfood.projects")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.projects")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.team_invite_redemptions")
    op.execute("DROP TRIGGER tr_identity ON dogfood.team_invites")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.team_membership_events")
    op.execute("DROP TRIGGER tr_identity ON dogfood.team_members")
    op.execute("DROP TRIGGER tr_identity ON dogfood.teams")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.teams")
    op.execute("DROP TRIGGER tr_identity ON dogfood.participant_profiles")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.participant_profiles")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.hackathon_registrations")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.audit_events")
    op.execute("DROP TRIGGER tr_identity ON dogfood.hackathon_change_requests")
    op.execute("DROP TRIGGER tr_identity ON dogfood.platform_announcements")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.platform_announcements")
    op.execute("DROP TRIGGER tr_identity ON dogfood.hackathon_schedule_items")
    op.execute("DROP TRIGGER tr_identity ON dogfood.hackathon_sponsors")
    op.execute("DROP TRIGGER tr_identity ON dogfood.hackathon_tracks")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.hackathon_rules_versions")
    op.execute("DROP TRIGGER tr_identity ON dogfood.hackathon_memberships")
    op.execute("DROP TRIGGER tr_identity ON dogfood.hackathons")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.hackathons")
    op.execute("DROP TRIGGER tr_immutable ON dogfood.platform_terms_versions")
    op.execute("DROP TRIGGER tr_identity ON dogfood.users")
    op.execute("DROP TRIGGER tr_touch_updated_at ON dogfood.users")
    op.execute("DROP FUNCTION dogfood.guard_publication_children()")
    op.execute("DROP FUNCTION dogfood.guard_publication_chain()")
    op.execute("DROP FUNCTION dogfood.guard_judge_invite_acceptance()")
    op.execute("DROP FUNCTION dogfood.validate_submitted_review()")
    op.execute("DROP FUNCTION dogfood.guard_score_write()")
    op.execute("DROP FUNCTION dogfood.guard_hackathon_state()")
    op.execute("DROP FUNCTION dogfood.guard_rubric_mutation()")
    op.execute("DROP FUNCTION dogfood.record_membership_event()")
    op.execute("DROP FUNCTION dogfood.guard_identity()")
    op.execute("DROP FUNCTION dogfood.reject_history_mutation()")
    op.execute("DROP FUNCTION dogfood.touch_updated_at()")
    op.drop_constraint(
        "fk_result_awards_hackathon_id",
        "result_awards",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_awards_selected_by_user_id",
        "result_awards",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_awards_publication",
        "result_awards",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_awards_award", "result_awards", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_result_awards_entry", "result_awards", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_result_entries_hackathon_id",
        "result_entries",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_entries_publication",
        "result_entries",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_entries_project",
        "result_entries",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_publications_hackathon_id",
        "result_publications",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_publications_published_by_user_id",
        "result_publications",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_publications_supersedes",
        "result_publications",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_awards_hackathon_id", "awards", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_awards_selected_by_user_id", "awards", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_awards_track", "awards", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_awards_winner", "awards", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_judge_scores_hackathon_id",
        "judge_scores",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_scores_review", "judge_scores", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_judge_scores_criterion",
        "judge_scores",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_reviews_hackathon_id",
        "judge_reviews",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_reviews_invalidated_by_user_id",
        "judge_reviews",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_reviews_assignment",
        "judge_reviews",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judging_criteria_hackathon_id",
        "judging_criteria",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_assignments_hackathon_id",
        "judge_assignments",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_assignments_judge_user_id",
        "judge_assignments",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_assignments_assigned_by_user_id",
        "judge_assignments",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_assignments_revoked_by_user_id",
        "judge_assignments",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_assignments_judge",
        "judge_assignments",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_assignments_project",
        "judge_assignments",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_profiles_hackathon_id",
        "judge_profiles",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_profiles_user_id",
        "judge_profiles",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_profiles_judge",
        "judge_profiles",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_invites_hackathon_id",
        "judge_invites",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_invites_invited_by_user_id",
        "judge_invites",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_judge_invites_accepted_by_user_id",
        "judge_invites",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_project_technologies_project_id",
        "project_technologies",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_project_media_project_id",
        "project_media",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_project_links_project_id",
        "project_links",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_project_submission_members_user_id",
        "project_submission_members",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_project_submission_members_project_team",
        "project_submission_members",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_projects_hackathon_id", "projects", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_projects_submitted_by_user_id",
        "projects",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_projects_deleted_by_user_id",
        "projects",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_projects_disqualified_by_user_id",
        "projects",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_projects_team", "projects", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_projects_track", "projects", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_team_invite_redemptions_user_id",
        "team_invite_redemptions",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_invite_redemptions_invite_team",
        "team_invite_redemptions",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_invites_hackathon_id",
        "team_invites",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_invites_invited_by_user_id",
        "team_invites",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_invites_team", "team_invites", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_team_membership_events_hackathon_id",
        "team_membership_events",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_membership_events_user_id",
        "team_membership_events",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_membership_events_team",
        "team_membership_events",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_members_hackathon_id",
        "team_members",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_members_user_id", "team_members", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_team_members_registration",
        "team_members",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_team_members_team", "team_members", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_teams_hackathon_id", "teams", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_teams_created_by_user_id", "teams", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_teams_leader_user_id", "teams", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint("fk_teams_leader", "teams", schema="dogfood", type_="foreignkey")
    op.drop_constraint(
        "fk_participant_profiles_hackathon_id",
        "participant_profiles",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_participant_profiles_user_id",
        "participant_profiles",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_participant_profiles_registration",
        "participant_profiles",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_registrations_hackathon_id",
        "hackathon_registrations",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_registrations_user_id",
        "hackathon_registrations",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_registrations_participant",
        "hackathon_registrations",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_registrations_rules",
        "hackathon_registrations",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_registrations_terms",
        "hackathon_registrations",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_audit_events_hackathon_id",
        "audit_events",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_audit_events_actor_user_id",
        "audit_events",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_change_requests_hackathon_id",
        "hackathon_change_requests",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_change_requests_requested_by_user_id",
        "hackathon_change_requests",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_change_requests_expected_owner_user_id",
        "hackathon_change_requests",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_change_requests_target_owner_user_id",
        "hackathon_change_requests",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_change_requests_reviewed_by_user_id",
        "hackathon_change_requests",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_platform_announcements_created_by_user_id",
        "platform_announcements",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_platform_announcements_edited_by_user_id",
        "platform_announcements",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_schedule_items_hackathon_id",
        "hackathon_schedule_items",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_sponsors_hackathon_id",
        "hackathon_sponsors",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_tracks_hackathon_id",
        "hackathon_tracks",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_rules_versions_hackathon_id",
        "hackathon_rules_versions",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_rules_versions_created_by_user_id",
        "hackathon_rules_versions",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_memberships_hackathon_id",
        "hackathon_memberships",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_memberships_user_id",
        "hackathon_memberships",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathon_memberships_status_changed_by_user_id",
        "hackathon_memberships",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathons_created_by_user_id",
        "hackathons",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathons_organizer_user_id",
        "hackathons",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_hackathons_organizer", "hackathons", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_hackathons_rules", "hackathons", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_hackathons_publication", "hackathons", schema="dogfood", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_platform_terms_versions_created_by_user_id",
        "platform_terms_versions",
        schema="dogfood",
        type_="foreignkey",
    )
    op.drop_table("result_awards", schema="dogfood")
    op.drop_table("result_entries", schema="dogfood")
    op.drop_table("result_publications", schema="dogfood")
    op.drop_table("awards", schema="dogfood")
    op.drop_table("judge_scores", schema="dogfood")
    op.drop_table("judge_reviews", schema="dogfood")
    op.drop_table("judging_criteria", schema="dogfood")
    op.drop_table("judge_assignments", schema="dogfood")
    op.drop_table("judge_profiles", schema="dogfood")
    op.drop_table("judge_invites", schema="dogfood")
    op.drop_table("project_technologies", schema="dogfood")
    op.drop_table("project_media", schema="dogfood")
    op.drop_table("project_links", schema="dogfood")
    op.drop_table("project_submission_members", schema="dogfood")
    op.drop_table("projects", schema="dogfood")
    op.drop_table("team_invite_redemptions", schema="dogfood")
    op.drop_table("team_invites", schema="dogfood")
    op.drop_table("team_membership_events", schema="dogfood")
    op.drop_table("team_members", schema="dogfood")
    op.drop_table("teams", schema="dogfood")
    op.drop_table("participant_profiles", schema="dogfood")
    op.drop_table("hackathon_registrations", schema="dogfood")
    op.drop_table("audit_events", schema="dogfood")
    op.drop_table("hackathon_change_requests", schema="dogfood")
    op.drop_table("platform_announcements", schema="dogfood")
    op.drop_table("hackathon_schedule_items", schema="dogfood")
    op.drop_table("hackathon_sponsors", schema="dogfood")
    op.drop_table("hackathon_tracks", schema="dogfood")
    op.drop_table("hackathon_rules_versions", schema="dogfood")
    op.drop_table("hackathon_memberships", schema="dogfood")
    op.drop_table("hackathons", schema="dogfood")
    op.drop_table("platform_terms_versions", schema="dogfood")
    op.drop_table("users", schema="dogfood")
    op.execute("DROP SCHEMA dogfood")
