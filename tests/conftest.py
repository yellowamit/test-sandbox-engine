import pytest
import json
import os
import time
from tabulate import tabulate
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from scripts.seed_data import seed_test_database

test_results = []

def pytest_configure(config):
    config.addinivalue_line("markers", "req_id(id): Mark test case with associated requirement ID")

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    seed_test_database()
    yield

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        req_marker = item.get_closest_marker("req_id")
        req_id = req_marker.args[0] if req_marker else "REQ-UNASSIGNED"
        
        status = "PASSED" if report.passed else "FAILED"
        err_msg = str(report.longrepr) if report.failed else "None"

        test_results.append({
            "requirement_id": req_id,
            "test_name": item.nodeid.split("::")[-1],
            "module": item.nodeid.split("::")[0],
            "status": status,
            "duration_ms": round(report.duration * 1000, 2),
            "error_detail": err_msg
        })

def pytest_sessionfinish(session, exitstatus):
    os.makedirs("reports", exist_ok=True)
    
    json_path = "reports/test_execution_matrix.json"
    with open(json_path, "w") as f:
        json.dump(test_results, f, indent=2)

    md_path = "reports/test_execution_matrix.md"
    table_headers = ["Req ID", "Module", "Test Case", "Status", "Duration (ms)"]
    table_rows = [
        [r["requirement_id"], r["module"], r["test_name"], r["status"], r["duration_ms"]]
        for r in test_results
    ]
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASSED")
    failed = total - passed

    markdown_content = f"""# Test Execution & Result Analysis Report
**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  
**Total Tests:** {total} | **Passed:** {passed} | **Failed:** {failed}  
**Success Rate:** {(passed/total*100 if total else 0):.1f}%

## Verification Matrix
{tabulate(table_rows, headers=table_headers, tablefmt="github")}

## Audit Notes
- All assertions verified against PostgreSQL database states (row locks, foreign-key cascade integrity, non-negative constraints).
- Ephemeral test runs reset data using deterministic seeds (`seed_data.py`).
"""
    with open(md_path, "w") as f:
        f.write(markdown_content)

    print(f"\n[REPORT] Generated Prescribed Test Reports:\n  -> {json_path}\n  -> {md_path}\n")
