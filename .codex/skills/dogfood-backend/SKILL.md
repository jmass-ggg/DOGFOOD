---
name: dogfood-backend
description: Build or modify the DogFood backend APIs, services, validation, persistence, and error handling. Use for FastAPI, SQLAlchemy, Alembic, PostgreSQL, authentication, REST endpoints, service-layer logic, and backend integrations.
---

# DogFood Backend Engineering

Inspect the existing backend before making architectural changes.

If there is no established backend stack, prefer:

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2
- PostgreSQL
- Alembic
- pytest

Do not introduce Django alongside FastAPI unless the repository already
requires both.

Do not add Redis merely because it may be useful later.

## Architecture

Prefer a clear structure equivalent to:

app/
- api/
- models/
- schemas/
- services/
- repositories/ when useful
- auth/
- core/
- db/
- tests/

Avoid unnecessary layer ceremony for trivial CRUD.

Keep business rules out of route handlers when they are non-trivial.

## Endpoint Workflow

For a mutation:

1. authenticate
2. resolve hackathon scope
3. authorize
4. validate business state
5. validate deadline/state
6. perform transaction
7. return intentionally shaped response

## Schemas

Use different schemas for different trust boundaries.

Examples:

- ProjectCreate
- ProjectUpdate
- ParticipantProjectRead
- AdminProjectRead
- JudgeProjectRead

`JudgeProjectRead` must never include participant/team identity fields.

## Error Semantics

Use consistent HTTP status codes.

Typical:

- 400 invalid business request
- 401 unauthenticated
- 403 authenticated but prohibited
- 404 absent or intentionally concealed resource
- 409 state/uniqueness conflict
- 422 request validation failure

Return stable machine-readable error codes when useful.

## Transactions

Use transactions for flows such as:

- accepting team invite
- joining/leaving team
- submitting project
- assigning judge
- submitting judge review
- confirming results

Check constraints again inside the transaction where races are possible.

## API Areas

Expected domains may include:

- auth
- hackathons
- registrations
- teams
- invitations
- tracks
- projects
- project media/links
- organizers/admin
- judges
- judging criteria
- reviews/scores
- results/awards
- change requests

Do not expose internal models directly.

## Security

Never:

- trust user-supplied role
- trust user-supplied hackathon_id without authorization
- let judge endpoints return team identity
- let admin modify project contents
- let closed submissions mutate without authorized override
- interpolate SQL manually where ORM/parameters should be used

## Completion

After implementation run relevant:

- migration checks
- backend tests
- lint/type checks if configured

Fix failures introduced by the change.
