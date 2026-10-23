from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.file_validation import sanitize_filename, validate_file_signature
from app.core.security import AdminIdentity, StudentIdentity
from app.main import app
from app.models.submission import Submission
from app.routes import admin_import, submissions


class FakeUploadFile:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self._position = offset
        elif whence == 1:
            self._position += offset
        elif whence == 2:
            self._position = len(self._data) + offset
        return self._position

    def tell(self) -> int:
        return self._position


def test_renamed_exe_with_pdf_extension_is_rejected():
    assert validate_file_signature(b"MZ\x90\x00\x03", "pdf") is False


def test_path_traversal_filename_is_sanitized():
    assert sanitize_filename("../../etc/passwd.pdf") == "etcpasswd.pdf"


def test_oversized_file_is_rejected_before_reading_entire_stream():
    stream = FakeUploadFile(b"%PDF-1.4\n" + b"a" * 200)
    with pytest.raises(Exception):
        from app.core.file_validation import enforce_max_size

        enforce_max_size(stream, 10)


class FakeQuery:
    def __init__(self, result: object) -> None:
        self._result = result

    def filter(self, *args, **kwargs) -> "FakeQuery":
        return self

    def first(self) -> object:
        return self._result

    def one_or_none(self) -> object:
        return self._result


class FakeSession:
    def __init__(self, result: object) -> None:
        self._result = result

    def query(self, *_args, **_kwargs) -> FakeQuery:
        return FakeQuery(self._result)

    def add(self, _obj: object) -> None:
        return None

    def commit(self) -> None:
        return None

    def refresh(self, _obj: object) -> None:
        return None


def test_submission_upload_rejects_renamed_binary_file():
    submission = Submission(
        student_id=1,
        module="seminar",
        branch_id=1,
        academic_year_id=1,
        title="Topic",
        abstract="Abstract",
        embedding=[0.0] * 384,
        similarity_score=0.0,
        status="pending",
    )
    fake_session = FakeSession(submission)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[submissions.get_db] = override_get_db
    
    # Override student auth
    def override_student_auth():
        return StudentIdentity(student_id=1, sis_id="TEST_SIS", full_name="Test Student")
    
    app.dependency_overrides[submissions.require_student_auth] = override_student_auth

    with TestClient(app) as client:
        response = client.post(
            "/api/submissions/1/upload-abstract",
            files={"file": ("topic.pdf", b"MZ\x90\x00\x03", "application/pdf")},
        )

    assert response.status_code == 400
    assert "signature" in response.text.lower()

    app.dependency_overrides.clear()


def test_admin_import_rejects_renamed_binary_file():
    def override_get_db():
        yield FakeSession(None)

    app.dependency_overrides[admin_import.get_db] = override_get_db
    app.dependency_overrides[admin_import.require_admin_auth] = lambda: AdminIdentity(
        admin_id=8,
        username="super",
        full_name="Super Admin",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/admin/import/seminar",
            files={"file": ("topics.xlsx", b"MZ\x90\x00\x03", "application/vnd.openxmlformats-officedocument/spreadsheetml.sheet")},
        )

    assert response.status_code == 400
    assert "signature" in response.text.lower()

    app.dependency_overrides.clear()
