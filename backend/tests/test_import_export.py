from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.security import AdminIdentity, create_access_token
from app.main import app
from app.models.archive_topic import ArchiveTopic
from app.models.student import Student
from app.models.submission import Submission
from app.routes import admin_export, admin_import, admin_submissions, archive, submissions
from app.services import email_service


class FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class FakeSession:
    def __init__(self, rows: dict[type[Any], list[Any]] | None = None) -> None:
        self._rows = rows or {}
        self.added: list[Any] = []
        self._next_id = 1

    def query(self, model: type[Any]) -> "FakeQuery":
        return FakeQuery(self._rows.get(model, []), self)

    def execute(self, query: Any) -> FakeResult:
        rows: list[dict[str, Any]] = []
        for row in self._rows.get(ArchiveTopic, []):
            rows.append(
                {
                    "id": getattr(row, "id", None),
                    "module": getattr(row, "module", None),
                    "branch_id": getattr(row, "branch_id", None),
                    "branch_name": getattr(row, "branch_name", None) or getattr(row, "branch", None),
                    "academic_year_id": getattr(row, "academic_year_id", None),
                    "title": getattr(row, "title", None),
                    "abstract": getattr(row, "abstract", None),
                    "source": getattr(row, "source", None),
                    "created_at": getattr(row, "created_at", None),
                }
            )
        return FakeResult(rows)

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
            if getattr(obj, "uploaded_at", None) is None and hasattr(obj, "uploaded_at"):
                obj.uploaded_at = "2024-01-01T00:00:00"

    def refresh(self, obj: Any) -> None:
        return None


class FakeQuery:
    def __init__(self, rows: list[Any], session: FakeSession) -> None:
        self._rows = rows
        self._session = session
        self._filters: list[Any] = []
        self._order_by: list[Any] = []
        self._offset: int | None = None
        self._limit: int | None = None

    def filter(self, *criteria: Any) -> "FakeQuery":
        self._filters.extend(criteria)
        return self

    def order_by(self, *criteria: Any) -> "FakeQuery":
        self._order_by.extend(criteria)
        return self

    def offset(self, offset: int) -> "FakeQuery":
        self._offset = offset
        return self

    def limit(self, limit: int) -> "FakeQuery":
        self._limit = limit
        return self

    def first(self) -> Any:
        filtered = self._apply_filters(self._rows)
        return filtered[0] if filtered else None

    def one_or_none(self) -> Any:
        filtered = self._apply_filters(self._rows)
        if len(filtered) > 1:
            raise ValueError("Multiple rows found")
        return filtered[0] if filtered else None

    def all(self) -> list[Any]:
        return self._apply_filters(self._rows)

    def count(self) -> int:
        return len(self._apply_filters(self._rows))

    def _apply_filters(self, rows: list[Any]) -> list[Any]:
        filtered = list(rows)
        for criterion in self._filters:
            if not hasattr(criterion, "left") or not hasattr(criterion, "right"):
                continue
            attr_name = getattr(getattr(criterion.left, "name", None), "__str__", lambda: None)()
            if not attr_name:
                continue
            value = getattr(criterion.right, "value", criterion.right)
            filtered = [row for row in filtered if getattr(row, attr_name, None) == value]
        if self._offset is not None:
            filtered = filtered[self._offset :]
        if self._limit is not None:
            filtered = filtered[: self._limit]
        return filtered


def _excel_bytes(dataframe: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def _archive_topic(module: str, title: str, abstract: str, branch_id: int, academic_year_id: int = 1) -> ArchiveTopic:
    return ArchiveTopic(
        module=module,
        title=title,
        abstract=abstract,
        branch_id=branch_id,
        academic_year_id=academic_year_id,
        embedding=[0.0] * 384,
        source="test",
        created_at=datetime.utcnow(),
    )


def test_import_endpoint_imports_valid_rows_and_reports_failures(monkeypatch):
    fake_session = FakeSession()

    def override_get_db():
        yield fake_session

    dataframe = pd.DataFrame(
        [
            {"academic_year": "2024", "branch": "CSE", "title": "AI Ethics", "abstract": "Valid abstract"},
            {"academic_year": "2024", "branch": "UNKNOWN", "title": "Bad Branch", "abstract": "Ignored"},
            {"academic_year": "2024", "branch": "CSE", "title": "AI Ethics", "abstract": "Duplicate"},
        ]
    )

    app.dependency_overrides[admin_import.get_db] = override_get_db
    app.dependency_overrides[admin_import.require_admin_auth] = lambda: AdminIdentity(
        admin_id=7,
        username="super",
        full_name="Super Admin",
    )
    monkeypatch.setattr("app.services.similarity_service.embed_text", lambda title, abstract: [0.0] * 384)
    with patch("app.routes.admin_import.import_service.parse_excel", return_value=dataframe):
        with TestClient(app) as client:
            response = client.post(
                "/api/admin/import/seminar",
                files={"file": ("topics.xlsx", _excel_bytes(dataframe), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )

    assert response.status_code == 200
    payload = response.json()
    assert payload["imported_count"] == 1
    assert payload["failed_count"] == 2
    assert payload["total_records"] == 3
    assert payload["failure_details"] == [
        {"row_number": 3, "error_message": "branch is invalid"},
        {"row_number": 4, "error_message": "duplicate title in archive"},
    ]
    assert len(fake_session.added) == 4
    assert any(getattr(entry, "module", None) == "seminar" for entry in fake_session.added)
    assert any(getattr(entry, "file_name", None) == "topics.xlsx" for entry in fake_session.added)
    assert sum(getattr(entry, "row_number", None) is not None for entry in fake_session.added) == 2

    app.dependency_overrides.clear()


def test_import_endpoint_rejects_faculty_coordinator():
    fake_session = FakeSession()

    def override_get_db():
        yield fake_session

    app.dependency_overrides[admin_import.get_db] = override_get_db
    app.dependency_overrides[admin_import.require_admin_auth] = lambda: (_ for _ in ()).throw(
        HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/admin/import/seminar",
            files={"file": ("topics.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_export_endpoint_returns_filtered_rows_and_respects_branch_permissions():
    fake_session = FakeSession({ArchiveTopic: [
        _archive_topic("seminar", "Alpha", "A", 1),
        _archive_topic("seminar", "Beta", "B", 2),
    ]})

    def override_get_db():
        yield fake_session

    app.dependency_overrides[admin_export.get_db] = override_get_db
    app.dependency_overrides[admin_export.require_admin_auth] = lambda: AdminIdentity(
        admin_id=1,
        username="faculty",
        full_name="Faculty Admin",
    )

    with TestClient(app) as client:
        response = client.get("/api/admin/export/seminar?branch=CSE&format=csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    rows = [line for line in response.text.splitlines() if line and not line.startswith("id")]
    assert len(rows) == 1
    assert "Alpha" in response.text
    assert "Beta" not in response.text

    app.dependency_overrides.clear()


def test_faculty_and_super_admin_export_differ_in_branch_scope():
    fake_session = FakeSession({ArchiveTopic: [
        _archive_topic("seminar", "Alpha", "A", 1),
        _archive_topic("seminar", "Beta", "B", 2),
    ]})

    def override_get_db():
        yield fake_session

    app.dependency_overrides[admin_export.get_db] = override_get_db

    faculty_token = create_access_token(3, "faculty", "Faculty Admin")
    with TestClient(app) as client:
        faculty_response = client.get(
            "/api/admin/export/seminar?branch=EEE&format=csv",
            headers={"Authorization": f"Bearer {faculty_token}"},
        )

    assert faculty_response.status_code == 200
    assert "Beta" in faculty_response.text
    assert "Alpha" not in faculty_response.text

    super_admin_token = create_access_token(4, "super", "Super Admin")
    with TestClient(app) as client:
        super_admin_response = client.get(
            "/api/admin/export/seminar?branch=EEE&format=csv",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )

    assert super_admin_response.status_code == 200
    assert "Beta" in super_admin_response.text
    assert "Alpha" not in super_admin_response.text

    app.dependency_overrides.clear()


def test_public_archive_endpoint_omits_abstract_field():
    fake_session = FakeSession({ArchiveTopic: [
        _archive_topic("seminar", "Alpha", "Secret", 1),
        _archive_topic("project", "Beta", "Hidden", 2),
    ]})

    def override_get_db():
        yield fake_session

    app.dependency_overrides[archive.get_db] = override_get_db

    with TestClient(app) as client:
        response = client.get("/api/public/archive/seminar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["module"] == "seminar"
    assert payload["items"][0]["title"] == "Alpha"
    assert "abstract" not in payload["items"][0]
    assert "academic_year" not in payload["items"][0]
    assert "branch" not in payload["items"][0]

    app.dependency_overrides.clear()


def test_flagged_submission_sends_expected_email_arguments(monkeypatch):
    student = Student(id=1, full_name="Ada", sis_id="SIS-100", branch_id=1)
    student.email = "ada@example.com"
    fake_session = FakeSession({Student: [student], Submission: []})

    def override_get_db():
        yield fake_session

    app.dependency_overrides[submissions.get_db] = override_get_db
    
    # Override student auth
    from app.core.security import StudentIdentity
    def override_student_auth():
        return StudentIdentity(student_id=1, sis_id="SIS-100", full_name="Ada")
    
    app.dependency_overrides[submissions.require_student_auth] = override_student_auth
    
    monkeypatch.setattr(submissions.similarity_service, "embed_text", lambda title, abstract: [0.0] * 384)
    monkeypatch.setattr(
        submissions.similarity_service,
        "find_similar_topics",
        lambda db_session, embedding, branch, module_type, top_k=3: [{"archive_id": 1, "year": "2025", "title": "Existing topic", "similarity": 0.95}],
    )

    with patch("app.routes.submissions.send_email") as send_email_mock:
        with TestClient(app) as client:
            response = client.post(
                "/api/submissions/check-similarity",
                json={
                    "branch": "CSE",
                    "module_type": "seminar",
                    "title": "New topic",
                    "abstract": "A new abstract",
                },
            )

    assert response.status_code == 200
    send_email_mock.assert_called_once()
    to_address, subject, body = send_email_mock.call_args.args
    assert to_address == "ada@example.com"
    assert subject == "Submission flagged for review"
    assert "flagged" in body.lower()

    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("action", "expected_subject", "expected_phrase"),
    [
        ("approve", "Submission approved", "approved"),
        ("reject", "Submission rejected", "rejected"),
    ],
)
def test_admin_decision_emails_are_sent_for_review_outcomes(monkeypatch, action, expected_subject, expected_phrase):
    fake_session = FakeSession({Submission: []})

    def override_get_db():
        yield fake_session

    submission = Submission(
        student_id=1,
        module="seminar",
        branch_id=1,
        academic_year_id=1,
        title="Some topic",
        abstract="Abstract",
        embedding=[0.0] * 384,
        similarity_score=0.1,
        status="pending",
        submitted_at=datetime.utcnow(),
    )
    student = Student(id=1, full_name="Ada", sis_id="SIS-200", branch_id=1)
    student.email = "ada@example.com"
    submission.student = student
    fake_session.add(student)
    fake_session.add(submission)

    app.dependency_overrides[admin_submissions.get_db] = override_get_db
    app.dependency_overrides[admin_submissions.require_admin_auth] = lambda: AdminIdentity(
        admin_id=10,
        username="super",
        full_name="Super Admin",
    )

    with patch("app.routes.admin_submissions.send_email") as send_email_mock:
        with TestClient(app) as client:
            response = client.post(
                f"/api/admin/submissions/{submission.id}/decision",
                json={"action": action, "notes": "Looks good"},
            )

    assert response.status_code == 200
    send_email_mock.assert_called_once()
    to_address, subject, body = send_email_mock.call_args.args
    assert to_address == "ada@example.com"
    assert subject == expected_subject
    assert expected_phrase in body.lower()

    app.dependency_overrides.clear()


def test_send_email_does_not_raise_when_smtp_send_fails(monkeypatch):
    monkeypatch.setattr(email_service.settings, "ENVIRONMENT", "prod")
    monkeypatch.setattr(email_service.settings, "EMAIL_BACKEND", "smtp")

    with patch("app.services.email_service.smtplib.SMTP", side_effect=RuntimeError("boom")):
        email_service.send_email("student@example.com", "Subject", "Body")
