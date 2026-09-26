---
name: dogfood-database
description: Design, migrate, review, or optimize DogFood PostgreSQL data models and SQLAlchemy persistence. Use for schemas, tables, constraints, relationships, migrations, indexes, query design, and database correctness.
---

# DogFood Database Engineering

Read `docs/dogfood-domain.md` for domain invariants relevant to the task.

Prefer PostgreSQL.

If the backend already uses another supported persistence style, preserve the
existing architecture unless migration is explicitly requested.

## Core Modeling Principles

- Normalize important entities.
- Use UUID primary keys if that is already the project convention.
- Use timestamptz-compatible timestamps.
- Use explicit foreign keys.
- Add database constraints for invariants that must never be violated.
- Do not rely only on frontend validation.
- Avoid storing values that can be safely derived unless caching is justified.
- Use transactions for multi-table state transitions.

## Recommended Core Model

Typical entities:

- users
- hackathons
- hackathon_memberships
- hackathon_registrations
- sponsors
- hackathon_sponsors
- participant_profiles
- teams
- team_members
- team_invites
- team_join_requests
- hackathon_tracks
- projects
- project_links
- project_media
- project_technologies
- judge_invites
- judge_assignments
- judging_criteria
- judge_reviews
- judge_scores
- awards
- announcements
- hackathon_change_requests
- audit_logs

Do not blindly create tables that already exist under equivalent names.

## Role Model

Roles are not combinable in the same hackathon.

Prefer one hackathon-scoped role on membership:

- PARTICIPANT
- JUDGE
- HACKATHON_ADMIN
- ORGANIZER

TEAM_LEADER belongs to `team_members.member_role`, not the global/hackathon
role system.

DOGFOOD_SUPER_ADMIN is platform-scoped.

## Critical Constraints

Enforce equivalents of:

- unique user membership per hackathon
- one team membership per user per hackathon
- one project per team per hackathon
- one judge review per judge/project
- one criterion score per review/criterion
- unique technology per project when appropriate
- unique like per project/user if likes exist

Validate team min/max limits transactionally.

## Submission Modeling

A solo participant should still be represented by a one-person team.

Project should reference team and hackathon.

Use:

project_links:
- project_id
- link_type
- url
- label

instead of provider-specific columns for every possible URL.

## Judging

Keep:

judge_reviews
- judge
- project
- state
- comments
- timestamps

judge_scores
- review
- criterion
- score
- comment

Calculate weighted totals from criterion scores.

Do not treat a duplicated `total_score` column as authoritative.

## Indexing

Add indexes based on access patterns, especially:

- memberships by hackathon/user
- teams by hackathon
- projects by hackathon/team
- judge assignments by judge/project
- judge reviews by project/judge
- scores by review
- announcements by hackathon/published time

Do not add speculative indexes without query benefit.

## Migrations

For every schema change:

1. create migration
2. inspect generated SQL/migration
3. verify upgrade
4. verify downgrade when practical
5. check existing data compatibility

Never silently reset or drop developer data unless explicitly requested.
