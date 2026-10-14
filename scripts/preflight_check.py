import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine, Base
from app.models import User, Product, Order, OrderItem

def run_preflight_checks() -> bool:
    print("\n[PRE-FLIGHT] ================== STARTING PRE-FLIGHT DATABASE CHECKS ==================")
    start_time = time.time()
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    all_passed = True

    try:
        with engine.connect() as conn:
            ping_start = time.time()
            conn.execute(text("SELECT 1;"))
            latency_ms = (time.time() - ping_start) * 1000
            print(f"  [PASS] Database Connectivity OK (Latency: {latency_ms:.2f}ms)")
    except Exception as e:
        print(f"  [FAIL] Database Connection Refused: {e}")
        return False

    required_tables = {"users", "products", "orders", "order_items"}
    existing_tables = set(inspector.get_table_names())
    missing_tables = required_tables - existing_tables

    if missing_tables:
        print(f"  [FAIL] Missing Schema Tables: {missing_tables}")
        all_passed = False
    else:
        print(f"  [PASS] Required Tables Present: {sorted(list(required_tables))}")

    expected_fks = {
        "orders": {"users"},
        "order_items": {"orders", "products"}
    }
    for table, target_tables in expected_fks.items():
        fks = inspector.get_foreign_keys(table)
        referred = {fk["referred_table"] for fk in fks}
        if not target_tables.issubset(referred):
            print(f"  [FAIL] Foreign Key Mismatch on table '{table}'. Expected {target_tables}, found {referred}")
            all_passed = False
        else:
            print(f"  [PASS] Foreign Key Integrity Confirmed on '{table}' -> {target_tables}")

    try:
        with engine.begin() as conn:
            conn.execute(text("SAVEPOINT test_savepoint;"))
            try:
                conn.execute(
                    text("INSERT INTO users (username, email, wallet_balance) VALUES ('test_err', 'err@test.com', -50.00);")
                )
                print("  [FAIL] Check Constraint Failed: Negative wallet balance was allowed.")
                all_passed = False
            except Exception:
                print("  [PASS] Invariant Verified: Negative wallet balances strictly blocked by DB constraint.")
            finally:
                conn.execute(text("ROLLBACK TO SAVEPOINT test_savepoint;"))
    except Exception as e:
        print(f"  [FAIL] Invariant Check Error: {e}")
        all_passed = False

    elapsed = (time.time() - start_time) * 1000
    print(f"[PRE-FLIGHT] ================= PRE-FLIGHT SUMMARY: {'PASSED' if all_passed else 'FAILED'} ({elapsed:.1f}ms) ================\n")
    return all_passed

if __name__ == "__main__":
    success = run_preflight_checks()
    sys.exit(0 if success else 1)
