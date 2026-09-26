---
name: dogfood-authorization
description: Implement or audit DogFood authorization, permissions, role checks, ownership checks, judge anonymity, IDOR protection, and deadline-based access. Use whenever an endpoint or UI action depends on who the user is allowed to access or modify.
---

# DogFood Authorization

Read `docs/dogfood-domain.md` before changing permissions.

Use strict least privilege.

Authorization is:

RBAC
+
resource ownership
+
hackathon scope
+
assignment checks
+
deadline/state checks

## Default

DENY unless explicitly allowed.

Never treat frontend visibility as security.

## Guest

May view public hackathon information:

- overview
- schedule
- rules
- sponsors
- tracks
- public announcements

May view projects only after results are published and according to
`result_gallery_mode`.

## Participant

May:

- register
- join a permitted team
- view own team
- view own submission

Normal team members cannot edit project submission.

## Team Leader

May manage own team according to hackathon/team state.

Before submission/deadline where permitted:

- invite members
- remove members
- edit team
- submit project
- edit project
- delete project

Never allow Team Leader to modify another team's resources.

## Judge

Judge authorization is intentionally narrow.

A Judge may:

- list assigned projects
- read assigned project judging view
- create/update own review before judging closes

Judge must never receive:

- team name
- participant identity
- emails
- usernames
- profile data
- other judge scores
- live average
- current ranking

Use a dedicated Judge response schema/DTO.

Do not serialize a full Project/Team model and merely hide fields in CSS.

For every judged-project access verify:

- current user is JUDGE
- same hackathon
- active assignment exists
- judging state allows action

Prevent IDOR by testing direct project-ID manipulation.

## Hackathon Admin

May:

- view submissions
- view participants
- manage participants
- ban participant at hackathon scope
- invite/remove judges
- assign judges
- see judging progress/rankings
- select/propose winners

Must not:

- modify contestant project content
- modify core hackathon settings
- publish final results

## Organizer

May manage hackathon settings and admins.

May configure:

- dates
- team limits
- tracks
- judging criteria
- judges
- visibility

May select winners and publish results.

If Organizer overrides contestant project content:
- require reason
- write audit log

## DogFood Super Admin

Platform scope.

Owns:

- global moderation
- platform announcements
- deletion approval
- ownership-transfer approval

## Deadline Rules

Server must enforce:

- registration window
- submission deadline
- judging window
- result publication state

Never trust a disabled button as deadline enforcement.

## Security Tests

For protected functionality test:

1. unauthenticated
2. wrong role
3. correct role wrong hackathon
4. correct role wrong resource
5. correct role correct resource
6. deadline closed
7. direct ID manipulation
8. judge response does not leak identities

Prefer 404 rather than leaking resource existence where appropriate.
Use 403 when resource existence is already legitimately known.
