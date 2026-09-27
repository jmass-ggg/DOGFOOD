# DogFood Backend API

Backend foundation for the DogFood hackathon platform, built with FastAPI and PostgreSQL.

## Prerequisites

- Python 3.12 or higher
- PostgreSQL 14 or higher
- pip or uv package manager

## Setup Instructions

### 1. Install Dependencies

Using pip:
```bash
cd backend
pip install -e ".[dev]"
```

Using uv (recommended):
```bash
cd backend
uv pip install -e ".[dev]"
```

### 2. Configure Environment

Copy the example environment file and update with your values:
```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL`: Your `postgresql+psycopg://` connection string. Replace any older `postgresql+asyncpg://` value.
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### 3. Set Up PostgreSQL

Create a PostgreSQL database:
```bash
createdb dogfood
```

Or using psql:
```sql
CREATE DATABASE dogfood;
```

### 4. Run Database Migrations

Run the available Alembic migrations:
```bash
alembic upgrade head
```

### 5. Start the Application

Run the FastAPI application using uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

### 6. Verify Installation

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "dogfood-api",
  "database": "connected"
}
```

## Running Tests

### Test Database Setup

Database tests require a dedicated database named `testdb`. Set it up once before running tests:

```bash
sudo -u postgres ./setup_test_db.sh
```

This creates:
- Test database: `testdb`
- Test user: `test` (password: `test`)
- Connection string: `postgresql+psycopg://test:test@localhost:5432/testdb`

Tests ignore your application `DATABASE_URL` and use `TEST_DATABASE_URL` when set. The URL must use the psycopg driver and a database named `testdb`.

### Running Tests

Execute all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_health.py
```

Run property-based tests only:
```bash
pytest -k "property"
```

## Docker Support

Build the Docker image:
```bash
docker build -t dogfood-api .
```

Run the container:
```bash
docker run -p 8000:8000 --env-file .env dogfood-api
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application factory
│   ├── config.py            # Configuration management
│   └── core/
│       ├── database.py      # Database connectivity
│       ├── errors.py        # Error handling
│       ├── logging.py       # Logging infrastructure
│       ├── request_id.py    # Request tracking
│       └── clock.py         # Time management
├── tests/
│   ├── conftest.py          # Shared test fixtures
│   └── test_*.py            # Test files
├── migrations/              # Alembic migrations
├── pyproject.toml           # Project dependencies
├── alembic.ini              # Alembic configuration
├── Dockerfile               # Container build definition
└── .env.example             # Example configuration
```

## Development

- Follow the existing code structure and patterns
- Add tests for new functionality
- Run tests before committing
- Use type hints for all function signatures
- Keep database migrations reversible

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## Troubleshooting

### Database Connection Issues

If you see database connection errors:
1. Verify PostgreSQL is running: `pg_isready`
2. Check your `DATABASE_URL` in `.env`
3. Ensure the database exists: `psql -l`
4. Verify connection permissions

### Migration Issues

If Alembic migrations fail:
1. Check database connectivity
2. Verify `alembic.ini` configuration
3. Review migration files in `migrations/versions/`

### Import Errors

If you encounter import errors:
1. Ensure you installed the package in editable mode: `pip install -e ".[dev]"`
2. Verify you're in the correct directory
3. Check your Python version: `python --version`

## Contributing

1. Create a feature branch
2. Implement changes with tests
3. Run the test suite
4. Submit a pull request

## License

Internal project for DogFood hackathon platform.

## T2 persistence

The 33 typed model mappings live in the domain `models.py` files. Import
`app.models` to register every table; the shared `DeclarativeBase` lives in
`app/core/model_base.py`. All tables explicitly use the `dogfood` schema.
Bounded vocabularies remain `TEXT` plus named checks, not native enums.

`0001_dogfood_v1` installs the frozen schema using explicit Alembic operations
and versioned PostgreSQL function/trigger DDL. It does not load the reference
SQL or import live application models. Use migrations for database setup;
`Base.metadata.create_all()` does not install the 11 functions/49 triggers.
The development downgrade removes the revision's objects and their data; use
it only on disposable databases. It does not use `DROP SCHEMA ... CASCADE`.

From `backend/`, with a dedicated database URL in `DATABASE_URL`:

```bash
python -m alembic heads
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

Autogenerate inspects only `dogfood` and compares server defaults. It cannot
prove function/trigger or CHECK-constraint parity; the catalog tests below
cover those separately. The two deferred ownership/leadership FKs retain
their frozen semantics. `use_alter` on cyclic metadata references controls
DDL ordering only, not constraint deferrability.

### PostgreSQL integration tests

Use PostgreSQL 16+ and separate disposable databases. T1 retains its existing
`TEST_DATABASE_URL` contract (database name `testdb`). T2 uses a separate
`T2_DATABASE_URL` with database name prefixed `dogfood_t2_`; its fixture applies
the migration to an empty database or checks an existing T2 revision. Tests
roll back their fixtures, including commits inside ORM sessions. No database
is dropped or reset by the test suite.

1. Create an empty reference database, a separate empty `dogfood_t2_*`
   migration database, and an empty `dogfood_t2_*` metadata-test database
   with PostgreSQL tooling.
2. From the repository root run the unchanged frozen verifier:
   `SCHEMA_TEST_DATABASE_URL='postgresql://…/reference' python verify_schema.py`.
3. From `backend/` run:

```bash
T2_DATABASE_URL='postgresql+psycopg://…/dogfood_t2_tests' \
T2_REFERENCE_DATABASE_URL='postgresql+psycopg://…/reference' \
T2_METADATA_DATABASE_URL='postgresql+psycopg://…/dogfood_t2_metadata' \
python -m pytest tests/persistence
```

Without `T2_DATABASE_URL`, PostgreSQL persistence tests are explicitly skipped.
Without the reference URL, catalog parity tests are skipped. Without the
metadata URL, metadata parity is skipped. A verification run must set all three
and report zero skipped tests. Metadata DDL runs in a rolled-back transaction
and leaves its dedicated database empty. Catalog comparison covers
columns, defaults, generated expressions, exact constraints, indexes, partial
predicates, function definitions, trigger definitions and native enums.

Persistence tests do not establish API authorization, privacy projections,
business transaction correctness, concurrent race behavior or production
readiness. Project child relationships are explicit read-only navigation with
`lazy="raise"`; load them explicitly (for example with `selectinload`) and make
writes via the mapped child entities. No cascade or workflow is implied.
