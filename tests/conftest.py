import pytest
import src.dao.db_connection as _db_module


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Chaque test reçoit une base SQLite fraîche dans un dossier temporaire."""
    monkeypatch.setattr(_db_module, "_connection", None)
    monkeypatch.setattr(_db_module, "_DB_PATH", tmp_path / "test.db")
    yield
    conn = _db_module._connection
    if conn is not None:
        conn.close()
    monkeypatch.setattr(_db_module, "_connection", None)
