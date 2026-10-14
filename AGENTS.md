# AGENTS.md — Developer & LLM Context File

## 1. Project Overview
This repository implements the **Ephemeral Test Sandbox & Automated Verification Engine**.
It automates:
1. Isolated environment setup and database schema/invariant pre-flight checks.
2. Deterministic data seeding with edge-case profiles (Faker fixed seed: 42).
3. Unit and database-level integration testing with strict ACID boundary assertions.
4. Prescribed test execution reporting via custom Pytest hooks into Markdown and JSON matrices.

## 2. Architecture & Tech Stack
- **Language**: Python 3.11+
- **API Framework**: FastAPI, Pydantic v2
- **Persistence**: PostgreSQL 16, SQLAlchemy 2.0 ORM
- **Testing Engine**: Pytest, Pytest-Cov, HTTPX (TestClient)
- **Containerization**: Docker Compose with pg_isready health checks

## 3. Directory Conventions
- `app/`: Production application code (models, schemas, database connection, business endpoints).
- `scripts/`: Operational tools for environment diagnostics and seeding:
  - `preflight_check.py`: Schema inspection, FK confirmation, check-constraint validation.
  - `seed_data.py`: Deterministic seed data creation.
- `tests/`:
  - `unit/`: Fast, isolated tests without network/DB calls.
  - `integration/`: API + DB tests asserting transactional side-effects.
  - `conftest.py`: Test fixtures and reporting hooks.
- `reports/`: Target directory for `test_execution_matrix.json` and `.md`.

## 4. Key Engineering Invariants
- **Database Non-Negative Constraints**: Users cannot have negative balances; products cannot have negative stock or price.
- **Row Locking**: Endpoints modifying inventory and balances MUST acquire row-level locks using `.with_for_update()`.
- **Requirement Tagging**: Every test must include a `@pytest.mark.req_id("REQ-XYZ")` decorator so the reporter logs it correctly.
- **No Mocking in Integration Tests**: Integration tests MUST run against the real PostgreSQL container to verify database state.

## 5. Development Commands
- Start Sandbox DB:
  `docker compose up -d sandbox_db`
- Run Pre-Flight DB Checks:
  `python scripts/preflight_check.py`
- Seed Test Data:
  `python scripts/seed_data.py`
- Run Complete Test Suite & Generate Reports:
  `pytest -v`
- Inspect Test Reports:
  `cat reports/test_execution_matrix.md`
