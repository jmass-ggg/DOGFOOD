---
name: dogfood-feature-delivery
description: Implement or finish a DogFood hackathon-platform feature end-to-end with minimal scope, correct integration, and working validation. Use for feature requests, bug fixes that span layers, unfinished flows, or requests to complete a DogFood milestone.
---

# DogFood Feature Delivery

Use `docs/dogfood-domain.md` when the task touches product rules,
permissions, submissions, teams, judging, or results.

## Goal

Ship the requested vertical slice completely.

Do not maximize file count or architecture complexity.

Optimize for:

1. correctness
2. completion
3. judge-visible product quality
4. maintainability
5. development speed

## Workflow

1. Inspect only the relevant repository areas.
2. Determine the existing stack and conventions.
3. Define concrete acceptance criteria from the request.
4. Identify affected:
   - database
   - backend
   - authorization
   - frontend
   - tests
5. Implement the smallest complete vertical slice.
6. Reuse existing abstractions before creating new ones.
7. Add schema migrations when persistence changes.
8. Enforce business/security rules server-side.
9. Implement loading, empty, success, and error states in UI where relevant.
10. Run the relevant validation commands.
11. Fix failures caused by the change.
12. Report exactly what changed and anything still blocked.

## Scope Discipline

Prioritize:

- auth
- hackathon registration
- team management
- project submission
- deadline enforcement
- judging
- results
- organizer/admin workflows
- polished primary UX

Avoid unless specifically required:

- microservices
- Kafka
- Elasticsearch
- complex event sourcing
- premature Redis use
- public voting
- chat
- unnecessary notifications
- speculative abstractions

## Completion Rule

Do not stop at:

- database only
- endpoint only
- UI mockup only

when the request clearly requires a working user flow.

A feature is done when the relevant path works from user action through
persistence and back to visible UI/state.
