<!-- DOGFOOD_CODEX_START -->

# DogFood Hackathon Platform

This repository implements the DogFood hackathon platform.

Canonical product/domain rules live in:

`docs/dogfood-domain.md`

Read that document when the task changes:

- authorization
- hackathon roles
- teams
- submissions
- judging
- rankings
- results
- publication/privacy

Do not read unrelated documents automatically for tiny changes.

## Engineering Defaults

Preserve the repository's existing stack and conventions.

If backend architecture has not yet been chosen, prefer:

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Pydantic
- pytest

Do not mix Django and FastAPI without a concrete existing requirement.

Do not introduce infrastructure such as Redis, queues, microservices,
Elasticsearch, or event streaming unless the requested feature needs it.

## Working Style

For implementation tasks:

1. inspect the relevant existing code
2. preserve working architecture
3. implement the smallest complete vertical slice
4. enforce authorization/business rules server-side
5. add migrations when schema changes
6. add/update targeted tests
7. run relevant validation
8. fix failures caused by the change
9. do not claim unexecuted checks passed

Prefer completing a feature end-to-end over producing broad scaffolding.

## Product Priorities

Highest priority:

- reliable registration
- team flows
- smooth project submission
- privacy
- strong judging workspace
- configurable rubrics
- organizer/admin operations
- results
- polished UX

A small reliable feature set is preferable to unfinished stretch features.

## Security

Default deny.

Prevent:

- cross-hackathon access
- cross-team modification
- judge IDOR
- hidden participant identity leaks
- post-deadline mutation
- unauthorized result publication

Never use frontend-only permission checks as the security boundary.

## Codex Skills

Project-specific skills are available in `.codex/skills/`.

Use the most relevant skill for the task rather than loading every skill.

<!-- DOGFOOD_CODEX_END -->
