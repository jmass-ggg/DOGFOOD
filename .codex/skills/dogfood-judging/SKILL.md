---
name: dogfood-judging
description: Implement or review DogFood judging workflows including judge invitations, anonymous assignments, rubrics, scores, judging progress, ranking calculation, awards, winner confirmation, and result publication.
---

# DogFood Judging Workflow

Read `docs/dogfood-domain.md`.

Judging integrity is more important than feature quantity.

## Flow

Organizer/Admin
→ invite judges
→ configure criteria
→ assign projects
→ judging opens
→ judges review assigned projects
→ judges submit scores
→ judging closes
→ system calculates ranking
→ Admin/Organizer reviews
→ winner selected
→ Organizer publishes
→ public gallery opens according to visibility

## Blind Judging

Judge API and UI must not expose:

- team name
- participant identities
- user account information
- other judge scores
- live averages
- ranking

Participant count may be shown.

## Assignment

Never authorize judging based on role alone.

Require explicit assignment to the requested project.

## Rubrics

Criterion fields should support equivalents of:

- name
- description
- weight
- max_score
- display order

Validate score bounds.

Validate configured weights.

Prefer freezing criteria when judging begins.

## Reviews

One judge should have at most one review per project.

Each review contains one score per configured criterion.

Judge may update their own review until judging closes.

After closing:
- immutable to judge

Exceptional organizer/system corrections should be audited.

## Ranking

Calculate from completed valid reviews.

Weighted criterion contribution:

(score / max_score) * weight

Then aggregate judge review totals according to the configured ranking
strategy.

Do not let public likes affect judging score.

Do not automatically publish the highest calculated project as winner.

Ranking assists human winner confirmation.

## Winner State

Keep separate concepts:

- calculated_rank
- award/winner selection
- result publication

Admin or Organizer may select winners.

Only Organizer publishes final results under current rules.

## Test Cases

Always cover:

- judge cannot open unassigned project
- judge cannot see identities
- judge cannot see other scores
- out-of-range scores rejected
- duplicate criterion score prevented
- score editable before close
- score locked after close
- ranking updates from valid reviews
- unpublished results stay private
