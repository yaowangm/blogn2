# Code Quality Future Work

Items found during the behavior-preserving quality pass that should be handled separately because they may affect behavior, performance characteristics, presentation, or database structure.

## Search SQL Parameterization

- `src/services/search_service.py` builds several semantic-search SQL statements with string interpolation for vectors, thresholds, limits, and offsets.
- Current inputs appear to be internally derived or numerically constrained in normal routes, but the pattern is brittle and makes future edits easier to get wrong.
- Future work: convert these queries to bound SQLAlchemy parameters and add regression tests for ranking/order, pagination, fallback search, and invalid-vector handling.

## Test Database Lifecycle

- `pytest` provisions a temporary PostgreSQL database by default via `tests/db_lifecycle.py`.
- This is correct for integration isolation, but it means ordinary unit-test commands can create/drop schema unless `BLOGN_SKIP_TEST_DB_LIFECYCLE=1` is set.
- Future work: split pure unit/static tests from integration DB lifecycle, or make DB lifecycle opt-in for tests that actually require PostgreSQL.
