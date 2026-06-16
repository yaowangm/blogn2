# Code Quality Future Work

Items found during the behavior-preserving quality pass that should be handled separately because they may affect behavior, performance characteristics, presentation, or database structure.

## Test Database Lifecycle

- `pytest` provisions a temporary PostgreSQL database by default via `tests/db_lifecycle.py`.
- This is correct for integration isolation, but it means ordinary unit-test commands can create/drop schema unless `BLOGN_SKIP_TEST_DB_LIFECYCLE=1` is set.
- Future work: split pure unit/static tests from integration DB lifecycle, or make DB lifecycle opt-in for tests that actually require PostgreSQL.
