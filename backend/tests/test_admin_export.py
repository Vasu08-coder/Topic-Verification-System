from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from fastapi.testclient import TestClient

from app.core.security import AdminIdentity
from app.main import app
from app.models.archive_topic import ArchiveTopic
from app.models.submission import Submission
from app.routes import admin_export


class FakeQuery:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows
        self._filters: list[Any] = []

    def filter(self, *criteria: Any) -> "FakeQuery":
        self._filters.extend(criteria)
        return self

    def first(self) -> Any | None:
        rows = self._apply_filters(self._rows)
        return rows[0] if rows else None

    def one_or_none(self) -> Any | None:
        rows = self._apply_filters(self._rows)
        if len(rows) > 1:
            raise ValueError("Multiple rows found")
        return rows[0] if rows else None

    def all(self) -> list[Any]:
        return self._apply_filters(self._rows)

    def _apply_filters(self, rows: list[Any]) -> list[Any]:
        filtered = list(rows)
        for criterion in self._filters:
            if not hasattr(criterion, "left") or not hasattr(criterion, "right"):
                continue
            attr_name = getattr(getattr(criterion.left, "key", None), "__str__", lambda: None)()
            if not attr_name:
                continue
            value = getattr(criterion.right, "value", criterion.right)
            filtered = [row for row in filtered if getattr(row, attr_name, None) == value]
        return filtered


class FakeResult:
    def __init__(self, rows: list[Any] | None = None, scalar: Any | None = None) -> None:
        self._rows = rows if rows is not None else []
        self._scalar = scalar

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[Any]:
        return self._rows

    def scalar(self) -> Any:
        return self._scalar


class FakeSession:
    def __init__(self, rows: dict[type[Any], list[Any]]) -> None:
        self._rows = rows

    def query(self, model: type[Any]) -> FakeQuery:
        return FakeQuery(self._rows.get(model, []))

    def execute(self, query: Any) -> FakeResult:
        return FakeResult(self._rows.get(ArchiveTopic, []))


class ArchiveRow:
    def __init__(self, title: str, branch: str, academic_year: str) -> None:
        self.title = title
        self.branch = branch
        self.academic_year = academic_year
        self.abstract = "Abstract"
        self.status = "Approved"
        self.created_at = None


class SubmissionRow:
    def __init__(self, name: str, sis_id: str, branch: str) -> None:
        self.name = name
        self.sis_id = sis_id
        self.branch = branch
        self.title = "Demo topic"
        self.status = "approved"
        self.similarity_score = 0.92
        self.reviewed_by = 7
        self.reviewed_at = None
        self.admin_notes = "Looks good"


def test_archive_export_returns_xlsx_for_faculty_branch(monkeypatch):
    fake_session = FakeSession({ArchiveTopic: [ArchiveRow("Alpha", "CSE", "2025-26"), ArchiveRow("Beta", "EEE", "2025-26")]})
    faculty_branch = "CSE"

    def override_get_db():
        yield fake_session

    app.dependency_overrides[admin_export.get_db] = override_get_db
    app.dependency_overrides[admin_export.require_faculty_or_above] = lambda: AdminIdentity(
        admin_id=1,
        username="faculty",
        full_name="Faculty Admin",
        role="faculty_coordinator",
        branch=faculty_branch,
    )

    with TestClient(app) as client:
        response = client.get("/api/admin/export/seminar?branch=EEE&format=xlsx")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    disposition = response.headers["content-disposition"].lower()
    assert "seminar" in disposition
    assert ".xlsx" in disposition
    assert faculty_branch.lower() in disposition or "all" in disposition

    frame = pd.read_excel(BytesIO(response.content))
    assert list(frame["branch"]) == [faculty_branch]

    app.dependency_overrides.clear()


def test_submissions_export_returns_csv_with_expected_columns(monkeypatch):
    fake_session = FakeSession({Submission: [SubmissionRow("Ada", "SIS-1", "CSE")]})

    def override_get_db():
        yield fake_session

    app.dependency_overrides[admin_export.get_db] = override_get_db
    app.dependency_overrides[admin_export.require_faculty_or_above] = lambda: AdminIdentity(
        admin_id=2,
        username="faculty",
        full_name="Faculty Admin",
        role="faculty_coordinator",
        branch="CSE",
    )

    with TestClient(app) as client:
        response = client.get("/api/admin/export/submissions?format=csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    disposition = response.headers["content-disposition"].lower()
    assert "submissions" in disposition
    assert ".csv" in disposition
    assert "cse" in disposition or "all" in disposition
    assert "student_id" in response.text or "sis_id" in response.text

    app.dependency_overrides.clear()
