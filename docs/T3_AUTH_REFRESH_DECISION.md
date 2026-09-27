# T3 refresh/session owner decision — approved and implemented

The owner approved exactly one table, dogfood.auth_sessions, and additive
migration 0002_auth_sessions. The chosen design uses signed, purpose-bound
refresh JWTs with a persisted generation, absolute expiry and revocation state.
No credential material or token history is stored. PostgreSQL row locks serialize
rotation, and reuse revokes the session (including any newly rotated credential).

See the authoritative T3 appendix in [DATABASE_SCHEMA_SPEC.md](DATABASE_SCHEMA_SPEC.md)
for the complete physical definition and transaction/replay contract.

Logout is now current-session only; logout-all retains global auth_version
invalidation. Strict replay policy deliberately requires re-login if a client
retries a consumed refresh credential after losing the previous response.
