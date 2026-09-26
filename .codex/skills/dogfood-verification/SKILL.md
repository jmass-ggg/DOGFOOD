---
name: dogfood-verification
description: Verify DogFood changes before calling them complete. Use for acceptance testing, regression testing, authorization testing, API validation, frontend build checks, migration verification, and pre-demo readiness.
---

# DogFood Verification

Verify the requested change proportionally.

Do not run unrelated expensive suites without reason.

Never report a test as passing unless it actually ran successfully.

## Critical Acceptance Paths

Prioritize:

1. user can view hackathon
2. eligible user can register
3. team/solo constraints work
4. Team Leader can manage team
5. Team Leader can submit exactly one project
6. normal member cannot edit project
7. deadline locks project
8. Admin can inspect but not edit project
9. Judge sees only assigned project
10. Judge response contains no identity leaks
11. Judge can score using configured rubric
12. Judge cannot see other scores/ranking
13. scoring locks at deadline
14. system calculates ranking
15. Admin/Organizer can select winner
16. only Organizer publishes
17. public cannot see submissions before publication
18. post-results visibility honors WINNERS_ONLY/ALL_PROJECTS

## Authorization Matrix Testing

For each sensitive endpoint test:

- unauthenticated user
- wrong role
- wrong hackathon
- wrong resource owner
- correct authorized user
- closed deadline/state
- modified resource ID

This specifically guards against IDOR.

## Backend

Use repository-defined commands.

Typical examples when applicable:

pytest -q

Run migration upgrade against a disposable/local database where configured.

## Frontend

Use repository-defined commands.

Typical:

npm run lint
npm run test
npm run build

Do not invent a command if package.json does not define it.

## Manual/Browser Checks

When browser tooling is available, check the changed critical flow.

Look for:

- broken navigation
- failed network requests
- incorrect role actions
- loading/error problems
- layout overflow
- stale UI after mutation

## Done Report

When completing work report:

- what was implemented
- migrations added
- tests/checks executed
- pass/fail result
- any unresolved limitation

Do not describe unexecuted verification as completed.
