from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi.testclient import TestClient

from app.core.security import AdminIdentity
from app.main import app
from app.routes import admin_import


class FakeQuery:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows
        self._filters: list[Any] = []
        self._order_by: list[Any] = []

    def filter(self, *criteria: Any) -> "FakeQuery":
        self._filters.extend(criteria)
        return self

    def order_by(self, *criteria: Any) -> "FakeQuery":
        self._order_by.extend(criteria)
        return self

    def all(self) -> list[Any]:
        return list(self._rows)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self._next_id = 1
        self._rows: dict[type[Any], list[Any]] = {}

    def add(self, obj: Any) -> None:
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = self._next_id
            self._next_id += 1
        self._rows.setdefault(type(obj), []).append(obj)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        for obj in self.added:
            if getattr(obj, "uploaded_at", None) is None:
                obj.uploaded_at = datetime.utcnow()

    def refresh(self, obj: Any) -> None:
        return None

    def query(self, model: type[Any]) -> FakeQuery:
        return FakeQuery(self._rows.get(model, []))


def test_admin_import_endpoint_creates_import_history(monkeypatch):
    fake_session = FakeSession()

    def override_get_db():
        yield fake_session

    def fake_parse_excel(_bytes: bytes, _filename: str) -> pd.DataFrame:
        return pd.DataFrame(
            [{"academic_year": "2024", "branch": "CSE", "title": "AI Ethics", "abstract": "A sample abstract"}]
        )

    def fake_import_rows(_db_session: Any, module_type: str, dataframe: pd.DataFrame, filename: str) -> dict[str, Any]:
        assert module_type == "seminar"
        assert len(dataframe) == 1
        assert filename == "topics.xlsx"
        return {
            "total_records": 1,
            "imported": 1,
            "failed": 0,
            "failure_details": [],
            "filename": filename,
            "module_type": module_type,
        }

    app.dependency_overrides[admin_import.get_db] = override_get_db
    app.dependency_overrides[admin_import.require_admin_auth] = lambda: AdminIdentity(
        admin_id=42,
        username="super",
        full_name="Super Admin",
    )
    monkeypatch.setattr(admin_import.import_service, "parse_excel", fake_parse_excel)
    monkeypatch.setattr(admin_import.import_service, "import_rows", fake_import_rows)

    with TestClient(app) as client:
        response = client.post(
            "/api/admin/import/seminar",
            files={"file": ("topics.xlsx", b"PK\x03\x04fake-bytes", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["file_name"] == "topics.xlsx"
    assert payload["module"] == "seminar"
    assert payload["imported_count"] == 1
    assert payload["failed_count"] == 0
    assert len(fake_session.added) == 1

    app.dependency_overrides.clear()
