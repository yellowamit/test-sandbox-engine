# Ephemeral Test Sandbox & Automated Verification Engine

An automated, reproducible test orchestration harness built around a transactional Order & Wallet Inventory microservice (`FastAPI` + `PostgreSQL 16`). Designed to demonstrate engineering best practices in **Test Data & Environment Setup**, **Automated Database Pre-Flight Checks**, and **Test Execution & Prescribed Result Analysis**.

---

## Key Capabilities

### 1. Test Data & Environment Setup
- **Isolated Containerized Sandbox (`docker-compose.yml`)**: Spins up an ephemeral PostgreSQL 16 instance with automated `pg_isready` health checks on host port `5433`.
- **Automated Pre-Flight Database Checks (`scripts/preflight_check.py`)**: Executes diagnostic checks prior to test runs to verify:
  - Database connection health and ping latency.
  - Schema existence (`users`, `products`, `orders`, `order_items`).
  - Referential integrity and foreign-key constraints.
  - ACID check-constraint enforcement (`chk_user_wallet_non_negative`, `chk_product_stock_non_negative`) using non-destructive SQL `SAVEPOINT` rollbacks.
- **Deterministic Data Seeding (`scripts/seed_data.py`)**: Prepares initial test data using a fixed synthetic seed (`Faker.seed(42)`) to guarantee reproducible test states across runs:
  - `alice_funded` (Wallet: `5000.00`), `bob_broke` (Wallet: `0.00`), `carol_exact` (Wallet: `99.99`), `dave_concurrency` (Wallet: `1000.00`).
  - Boundary inventory SKUs including in-stock items, single-unit stock (`stock_quantity=1`), and depleted items (`stock_quantity=0`).

### 2. Test Execution & Result Analysis
- **Unit Testing (`tests/unit/test_pricing_unit.py`)**: Validates Pydantic v2 request schemas, strictly positive quantity constraints, non-empty checkout payloads, and `Decimal` pricing precision without external I/O.
- **Database-State Integration Testing (`tests/integration/test_orders_db_state.py`)**: Verifies API responses alongside direct SQLAlchemy database state assertions, ensuring `SELECT ... FOR UPDATE` row-level locking and full transactional rollbacks on insufficient stock or wallet funds.
- **Prescribed Outcome Documentation (`tests/conftest.py`)**: Custom Pytest reporting hooks (`pytest_runtest_makereport` & `pytest_sessionfinish`) capture requirement IDs (`@pytest.mark.req_id`), execution latency, and error traces to automatically generate standardized reports in `reports/test_execution_matrix.md` and `reports/test_execution_matrix.json`.

---

## Project Structure

```text
test-sandbox-engine/
├── .github/workflows/test-ci.yml   # Automated GitHub Actions CI pipeline
├── app/
│   ├── config.py                   # Environment & DB connection settings
│   ├── database.py                 # SQLAlchemy 2.0 engine & session management
│   ├── models.py                   # Relational schema & DB check constraints
│   ├── schemas.py                  # Pydantic v2 validation models
│   └── main.py                     # FastAPI transactional checkout endpoints
├── scripts/
│   ├── preflight_check.py          # Automated database health & constraint checker
│   └── seed_data.py                # Deterministic initial test data generator
├── tests/
│   ├── conftest.py                 # Fixtures & custom prescribed report generator
│   ├── unit/
│   │   └── test_pricing_unit.py    # Isolated unit test suite
│   └── integration/
│       └── test_orders_db_state.py # Database-backed integration test suite
├── reports/                        # Auto-generated Markdown & JSON test matrices
├── AGENTS.md                       # Context instructions for AI coding assistants
├── docker-compose.yml              # PostgreSQL 16 sandbox & API containers
├── Dockerfile                      # Production/test container build definition
├── pytest.ini                      # Pytest path & custom marker configuration
└── requirements.txt                # Python dependencies (Psycopg 3 binary wheels)
```

---

## Quick Start Guide

### 1. Clone & Set Up Virtual Environment
```powershell
git clone [https://github.com/yellowamit/test-sandbox-engine.git](https://github.com/yellowamit/test-sandbox-engine.git)
cd test-sandbox-engine

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS / Git Bash:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start the Isolated PostgreSQL Sandbox
```powershell
docker compose up -d sandbox_db
```

### 3. Run Database Pre-Flight Checks & Seed Initial Test Data
```powershell
python scripts/preflight_check.py
python scripts/seed_data.py
```

**Expected Pre-Flight Output:**
```text
[PRE-FLIGHT] ================== STARTING PRE-FLIGHT DATABASE CHECKS ==================
  [PASS] Database Connectivity OK (Latency: 1.85ms)
  [PASS] Required Tables Present: ['order_items', 'orders', 'products', 'users']
  [PASS] Foreign Key Integrity Confirmed on 'orders' -> {'users'}
  [PASS] Foreign Key Integrity Confirmed on 'order_items' -> {'orders', 'products'}
  [PASS] Invariant Verified: Negative wallet balances strictly blocked by DB constraint.
[PRE-FLIGHT] ================= PRE-FLIGHT SUMMARY: PASSED (18.4ms) ================
```

### 4. Execute Test Suite & Generate Prescribed Reports
```powershell
pytest -v
```

---

## Sample Generated Report (`reports/test_execution_matrix.md`)

Every run of `pytest` automatically updates `reports/test_execution_matrix.md` and `reports/test_execution_matrix.json`:

| Req ID | Module | Test Case | Status | Duration (ms) |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-INT-01` | `tests/integration/test_orders_db_state.py` | `test_successful_checkout_atomic_db_mutation` | PASSED | 42.15 |
| `REQ-INT-02` | `tests/integration/test_orders_db_state.py` | `test_rejection_on_zero_inventory_no_db_mutation` | PASSED | 14.80 |
| `REQ-INT-03` | `tests/integration/test_orders_db_state.py` | `test_rejection_on_insufficient_wallet_balance` | PASSED | 12.34 |
| `REQ-UNIT-01` | `tests/unit/test_pricing_unit.py` | `test_order_item_strictly_positive_quantity` | PASSED | 1.12 |
| `REQ-UNIT-02` | `tests/unit/test_pricing_unit.py` | `test_checkout_payload_empty_items_rejected` | PASSED | 0.85 |
| `REQ-UNIT-03` | `tests/unit/test_pricing_unit.py` | `test_pricing_calculation_precision` | PASSED | 0.45 |