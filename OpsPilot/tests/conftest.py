import pytest
from opspilot.database.db import initialize_database


@pytest.fixture
def demo_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_opspilot.db"
    monkeypatch.setenv("OPSILOT_DB_PATH", str(db_path))
    monkeypatch.setenv("OPSILOT_APPROVALS_DIR", str(tmp_path / "approvals"))
    monkeypatch.setenv("OPSILOT_REPORTS_DIR", str(tmp_path / "reports"))
    initialize_database()
    return db_path
