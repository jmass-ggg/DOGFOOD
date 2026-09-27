-- DogFood V1 proposed physical schema: owner review required before T2.
-- Authoritative owner decisions and proposed implementation details:
-- docs/DATABASE_SCHEMA_SPEC.md. No domain migration or application models.
-- PostgreSQL 16+. Install once into an empty database as migration owner.
-- No credentials, grants, RLS, extensions, DROP or IF NOT EXISTS.
BEGIN;
CREATE SCHEMA dogfood;

CREATE TABLE dogfood.users (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    email text NOT NULL,
    email_key text GENERATED ALWAYS AS (lower(btrim(email))) STORED NOT NULL,
    username text NOT NULL,
    username_key text GENERATED ALWAYS AS (lower(btrim(username))) STORED NOT NULL,
    password_hash text NOT NULL,
    full_name text NOT NULL,
    country text NULL,
    is_super_admin boolean NOT NULL DEFAULT false,
    email_verified_at timestamptz NULL,
    disabled_at timestamptz NULL,
    auth_version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT ck_users_auth_version CHECK (auth_version >= 1),
    CONSTRAINT uq_users_email UNIQUE (email_key),
    CONSTRAINT uq_users_username UNIQUE (username_key),
    CONSTRAINT ck_users_email CHECK (btrim(email) <> ''),
    CONSTRAINT ck_users_username CHECK (btrim(username) <> ''),
    CONSTRAINT ck_users_password_hash CHECK (btrim(password_hash) <> ''),
    CONSTRAINT ck_users_full_name CHECK (btrim(full_name) <> '')
);

CREATE TABLE dogfood.platform_terms_versions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    version_label text NOT NULL,
    body text NOT NULL,
    published_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    created_by_user_id uuid NOT NULL,
    CONSTRAINT pk_platform_terms_versions PRIMARY KEY (id),
    CONSTRAINT uq_platform_terms_versions_label UNIQUE (version_label),
    CONSTRAINT ck_platform_terms_versions_version_label CHECK (btrim(version_label) <> ''),
    CONSTRAINT ck_platform_terms_versions_body CHECK (btrim(body) <> '')
);

CREATE TABLE dogfood.hackathons (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    created_by_user_id uuid NOT NULL,
    organizer_user_id uuid NOT NULL,
    organizer_role text GENERATED ALWAYS AS ('ORGANIZER'::text) STORED NOT NULL,
    organizer_status text GENERATED ALWAYS AS ('ACTIVE'::text) STORED NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    tagline text NULL,
    description text NULL,
    logo_key text NULL,
    cover_key text NULL,
    format text NULL,
    venue text NULL,
    display_timezone text NOT NULL DEFAULT 'UTC',
    lifecycle_status text NOT NULL DEFAULT 'DRAFT',
    registration_start_at timestamptz NULL,
    registration_end_at timestamptz NULL,
    hackathon_start_at timestamptz NULL,
    submission_deadline_at timestamptz NULL,
    judging_start_at timestamptz NULL,
    judging_end_at timestamptz NULL,
    hackathon_end_at timestamptz NULL,
    team_min_size integer NOT NULL DEFAULT 1,
    team_max_size integer NULL,
    result_gallery_mode text NOT NULL DEFAULT 'WINNERS_ONLY',
    minimum_reviews_per_project integer NOT NULL DEFAULT 1,
    current_rules_version_id uuid NULL,
    current_result_publication_id uuid NULL,
    rubric_locked_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_hackathons PRIMARY KEY (id),
    CONSTRAINT ck_hackathons_team_min CHECK (team_min_size >= 1),
    CONSTRAINT ck_hackathons_team_max CHECK (team_max_size IS NULL OR team_max_size >= team_min_size),
    CONSTRAINT ck_hackathons_coverage CHECK (minimum_reviews_per_project >= 1),
    CONSTRAINT uq_hackathons_slug UNIQUE (slug),
    CONSTRAINT ck_hackathons_name CHECK (btrim(name) <> ''),
    CONSTRAINT ck_hackathons_slug CHECK (btrim(slug) <> ''),
    CONSTRAINT ck_hackathons_display_timezone CHECK (btrim(display_timezone) <> ''),
    CONSTRAINT ck_hackathons_lifecycle_status CHECK (lifecycle_status IN ('DRAFT', 'PUBLISHED', 'CANCELLED', 'ARCHIVED')),
    CONSTRAINT ck_hackathons_result_gallery_mode CHECK (result_gallery_mode IN ('WINNERS_ONLY', 'ALL_PROJECTS')),
    CONSTRAINT ck_hackathons_registration_window CHECK (registration_start_at IS NULL OR registration_end_at IS NULL OR registration_start_at <= registration_end_at),
    CONSTRAINT ck_hackathons_registration_before_submission CHECK (registration_end_at IS NULL OR submission_deadline_at IS NULL OR registration_end_at <= submission_deadline_at),
    CONSTRAINT ck_hackathons_event_before_submission CHECK (hackathon_start_at IS NULL OR submission_deadline_at IS NULL OR hackathon_start_at <= submission_deadline_at),
    CONSTRAINT ck_hackathons_submission_before_judging CHECK (submission_deadline_at IS NULL OR judging_start_at IS NULL OR submission_deadline_at <= judging_start_at),
    CONSTRAINT ck_hackathons_judging_window CHECK (judging_start_at IS NULL OR judging_end_at IS NULL OR judging_start_at <= judging_end_at),
    CONSTRAINT ck_hackathons_submission_within_event CHECK (submission_deadline_at IS NULL OR hackathon_end_at IS NULL OR submission_deadline_at <= hackathon_end_at),
    CONSTRAINT ck_hackathons_published CHECK (lifecycle_status <> 'PUBLISHED' OR (registration_start_at IS NOT NULL AND registration_end_at IS NOT NULL AND hackathon_start_at IS NOT NULL AND submission_deadline_at IS NOT NULL AND judging_start_at IS NOT NULL AND judging_end_at IS NOT NULL AND hackathon_end_at IS NOT NULL AND current_rules_version_id IS NOT NULL))
);

CREATE TABLE dogfood.hackathon_memberships (
    hackathon_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role text NOT NULL,
    status text NOT NULL DEFAULT 'ACTIVE',
    status_changed_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    status_changed_by_user_id uuid NULL,
    status_reason text NULL,
    joined_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_hackathon_memberships PRIMARY KEY (hackathon_id, user_id),
    CONSTRAINT uq_hackathon_memberships_role UNIQUE (hackathon_id, user_id, role),
    CONSTRAINT uq_hackathon_memberships_role_status UNIQUE (hackathon_id, user_id, role, status),
    CONSTRAINT ck_hackathon_memberships_role CHECK (role IN ('PARTICIPANT', 'JUDGE', 'HACKATHON_ADMIN', 'ORGANIZER')),
    CONSTRAINT ck_hackathon_memberships_status CHECK (status IN ('ACTIVE', 'BANNED', 'REVOKED')),
    CONSTRAINT ck_hackathon_memberships_status_reason CHECK (status = 'ACTIVE' OR (status_changed_by_user_id IS NOT NULL AND status_reason IS NOT NULL AND btrim(status_reason) <> ''))
);

CREATE TABLE dogfood.hackathon_rules_versions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    version_number integer NOT NULL,
    rules text NOT NULL,
    eligibility_description text NULL,
    eligibility_flags jsonb NOT NULL DEFAULT '{}'::jsonb,
    country_lists jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by_user_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_hackathon_rules_versions PRIMARY KEY (id),
    CONSTRAINT ck_hackathon_rules_versions_number CHECK (version_number >= 1),
    CONSTRAINT uq_hackathon_rules_versions_number UNIQUE (hackathon_id, version_number),
    CONSTRAINT uq_hackathon_rules_versions_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_hackathon_rules_versions_eligibility_flags CHECK (jsonb_typeof(eligibility_flags) = 'object'),
    CONSTRAINT ck_hackathon_rules_versions_country_lists CHECK (jsonb_typeof(country_lists) = 'object'),
    CONSTRAINT ck_hackathon_rules_versions_rules CHECK (btrim(rules) <> '')
);

CREATE TABLE dogfood.hackathon_tracks (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    name text NOT NULL,
    name_key text GENERATED ALWAYS AS (lower(btrim(name))) STORED NOT NULL,
    description text NULL,
    sort_order integer NOT NULL DEFAULT 0,
    CONSTRAINT pk_hackathon_tracks PRIMARY KEY (id),
    CONSTRAINT uq_hackathon_tracks_name UNIQUE (hackathon_id, name_key),
    CONSTRAINT uq_hackathon_tracks_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_hackathon_tracks_name CHECK (btrim(name) <> '')
);

CREATE TABLE dogfood.hackathon_sponsors (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    name text NOT NULL,
    logo_key text NULL,
    url text NULL,
    tier text NULL,
    sort_order integer NOT NULL DEFAULT 0,
    CONSTRAINT pk_hackathon_sponsors PRIMARY KEY (id),
    CONSTRAINT ck_hackathon_sponsors_name CHECK (btrim(name) <> '')
);

CREATE TABLE dogfood.hackathon_schedule_items (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    title text NOT NULL,
    description text NULL,
    start_at timestamptz NOT NULL,
    end_at timestamptz NULL,
    location text NULL,
    link text NULL,
    sort_order integer NOT NULL DEFAULT 0,
    CONSTRAINT pk_hackathon_schedule_items PRIMARY KEY (id),
    CONSTRAINT ck_hackathon_schedule_items_dates CHECK (end_at IS NULL OR end_at >= start_at),
    CONSTRAINT ck_hackathon_schedule_items_title CHECK (btrim(title) <> '')
);

CREATE TABLE dogfood.platform_announcements (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    created_by_user_id uuid NOT NULL,
    edited_by_user_id uuid NULL,
    title text NOT NULL,
    body text NOT NULL,
    is_pinned boolean NOT NULL DEFAULT false,
    published_at timestamptz NULL,
    deleted_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_platform_announcements PRIMARY KEY (id),
    CONSTRAINT ck_platform_announcements_title CHECK (btrim(title) <> ''),
    CONSTRAINT ck_platform_announcements_body CHECK (btrim(body) <> '')
);

CREATE TABLE dogfood.hackathon_change_requests (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    request_type text NOT NULL,
    requested_by_user_id uuid NOT NULL,
    expected_owner_user_id uuid NOT NULL,
    target_owner_user_id uuid NULL,
    reason text NOT NULL,
    status text NOT NULL DEFAULT 'PENDING',
    reviewed_by_user_id uuid NULL,
    reviewed_at timestamptz NULL,
    review_reason text NULL,
    executed_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_hackathon_change_requests PRIMARY KEY (id),
    CONSTRAINT ck_hackathon_change_requests_request_type CHECK (request_type IN ('DELETE_HACKATHON', 'TRANSFER_OWNERSHIP')),
    CONSTRAINT ck_hackathon_change_requests_status CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    CONSTRAINT ck_hackathon_change_requests_reason CHECK (btrim(reason) <> ''),
    CONSTRAINT ck_hackathon_change_requests_target CHECK ((request_type = 'DELETE_HACKATHON' AND target_owner_user_id IS NULL) OR (request_type = 'TRANSFER_OWNERSHIP' AND target_owner_user_id IS NOT NULL AND target_owner_user_id <> expected_owner_user_id)),
    CONSTRAINT ck_hackathon_change_requests_review CHECK ((status = 'PENDING' AND reviewed_by_user_id IS NULL AND reviewed_at IS NULL AND review_reason IS NULL AND executed_at IS NULL) OR (status IN ('APPROVED','REJECTED') AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL AND review_reason IS NOT NULL AND btrim(review_reason) <> '' AND ((status = 'APPROVED' AND executed_at IS NOT NULL) OR (status = 'REJECTED' AND executed_at IS NULL))))
);

CREATE TABLE dogfood.audit_events (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NULL,
    actor_user_id uuid NULL,
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id uuid NOT NULL,
    reason text NULL,
    before_data jsonb NULL,
    after_data jsonb NULL,
    request_id text NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_audit_events PRIMARY KEY (id),
    CONSTRAINT ck_audit_events_action CHECK (btrim(action) <> ''),
    CONSTRAINT ck_audit_events_entity_type CHECK (btrim(entity_type) <> ''),
    CONSTRAINT ck_audit_events_before_data CHECK (jsonb_typeof(before_data) = 'object'),
    CONSTRAINT ck_audit_events_after_data CHECK (jsonb_typeof(after_data) = 'object')
);

CREATE TABLE dogfood.hackathon_registrations (
    hackathon_id uuid NOT NULL,
    user_id uuid NOT NULL,
    participant_role text GENERATED ALWAYS AS ('PARTICIPANT'::text) STORED NOT NULL,
    participation_preference text NOT NULL,
    referral_source text NULL,
    country_snapshot text NOT NULL,
    eligibility_attestations jsonb NOT NULL DEFAULT '{}'::jsonb,
    accepted_rules_version_id uuid NOT NULL,
    accepted_terms_version_id uuid NOT NULL,
    rules_accepted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    terms_accepted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    registered_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_hackathon_registrations PRIMARY KEY (hackathon_id, user_id),
    CONSTRAINT ck_hackathon_registrations_participation_preference CHECK (participation_preference IN ('SOLO', 'LOOKING_FOR_TEAM', 'HAVE_TEAM')),
    CONSTRAINT ck_hackathon_registrations_eligibility_attestations CHECK (jsonb_typeof(eligibility_attestations) = 'object'),
    CONSTRAINT ck_hackathon_registrations_age CHECK (NOT (eligibility_attestations ? 'age_eligibility_confirmed') OR jsonb_typeof(eligibility_attestations->'age_eligibility_confirmed') = 'boolean'),
    CONSTRAINT ck_hackathon_registrations_country_snapshot CHECK (btrim(country_snapshot) <> '')
);

CREATE TABLE dogfood.participant_profiles (
    hackathon_id uuid NOT NULL,
    user_id uuid NOT NULL,
    bio text NULL,
    skills text[] NOT NULL DEFAULT ARRAY[]::text[],
    looking_for_roles text[] NOT NULL DEFAULT ARRAY[]::text[],
    looking_for_team boolean NOT NULL DEFAULT false,
    discovery_opt_in boolean NOT NULL DEFAULT false,
    external_profile_urls jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_participant_profiles PRIMARY KEY (hackathon_id, user_id),
    CONSTRAINT ck_participant_profiles_external_profile_urls CHECK (jsonb_typeof(external_profile_urls) = 'object')
);

CREATE TABLE dogfood.teams (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    created_by_user_id uuid NOT NULL,
    leader_user_id uuid NULL,
    name text NOT NULL,
    roster_locked_at timestamptz NULL,
    dissolved_at timestamptz NULL,
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_teams PRIMARY KEY (id),
    CONSTRAINT ck_teams_leader CHECK ((dissolved_at IS NULL AND leader_user_id IS NOT NULL) OR (dissolved_at IS NOT NULL AND leader_user_id IS NULL)),
    CONSTRAINT uq_teams_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_teams_version CHECK (version >= 1),
    CONSTRAINT ck_teams_name CHECK (btrim(name) <> '')
);

CREATE TABLE dogfood.team_members (
    hackathon_id uuid NOT NULL,
    team_id uuid NOT NULL,
    user_id uuid NOT NULL,
    joined_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_team_members PRIMARY KEY (hackathon_id, user_id),
    CONSTRAINT uq_team_members_team_user UNIQUE (hackathon_id, team_id, user_id)
);

CREATE TABLE dogfood.team_membership_events (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    team_id uuid NOT NULL,
    user_id uuid NOT NULL,
    event_type text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_team_membership_events PRIMARY KEY (id),
    CONSTRAINT ck_team_membership_events_event_type CHECK (event_type IN ('JOINED', 'LEFT'))
);

CREATE TABLE dogfood.team_invites (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    team_id uuid NOT NULL,
    invited_by_user_id uuid NOT NULL,
    token_hash text NOT NULL,
    invite_kind text NOT NULL,
    target_email text NULL,
    max_uses integer NOT NULL,
    use_count integer NOT NULL DEFAULT 0,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_team_invites PRIMARY KEY (id),
    CONSTRAINT ck_team_invites_uses CHECK (max_uses > 0 AND use_count >= 0 AND use_count <= max_uses),
    CONSTRAINT uq_team_invites_token UNIQUE (token_hash),
    CONSTRAINT uq_team_invites_team UNIQUE (id, team_id),
    CONSTRAINT ck_team_invites_invite_kind CHECK (invite_kind IN ('TARGETED', 'SHARE_LINK')),
    CONSTRAINT ck_team_invites_token_hash CHECK (btrim(token_hash) <> ''),
    CONSTRAINT ck_team_invites_kind CHECK ((invite_kind = 'TARGETED' AND target_email IS NOT NULL AND btrim(target_email) <> '' AND max_uses = 1) OR (invite_kind = 'SHARE_LINK' AND target_email IS NULL)),
    CONSTRAINT ck_team_invites_expiry CHECK (expires_at > created_at)
);

CREATE TABLE dogfood.team_invite_redemptions (
    invite_id uuid NOT NULL,
    user_id uuid NOT NULL,
    team_id uuid NOT NULL,
    redeemed_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_team_invite_redemptions PRIMARY KEY (invite_id, user_id)
);

CREATE TABLE dogfood.projects (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    team_id uuid NOT NULL,
    track_id uuid NULL,
    submitted_by_user_id uuid NOT NULL,
    name text NOT NULL,
    tagline text NOT NULL,
    inspiration text NOT NULL,
    what_it_does text NOT NULL,
    how_it_was_built text NOT NULL,
    challenges text NOT NULL,
    accomplishments text NOT NULL,
    what_we_learned text NOT NULL,
    whats_next text NOT NULL,
    submitted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    deleted_at timestamptz NULL,
    deleted_by_user_id uuid NULL,
    disqualified_at timestamptz NULL,
    disqualified_by_user_id uuid NULL,
    disqualification_reason text NULL,
    version integer NOT NULL DEFAULT 1,
    CONSTRAINT pk_projects PRIMARY KEY (id),
    CONSTRAINT uq_projects_team UNIQUE (team_id),
    CONSTRAINT uq_projects_id_team UNIQUE (id, team_id),
    CONSTRAINT uq_projects_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_projects_version CHECK (version >= 1),
    CONSTRAINT ck_projects_name CHECK (btrim(name) <> ''),
    CONSTRAINT ck_projects_tagline CHECK (btrim(tagline) <> ''),
    CONSTRAINT ck_projects_deleted CHECK ((deleted_at IS NULL) = (deleted_by_user_id IS NULL)),
    CONSTRAINT ck_projects_disqualified CHECK ((disqualified_at IS NULL AND disqualified_by_user_id IS NULL AND disqualification_reason IS NULL) OR (disqualified_at IS NOT NULL AND disqualified_by_user_id IS NOT NULL AND disqualification_reason IS NOT NULL AND btrim(disqualification_reason) <> ''))
);

CREATE TABLE dogfood.project_submission_members (
    project_id uuid NOT NULL,
    team_id uuid NOT NULL,
    user_id uuid NOT NULL,
    was_leader boolean NOT NULL,
    captured_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_project_submission_members PRIMARY KEY (project_id, user_id)
);

CREATE TABLE dogfood.project_links (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL,
    link_type text NOT NULL,
    url text NOT NULL,
    label text NULL,
    sort_order integer NOT NULL DEFAULT 0,
    CONSTRAINT pk_project_links PRIMARY KEY (id),
    CONSTRAINT ck_project_links_link_type CHECK (link_type IN ('GITHUB', 'LIVE_DEMO', 'YOUTUBE', 'GOOGLE_DRIVE', 'ONEDRIVE', 'OTHER')),
    CONSTRAINT ck_project_links_https CHECK (url ~ '^https://[^[:space:]]+$')
);

CREATE TABLE dogfood.project_media (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL,
    storage_key text NOT NULL,
    mime_type text NOT NULL,
    size_bytes bigint NOT NULL,
    caption text NULL,
    sort_order integer NOT NULL DEFAULT 0,
    CONSTRAINT pk_project_media PRIMARY KEY (id),
    CONSTRAINT ck_project_media_size CHECK (size_bytes > 0),
    CONSTRAINT ck_project_media_image CHECK (mime_type LIKE 'image/%'),
    CONSTRAINT ck_project_media_storage_key CHECK (btrim(storage_key) <> '')
);

CREATE TABLE dogfood.project_technologies (
    project_id uuid NOT NULL,
    normalized_key text GENERATED ALWAYS AS (lower(btrim(display_name))) STORED NOT NULL,
    display_name text NOT NULL,
    CONSTRAINT pk_project_technologies PRIMARY KEY (project_id, normalized_key),
    CONSTRAINT ck_project_technologies_display_name CHECK (btrim(display_name) <> '')
);

CREATE TABLE dogfood.judge_invites (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    target_email text NOT NULL,
    target_email_key text GENERATED ALWAYS AS (lower(btrim(target_email))) STORED NOT NULL,
    token_hash text NOT NULL,
    invited_by_user_id uuid NOT NULL,
    status text NOT NULL DEFAULT 'PENDING',
    expires_at timestamptz NOT NULL,
    accepted_at timestamptz NULL,
    accepted_by_user_id uuid NULL,
    revoked_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_judge_invites PRIMARY KEY (id),
    CONSTRAINT uq_judge_invites_token UNIQUE (token_hash),
    CONSTRAINT ck_judge_invites_status CHECK (status IN ('PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED')),
    CONSTRAINT ck_judge_invites_target_email CHECK (btrim(target_email) <> ''),
    CONSTRAINT ck_judge_invites_token_hash CHECK (btrim(token_hash) <> ''),
    CONSTRAINT ck_judge_invites_expiry CHECK (expires_at > created_at),
    CONSTRAINT ck_judge_invites_accepted CHECK ((status = 'ACCEPTED' AND accepted_at IS NOT NULL AND accepted_by_user_id IS NOT NULL AND accepted_at < expires_at AND revoked_at IS NULL) OR (status <> 'ACCEPTED' AND accepted_at IS NULL AND accepted_by_user_id IS NULL)),
    CONSTRAINT ck_judge_invites_revoked CHECK ((status = 'REVOKED') = (revoked_at IS NOT NULL))
);

CREATE TABLE dogfood.judge_profiles (
    hackathon_id uuid NOT NULL,
    user_id uuid NOT NULL,
    judge_role text GENERATED ALWAYS AS ('JUDGE'::text) STORED NOT NULL,
    public_name text NOT NULL,
    public_bio text NULL,
    avatar_key text NULL,
    publication_consent boolean NOT NULL DEFAULT false,
    CONSTRAINT pk_judge_profiles PRIMARY KEY (hackathon_id, user_id),
    CONSTRAINT ck_judge_profiles_public_name CHECK (btrim(public_name) <> '')
);

CREATE TABLE dogfood.judge_assignments (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    judge_user_id uuid NOT NULL,
    judge_role text GENERATED ALWAYS AS ('JUDGE'::text) STORED NOT NULL,
    project_id uuid NOT NULL,
    assigned_by_user_id uuid NOT NULL,
    assigned_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    revoked_at timestamptz NULL,
    revoked_by_user_id uuid NULL,
    revocation_reason text NULL,
    CONSTRAINT pk_judge_assignments PRIMARY KEY (id),
    CONSTRAINT uq_judge_assignments_judge_project UNIQUE (judge_user_id, project_id),
    CONSTRAINT uq_judge_assignments_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_judge_assignments_revocation CHECK ((revoked_at IS NULL AND revoked_by_user_id IS NULL AND revocation_reason IS NULL) OR (revoked_at IS NOT NULL AND revoked_by_user_id IS NOT NULL AND revocation_reason IS NOT NULL AND btrim(revocation_reason) <> ''))
);

CREATE TABLE dogfood.judging_criteria (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    name text NOT NULL,
    description text NULL,
    weight_bps integer NOT NULL,
    max_score numeric(12,4) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    CONSTRAINT pk_judging_criteria PRIMARY KEY (id),
    CONSTRAINT ck_judging_criteria_weight CHECK (weight_bps >= 0 AND weight_bps <= 10000),
    CONSTRAINT ck_judging_criteria_max_score CHECK (max_score > 0 AND max_score <> 'NaN'::numeric),
    CONSTRAINT uq_judging_criteria_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_judging_criteria_name CHECK (btrim(name) <> '')
);

CREATE TABLE dogfood.judge_reviews (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    assignment_id uuid NOT NULL,
    status text NOT NULL DEFAULT 'DRAFT',
    comment text NULL,
    submitted_at timestamptz NULL,
    invalidated_at timestamptz NULL,
    invalidated_by_user_id uuid NULL,
    invalidation_reason text NULL,
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_judge_reviews PRIMARY KEY (id),
    CONSTRAINT uq_judge_reviews_assignment UNIQUE (assignment_id),
    CONSTRAINT uq_judge_reviews_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_judge_reviews_version CHECK (version >= 1),
    CONSTRAINT ck_judge_reviews_status CHECK (status IN ('DRAFT', 'SUBMITTED')),
    CONSTRAINT ck_judge_reviews_submitted CHECK ((status = 'SUBMITTED') = (submitted_at IS NOT NULL)),
    CONSTRAINT ck_judge_reviews_invalidated CHECK ((invalidated_at IS NULL AND invalidated_by_user_id IS NULL AND invalidation_reason IS NULL) OR (invalidated_at IS NOT NULL AND invalidated_by_user_id IS NOT NULL AND invalidation_reason IS NOT NULL AND btrim(invalidation_reason) <> ''))
);

CREATE TABLE dogfood.judge_scores (
    hackathon_id uuid NOT NULL,
    review_id uuid NOT NULL,
    criterion_id uuid NOT NULL,
    score numeric(12,4) NOT NULL,
    comment text NULL,
    CONSTRAINT pk_judge_scores PRIMARY KEY (review_id, criterion_id),
    CONSTRAINT ck_judge_scores_score CHECK (score >= 0 AND score <> 'NaN'::numeric)
);

CREATE TABLE dogfood.awards (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    track_id uuid NULL,
    name text NOT NULL,
    description text NULL,
    prize text NULL,
    rank integer NULL,
    selected_project_id uuid NULL,
    selected_by_user_id uuid NULL,
    selected_at timestamptz NULL,
    selection_reason text NULL,
    CONSTRAINT pk_awards PRIMARY KEY (id),
    CONSTRAINT ck_awards_rank CHECK (rank IS NULL OR rank >= 1),
    CONSTRAINT ck_awards_selection CHECK ((selected_project_id IS NULL AND selected_by_user_id IS NULL AND selected_at IS NULL AND selection_reason IS NULL) OR (selected_project_id IS NOT NULL AND selected_by_user_id IS NOT NULL AND selected_at IS NOT NULL)),
    CONSTRAINT uq_awards_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_awards_name CHECK (btrim(name) <> '')
);

CREATE TABLE dogfood.result_publications (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    hackathon_id uuid NOT NULL,
    publication_number integer NOT NULL,
    supersedes_publication_id uuid NULL,
    published_by_user_id uuid NOT NULL,
    published_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    scoring_method text NOT NULL,
    calculation_snapshot jsonb NOT NULL,
    correction_reason text NULL,
    CONSTRAINT pk_result_publications PRIMARY KEY (id),
    CONSTRAINT ck_result_publications_number CHECK (publication_number >= 1),
    CONSTRAINT ck_result_publications_correction CHECK ((publication_number = 1 AND supersedes_publication_id IS NULL AND correction_reason IS NULL) OR (publication_number > 1 AND supersedes_publication_id IS NOT NULL AND supersedes_publication_id <> id AND correction_reason IS NOT NULL AND btrim(correction_reason) <> '')),
    CONSTRAINT uq_result_publications_number UNIQUE (hackathon_id, publication_number),
    CONSTRAINT uq_result_publications_supersedes UNIQUE (supersedes_publication_id),
    CONSTRAINT uq_result_publications_event_id UNIQUE (hackathon_id, id),
    CONSTRAINT ck_result_publications_calculation_snapshot CHECK (jsonb_typeof(calculation_snapshot) = 'object'),
    CONSTRAINT ck_result_publications_scoring_method CHECK (btrim(scoring_method) <> '')
);

CREATE TABLE dogfood.result_entries (
    hackathon_id uuid NOT NULL,
    publication_id uuid NOT NULL,
    project_id uuid NOT NULL,
    final_score numeric(9,6) NOT NULL,
    review_count integer NOT NULL,
    rank integer NOT NULL,
    project_name_snapshot text NOT NULL,
    CONSTRAINT pk_result_entries PRIMARY KEY (publication_id, project_id),
    CONSTRAINT ck_result_entries_score CHECK (final_score >= 0 AND final_score <= 100 AND final_score <> 'NaN'::numeric),
    CONSTRAINT ck_result_entries_review_count CHECK (review_count >= 1),
    CONSTRAINT ck_result_entries_rank CHECK (rank >= 1),
    CONSTRAINT ck_result_entries_project_name_snapshot CHECK (btrim(project_name_snapshot) <> '')
);

CREATE TABLE dogfood.result_awards (
    hackathon_id uuid NOT NULL,
    publication_id uuid NOT NULL,
    award_id uuid NOT NULL,
    project_id uuid NOT NULL,
    award_name_snapshot text NOT NULL,
    prize_snapshot text NULL,
    selected_by_user_id uuid NOT NULL,
    CONSTRAINT pk_result_awards PRIMARY KEY (publication_id, award_id),
    CONSTRAINT ck_result_awards_award_name_snapshot CHECK (btrim(award_name_snapshot) <> '')
);

ALTER TABLE dogfood.platform_terms_versions ADD CONSTRAINT fk_platform_terms_versions_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathons ADD CONSTRAINT fk_hackathons_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathons ADD CONSTRAINT fk_hackathons_organizer_user_id FOREIGN KEY (organizer_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_memberships ADD CONSTRAINT fk_hackathon_memberships_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_memberships ADD CONSTRAINT fk_hackathon_memberships_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_memberships ADD CONSTRAINT fk_hackathon_memberships_status_changed_by_user_id FOREIGN KEY (status_changed_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_rules_versions ADD CONSTRAINT fk_hackathon_rules_versions_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_rules_versions ADD CONSTRAINT fk_hackathon_rules_versions_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_tracks ADD CONSTRAINT fk_hackathon_tracks_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_sponsors ADD CONSTRAINT fk_hackathon_sponsors_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_schedule_items ADD CONSTRAINT fk_hackathon_schedule_items_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.platform_announcements ADD CONSTRAINT fk_platform_announcements_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.platform_announcements ADD CONSTRAINT fk_platform_announcements_edited_by_user_id FOREIGN KEY (edited_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_change_requests ADD CONSTRAINT fk_hackathon_change_requests_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_change_requests ADD CONSTRAINT fk_hackathon_change_requests_requested_by_user_id FOREIGN KEY (requested_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_change_requests ADD CONSTRAINT fk_hackathon_change_requests_expected_owner_user_id FOREIGN KEY (expected_owner_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_change_requests ADD CONSTRAINT fk_hackathon_change_requests_target_owner_user_id FOREIGN KEY (target_owner_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_change_requests ADD CONSTRAINT fk_hackathon_change_requests_reviewed_by_user_id FOREIGN KEY (reviewed_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.audit_events ADD CONSTRAINT fk_audit_events_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.audit_events ADD CONSTRAINT fk_audit_events_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_registrations ADD CONSTRAINT fk_hackathon_registrations_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_registrations ADD CONSTRAINT fk_hackathon_registrations_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.participant_profiles ADD CONSTRAINT fk_participant_profiles_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.participant_profiles ADD CONSTRAINT fk_participant_profiles_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.teams ADD CONSTRAINT fk_teams_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.teams ADD CONSTRAINT fk_teams_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.teams ADD CONSTRAINT fk_teams_leader_user_id FOREIGN KEY (leader_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_members ADD CONSTRAINT fk_team_members_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_members ADD CONSTRAINT fk_team_members_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_membership_events ADD CONSTRAINT fk_team_membership_events_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_membership_events ADD CONSTRAINT fk_team_membership_events_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_invites ADD CONSTRAINT fk_team_invites_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_invites ADD CONSTRAINT fk_team_invites_invited_by_user_id FOREIGN KEY (invited_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_invite_redemptions ADD CONSTRAINT fk_team_invite_redemptions_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.projects ADD CONSTRAINT fk_projects_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.projects ADD CONSTRAINT fk_projects_submitted_by_user_id FOREIGN KEY (submitted_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.projects ADD CONSTRAINT fk_projects_deleted_by_user_id FOREIGN KEY (deleted_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.projects ADD CONSTRAINT fk_projects_disqualified_by_user_id FOREIGN KEY (disqualified_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.project_submission_members ADD CONSTRAINT fk_project_submission_members_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_invites ADD CONSTRAINT fk_judge_invites_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_invites ADD CONSTRAINT fk_judge_invites_invited_by_user_id FOREIGN KEY (invited_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_invites ADD CONSTRAINT fk_judge_invites_accepted_by_user_id FOREIGN KEY (accepted_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_profiles ADD CONSTRAINT fk_judge_profiles_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_profiles ADD CONSTRAINT fk_judge_profiles_user_id FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_assignments ADD CONSTRAINT fk_judge_assignments_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_assignments ADD CONSTRAINT fk_judge_assignments_judge_user_id FOREIGN KEY (judge_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_assignments ADD CONSTRAINT fk_judge_assignments_assigned_by_user_id FOREIGN KEY (assigned_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_assignments ADD CONSTRAINT fk_judge_assignments_revoked_by_user_id FOREIGN KEY (revoked_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judging_criteria ADD CONSTRAINT fk_judging_criteria_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_reviews ADD CONSTRAINT fk_judge_reviews_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_reviews ADD CONSTRAINT fk_judge_reviews_invalidated_by_user_id FOREIGN KEY (invalidated_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_scores ADD CONSTRAINT fk_judge_scores_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.awards ADD CONSTRAINT fk_awards_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.awards ADD CONSTRAINT fk_awards_selected_by_user_id FOREIGN KEY (selected_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_publications ADD CONSTRAINT fk_result_publications_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_publications ADD CONSTRAINT fk_result_publications_published_by_user_id FOREIGN KEY (published_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_entries ADD CONSTRAINT fk_result_entries_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_awards ADD CONSTRAINT fk_result_awards_hackathon_id FOREIGN KEY (hackathon_id) REFERENCES dogfood.hackathons (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_awards ADD CONSTRAINT fk_result_awards_selected_by_user_id FOREIGN KEY (selected_by_user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathons ADD CONSTRAINT fk_hackathons_organizer FOREIGN KEY (id, organizer_user_id, organizer_role, organizer_status) REFERENCES dogfood.hackathon_memberships (hackathon_id, user_id, role, status) ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dogfood.hackathons ADD CONSTRAINT fk_hackathons_rules FOREIGN KEY (id, current_rules_version_id) REFERENCES dogfood.hackathon_rules_versions (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathons ADD CONSTRAINT fk_hackathons_publication FOREIGN KEY (id, current_result_publication_id) REFERENCES dogfood.result_publications (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_registrations ADD CONSTRAINT fk_hackathon_registrations_participant FOREIGN KEY (hackathon_id, user_id, participant_role) REFERENCES dogfood.hackathon_memberships (hackathon_id, user_id, role) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_registrations ADD CONSTRAINT fk_hackathon_registrations_rules FOREIGN KEY (hackathon_id, accepted_rules_version_id) REFERENCES dogfood.hackathon_rules_versions (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.hackathon_registrations ADD CONSTRAINT fk_hackathon_registrations_terms FOREIGN KEY (accepted_terms_version_id) REFERENCES dogfood.platform_terms_versions (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.participant_profiles ADD CONSTRAINT fk_participant_profiles_registration FOREIGN KEY (hackathon_id, user_id) REFERENCES dogfood.hackathon_registrations (hackathon_id, user_id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.teams ADD CONSTRAINT fk_teams_leader FOREIGN KEY (hackathon_id, id, leader_user_id) REFERENCES dogfood.team_members (hackathon_id, team_id, user_id) ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dogfood.team_members ADD CONSTRAINT fk_team_members_registration FOREIGN KEY (hackathon_id, user_id) REFERENCES dogfood.hackathon_registrations (hackathon_id, user_id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_members ADD CONSTRAINT fk_team_members_team FOREIGN KEY (hackathon_id, team_id) REFERENCES dogfood.teams (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_membership_events ADD CONSTRAINT fk_team_membership_events_team FOREIGN KEY (hackathon_id, team_id) REFERENCES dogfood.teams (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_invites ADD CONSTRAINT fk_team_invites_team FOREIGN KEY (hackathon_id, team_id) REFERENCES dogfood.teams (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.projects ADD CONSTRAINT fk_projects_team FOREIGN KEY (hackathon_id, team_id) REFERENCES dogfood.teams (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.team_invite_redemptions ADD CONSTRAINT fk_team_invite_redemptions_invite_team FOREIGN KEY (invite_id, team_id) REFERENCES dogfood.team_invites (id, team_id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.projects ADD CONSTRAINT fk_projects_track FOREIGN KEY (hackathon_id, track_id) REFERENCES dogfood.hackathon_tracks (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.project_submission_members ADD CONSTRAINT fk_project_submission_members_project_team FOREIGN KEY (project_id, team_id) REFERENCES dogfood.projects (id, team_id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.project_links ADD CONSTRAINT fk_project_links_project_id FOREIGN KEY (project_id) REFERENCES dogfood.projects (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.project_media ADD CONSTRAINT fk_project_media_project_id FOREIGN KEY (project_id) REFERENCES dogfood.projects (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.project_technologies ADD CONSTRAINT fk_project_technologies_project_id FOREIGN KEY (project_id) REFERENCES dogfood.projects (id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_profiles ADD CONSTRAINT fk_judge_profiles_judge FOREIGN KEY (hackathon_id, user_id, judge_role) REFERENCES dogfood.hackathon_memberships (hackathon_id, user_id, role) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_assignments ADD CONSTRAINT fk_judge_assignments_judge FOREIGN KEY (hackathon_id, judge_user_id, judge_role) REFERENCES dogfood.hackathon_memberships (hackathon_id, user_id, role) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_assignments ADD CONSTRAINT fk_judge_assignments_project FOREIGN KEY (hackathon_id, project_id) REFERENCES dogfood.projects (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_reviews ADD CONSTRAINT fk_judge_reviews_assignment FOREIGN KEY (hackathon_id, assignment_id) REFERENCES dogfood.judge_assignments (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_scores ADD CONSTRAINT fk_judge_scores_review FOREIGN KEY (hackathon_id, review_id) REFERENCES dogfood.judge_reviews (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.judge_scores ADD CONSTRAINT fk_judge_scores_criterion FOREIGN KEY (hackathon_id, criterion_id) REFERENCES dogfood.judging_criteria (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.awards ADD CONSTRAINT fk_awards_track FOREIGN KEY (hackathon_id, track_id) REFERENCES dogfood.hackathon_tracks (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.awards ADD CONSTRAINT fk_awards_winner FOREIGN KEY (hackathon_id, selected_project_id) REFERENCES dogfood.projects (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_publications ADD CONSTRAINT fk_result_publications_supersedes FOREIGN KEY (hackathon_id, supersedes_publication_id) REFERENCES dogfood.result_publications (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_entries ADD CONSTRAINT fk_result_entries_publication FOREIGN KEY (hackathon_id, publication_id) REFERENCES dogfood.result_publications (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_awards ADD CONSTRAINT fk_result_awards_publication FOREIGN KEY (hackathon_id, publication_id) REFERENCES dogfood.result_publications (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_entries ADD CONSTRAINT fk_result_entries_project FOREIGN KEY (hackathon_id, project_id) REFERENCES dogfood.projects (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_awards ADD CONSTRAINT fk_result_awards_award FOREIGN KEY (hackathon_id, award_id) REFERENCES dogfood.awards (hackathon_id, id) ON DELETE RESTRICT NOT DEFERRABLE;

ALTER TABLE dogfood.result_awards ADD CONSTRAINT fk_result_awards_entry FOREIGN KEY (publication_id, project_id) REFERENCES dogfood.result_entries (publication_id, project_id) ON DELETE RESTRICT NOT DEFERRABLE;

CREATE UNIQUE INDEX ix_hackathon_memberships_organizer ON dogfood.hackathon_memberships (hackathon_id) WHERE role = 'ORGANIZER';

CREATE INDEX ix_hackathon_memberships_event_role ON dogfood.hackathon_memberships (hackathon_id, role);

CREATE INDEX ix_hackathon_memberships_user ON dogfood.hackathon_memberships (user_id);

CREATE INDEX ix_hackathons_lifecycle ON dogfood.hackathons (lifecycle_status);

CREATE INDEX ix_team_members_team ON dogfood.team_members (team_id);

CREATE INDEX ix_team_membership_events_conflict ON dogfood.team_membership_events (team_id, user_id, event_type);

CREATE INDEX ix_team_invites_team ON dogfood.team_invites (team_id);

CREATE INDEX ix_projects_track ON dogfood.projects (track_id);

CREATE UNIQUE INDEX ix_judge_invites_pending ON dogfood.judge_invites (hackathon_id, target_email_key) WHERE status = 'PENDING';

CREATE UNIQUE INDEX ix_hackathon_change_requests_pending ON dogfood.hackathon_change_requests (hackathon_id, request_type) WHERE status = 'PENDING';

CREATE INDEX ix_judge_assignments_judge_event ON dogfood.judge_assignments (judge_user_id, hackathon_id);

CREATE INDEX ix_judge_assignments_project ON dogfood.judge_assignments (project_id);

CREATE INDEX ix_judge_assignments_event_revoked ON dogfood.judge_assignments (hackathon_id, revoked_at);

CREATE INDEX ix_judge_scores_criterion ON dogfood.judge_scores (criterion_id);

CREATE INDEX ix_audit_events_event_time ON dogfood.audit_events (hackathon_id, created_at);

CREATE INDEX ix_audit_events_entity ON dogfood.audit_events (entity_type, entity_id);

CREATE INDEX ix_hackathon_sponsors_event_order ON dogfood.hackathon_sponsors (hackathon_id, sort_order);

CREATE INDEX ix_hackathon_schedule_items_event_order ON dogfood.hackathon_schedule_items (hackathon_id, sort_order);

CREATE INDEX ix_project_links_project_order ON dogfood.project_links (project_id, sort_order);

CREATE INDEX ix_project_media_project_order ON dogfood.project_media (project_id, sort_order);

CREATE UNIQUE INDEX ix_project_submission_members_leader ON dogfood.project_submission_members (project_id) WHERE was_leader;

CREATE FUNCTION dogfood.touch_updated_at() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
BEGIN NEW.updated_at := statement_timestamp(); RETURN NEW; END $$;

CREATE FUNCTION dogfood.reject_history_mutation() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, dogfood AS $$
BEGIN RAISE EXCEPTION 'immutable history: %', TG_TABLE_NAME USING ERRCODE = '23514'; END $$;

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

CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.users FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.users FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','created_at');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.platform_terms_versions FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.hackathons FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathons FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','created_at','created_by_user_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_memberships FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','user_id','joined_at');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.hackathon_rules_versions FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_tracks FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_sponsors FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_schedule_items FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.platform_announcements FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.platform_announcements FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','created_at');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.hackathon_change_requests FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.audit_events FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.hackathon_registrations FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.participant_profiles FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.participant_profiles FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','created_at','user_id');
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.teams FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.teams FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','created_by_user_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.team_members FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','team_id','user_id','joined_at');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.team_membership_events FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.team_invites FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','team_id','invited_by_user_id','token_hash','invite_kind','target_email');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.team_invite_redemptions FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.projects FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.projects FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','team_id','submitted_by_user_id','submitted_at');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.project_submission_members FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.project_links FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','project_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.project_media FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','project_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.project_technologies FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('project_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_invites FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','target_email','invited_by_user_id','token_hash','expires_at');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_profiles FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','user_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_assignments FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','judge_user_id','project_id','assigned_by_user_id','assigned_at');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judging_criteria FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.judge_reviews FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_reviews FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id','created_at','assignment_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.judge_scores FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('hackathon_id','review_id','criterion_id');
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.awards FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','hackathon_id');
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.result_publications FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.result_entries FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_immutable BEFORE UPDATE OR DELETE ON dogfood.result_awards FOR EACH ROW EXECUTE FUNCTION dogfood.reject_history_mutation();
CREATE TRIGGER tr_record_history AFTER INSERT OR DELETE ON dogfood.team_members FOR EACH ROW EXECUTE FUNCTION dogfood.record_membership_event();
CREATE TRIGGER tr_rubric_guard BEFORE INSERT OR UPDATE OR DELETE ON dogfood.judging_criteria FOR EACH ROW EXECUTE FUNCTION dogfood.guard_rubric_mutation();
CREATE TRIGGER tr_state_guard BEFORE UPDATE ON dogfood.hackathons FOR EACH ROW EXECUTE FUNCTION dogfood.guard_hackathon_state();
CREATE TRIGGER tr_score_guard BEFORE INSERT OR UPDATE OR DELETE ON dogfood.judge_scores FOR EACH ROW EXECUTE FUNCTION dogfood.guard_score_write();
CREATE TRIGGER tr_submit_guard BEFORE INSERT OR UPDATE ON dogfood.judge_reviews FOR EACH ROW EXECUTE FUNCTION dogfood.validate_submitted_review();
CREATE TRIGGER tr_accept_guard BEFORE INSERT OR UPDATE ON dogfood.judge_invites FOR EACH ROW EXECUTE FUNCTION dogfood.guard_judge_invite_acceptance();
CREATE TRIGGER tr_chain_guard BEFORE INSERT ON dogfood.result_publications FOR EACH ROW EXECUTE FUNCTION dogfood.guard_publication_chain();
CREATE TRIGGER tr_children_guard BEFORE INSERT ON dogfood.result_entries FOR EACH ROW EXECUTE FUNCTION dogfood.guard_publication_children();
CREATE TRIGGER tr_children_guard BEFORE INSERT ON dogfood.result_awards FOR EACH ROW EXECUTE FUNCTION dogfood.guard_publication_children();

-- Owner-approved T3 extension; the original 33 domain tables are unchanged.
CREATE TABLE dogfood.auth_sessions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    auth_version integer NOT NULL,
    generation bigint NOT NULL DEFAULT 0,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT pk_auth_sessions PRIMARY KEY (id),
    CONSTRAINT fk_auth_sessions_user FOREIGN KEY (user_id) REFERENCES dogfood.users (id) ON DELETE RESTRICT NOT DEFERRABLE,
    CONSTRAINT ck_auth_sessions_auth_version CHECK (auth_version >= 1),
    CONSTRAINT ck_auth_sessions_generation CHECK (generation >= 0),
    CONSTRAINT ck_auth_sessions_expiry CHECK (expires_at > created_at)
);
CREATE INDEX ix_auth_sessions_user ON dogfood.auth_sessions (user_id);
CREATE TRIGGER tr_touch_updated_at BEFORE UPDATE ON dogfood.auth_sessions FOR EACH ROW EXECUTE FUNCTION dogfood.touch_updated_at();
CREATE TRIGGER tr_identity BEFORE UPDATE ON dogfood.auth_sessions FOR EACH ROW EXECUTE FUNCTION dogfood.guard_identity('id','user_id','auth_version','expires_at','created_at');

COMMIT;
