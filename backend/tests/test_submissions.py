from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.security import AdminIdentity, StudentIdentity
from app.main import app
from app.models.archive_topic import ArchiveTopic
from app.models.branch import Branch
from app.models.student import Student
from app.models.submission import Submission
from app.models.activity_log import ActivityLog
from app.routes import admin_submissions, submissions


class FakeQuery:
    def __init__(self, rows: list[Any], session: "FakeSession") -> None:
        self._rows = rows
        self._session = session
        self._filters: list[Any] = []

    def filter(self, *criteria: Any) -> "FakeQuery":
        self._filters.extend(criteria)
        return self

    def first(self) -> Any:
        rows = self._apply_filters(self._rows)
        return rows[0] if rows else None

    def one_or_none(self) -> Any:
        rows = self._apply_filters(self._rows)
        if len(rows) > 1:
            raise ValueError("Multiple rows found")
        return rows[0] if rows else None

    def all(self) -> list[Any]:
        return self._apply_filters(self._rows)

    def count(self) -> int:
        return len(self._apply_filters(self._rows))

    def offset(self, offset: int) -> "FakeQuery":
        self._offset = offset
        return self

    def limit(self, limit: int) -> "FakeQuery":
        self._limit = limit
        return self

    def options(self, *args: Any, **kwargs: Any) -> "FakeQuery":
        return self

    def order_by(self, *criteria: Any) -> "FakeQuery":
        self._order_by = criteria
        return self

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
        if getattr(self, "_offset", None) is not None:
            filtered = filtered[self._offset :]
        if getattr(self, "_limit", None) is not None:
            filtered = filtered[: self._limit]
        return filtered


class FakeSession:
    def __init__(self) -> None:
        self.data: dict[type[Any], list[Any]] = defaultdict(list)
        self._added: list[Any] = []
        self._next_id = 1

    def query(self, model: type[Any]) -> FakeQuery:
        return FakeQuery(self.data[model], self)

    def add(self, obj: Any) -> None:
        self._added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = self._next_id
            self._next_id += 1
        self.data[type(obj)].append(obj)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        return None

    def refresh(self, obj: Any) -> None:
        return None


@pytest.fixture
def client(monkeypatch):
    fake_session = FakeSession()

    def override_get_db():
        yield fake_session

    app.dependency_overrides[admin_submissions.get_db] = override_get_db
    app.dependency_overrides[submissions.get_db] = override_get_db

    # Create a test student identity for auth override
    # This is used as the default authenticated student for student endpoints
    test_student_identity = StudentIdentity(student_id=1, sis_id="TEST_SIS_001", full_name="Test Student")

    def override_student_dependency():
        return test_student_identity

    app.dependency_overrides[submissions.require_student_auth] = override_student_dependency

    monkeypatch.setattr(submissions.similarity_service, "embed_text", lambda title, abstract: [0.0] * 384)
    monkeypatch.setattr(submissions.similarity_service, "find_similar_topics", lambda db_session, embedding, branch, module_type, top_k=3: [])

    with TestClient(app) as client:
        yield client, fake_session

    app.dependency_overrides.clear()


def _make_submission(session: FakeSession, *, status: str = "pending", branch: str = "CSE", module_type: str = "seminar") -> Submission:
    submission = Submission(
        student_id=1,
        module=module_type,
        branch_id=1,
        academic_year_id=1,
        title="Test Title",
        abstract="Test abstract",
        embedding=[0.0] * 384,
        similarity_score=0.0,
        status=status,
        submitted_at=datetime.utcnow(),
    )
    session.add(submission)
    return submission


def test_admin_submission_detail_includes_student_and_branch_data(client):
    client_obj, session = client

    branch = Branch(name="Computer Science", code="CSE", is_active=True)
    branch.id = 1
    student = Student(sis_id="SIS-123", full_name="Ada Lovelace", branch_id=branch.id)
    student.id = 1
    submission = Submission(
        student_id=student.id,
        module="seminar",
        branch_id=branch.id,
        academic_year_id=1,
        title="Test Title",
        abstract="Test abstract",
        embedding=[0.0] * 384,
        similarity_score=0.0,
        status="pending",
        submitted_at=datetime.utcnow(),
    )
    submission.id = 10
    session.add(branch)
    session.add(student)
    session.add(submission)

    def override_admin_dependency():
        return AdminIdentity(admin_id=5, username="admin", full_name="Super Admin")

    app.dependency_overrides[admin_submissions.require_admin_auth] = override_admin_dependency

    response = client_obj.get(f"/api/admin/submissions/{submission.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["student_full_name"] == "Ada Lovelace"
    assert payload["student_sis_id"] == "SIS-123"
    assert payload["branch_name"] == "Computer Science"


def test_admin_submission_list_includes_student_and_branch_data(client):
    client_obj, session = client

    branch = Branch(name="Mechanical Engineering", code="ME", is_active=True)
    branch.id = 2
    student = Student(sis_id="SIS-456", full_name="Grace Hopper", branch_id=branch.id)
    student.id = 2
    submission = Submission(
        student_id=student.id,
        module="project",
        branch_id=branch.id,
        academic_year_id=1,
        title="Second Title",
        abstract="Second abstract",
        embedding=[0.0] * 384,
        similarity_score=0.0,
        status="pending",
        submitted_at=datetime.utcnow(),
    )
    submission.id = 11
    session.add(branch)
    session.add(student)
    session.add(submission)

    def override_admin_dependency():
        return AdminIdentity(admin_id=6, username="admin", full_name="Super Admin")

    app.dependency_overrides[admin_submissions.require_admin_auth] = override_admin_dependency

    response = client_obj.get("/api/admin/submissions")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["student_full_name"] == "Grace Hopper"
    assert payload[0]["student_sis_id"] == "SIS-456"
    assert payload[0]["branch_name"] == "Mechanical Engineering"


def test_check_similarity_with_empty_archive_returns_pending_and_empty_matches(client):
    client_obj, session = client
    
    # Create a branch and student for the submission
    branch = Branch(name="Computer Science", code="CSE", is_active=True)
    branch.id = 1
    session.add(branch)
    
    test_student = Student(sis_id="TEST_SIS_001", full_name="Test Student", branch_id=1)
    test_student.id = 1
    session.add(test_student)

    response = client_obj.post(
        "/api/submissions/check-similarity",
        json={
            "branch": "CSE",
            "module_type": "seminar",
            "title": "New topic",
            "abstract": "Abstract text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["matches"] == []
    assert payload["can_upload_abstract"] is True
    assert session.query(Submission).all()


def test_check_similarity_with_near_duplicate_archive_row_returns_flagged(client, monkeypatch):
    client_obj, session = client
    
    # Create a branch and student for the submission
    branch = Branch(name="Computer Science", code="CSE", is_active=True)
    branch.id = 1
    session.add(branch)
    
    test_student = Student(sis_id="TEST_SIS_001", full_name="Test Student", branch_id=1)
    test_student.id = 1
    session.add(test_student)

    monkeypatch.setattr(
        submissions.similarity_service,
        "find_similar_topics",
        lambda db_session, embedding, branch, module_type, top_k=3: [{"archive_id": 1, "year": "2024", "title": "Existing topic", "similarity": 0.9}],
    )

    response = client_obj.post(
        "/api/submissions/check-similarity",
        json={
            "branch": "CSE",
            "module_type": "seminar",
            "title": "Near duplicate",
            "abstract": "Abstract text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "flagged"
    assert payload["best_similarity"] == 0.9
    assert payload["matches"][0]["title"] == "Existing topic"
    assert payload["can_upload_abstract"] is False


def test_submission_endpoint_requires_authentication(client):
    """Confirm that submission endpoints reject unauthenticated requests."""
    client_obj, _ = client
    # Temporarily clear auth override to test unauthenticated access
    app.dependency_overrides.pop(submissions.require_student_auth, None)

    response = client_obj.post(
        "/api/submissions/check-similarity",
        json={
            "branch": "CSE",
            "module_type": "seminar",
            "title": "New topic",
            "abstract": "Abstract text",
        },
    )

    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_upload_abstract_rejected_when_submission_is_flagged(client):
    client_obj, session = client
    submission = _make_submission(session, status="flagged")

    response = client_obj.post(
        f"/api/submissions/{submission.id}/upload-abstract",
        files={"file": ("topic.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Flagged submissions cannot upload an abstract"


def test_upload_abstract_rejects_wrong_extension(client):
    client_obj, session = client
    submission = _make_submission(session, status="pending")

    response = client_obj.post(
        f"/api/submissions/{submission.id}/upload-abstract",
        files={"file": ("topic.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Uploaded file signature does not match a supported PDF or DOCX file"


def test_approving_submission_inserts_archive_row(client):
    client_obj, session = client
    submission = _make_submission(session, branch="CSE", module_type="seminar")

    def override_admin_dependency():
        return AdminIdentity(admin_id=5, username="admin", full_name="Super Admin")

    app.dependency_overrides[admin_submissions.require_admin_auth] = override_admin_dependency

    response = client_obj.post(
        f"/api/admin/submissions/{submission.id}/decision",
        json={"action": "approve", "notes": "Approved"},
    )

    assert response.status_code == 200
    assert session.query(ArchiveTopic).count() == 1
    archived = session.query(ArchiveTopic).all()[0]
    assert archived.title == submission.title
    assert archived.branch_id == submission.branch_id


def test_decision_creates_one_history_entry_with_expected_statuses(client):
    client_obj, session = client
    submission = _make_submission(session, status="pending", branch="CSE", module_type="project")

    def override_admin_dependency():
        return AdminIdentity(admin_id=7, username="admin", full_name="Super Admin")

    app.dependency_overrides[admin_submissions.require_admin_auth] = override_admin_dependency

    response = client_obj.post(
        f"/api/admin/submissions/{submission.id}/decision",
        json={"action": "needs_modification", "notes": "Needs revision"},
    )

    assert response.status_code == 200
    history_rows = session.query(ActivityLog).all()
    assert len(history_rows) == 1
    assert history_rows[0].action_type == "resub_requested"
    assert history_rows[0].description == "Needs revision"
