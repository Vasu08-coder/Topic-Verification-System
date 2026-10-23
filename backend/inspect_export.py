from fastapi.testclient import TestClient
from app.main import app
from app.core.security import AdminIdentity
from app.routes import admin_export

class FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self._filters = []

    def filter(self, *criteria):
        self._filters.extend(criteria)
        return self

    def all(self):
        return list(self._rows)

class FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        return FakeQuery(self._rows.get(model, []))

class SubmissionRow:
    def __init__(self, name, sis_id, branch):
        self.name = name
        self.sis_id = sis_id
        self.branch = branch
        self.title = 'Demo topic'
        self.status = 'approved'
        self.similarity_score = 0.92
        self.reviewed_by = 7
        self.reviewed_at = None
        self.admin_notes = 'Looks good'

fake_session = FakeSession({admin_export.Submission: [SubmissionRow('Ada', 'SIS-1', 'CSE')]})

def override_get_db():
    yield fake_session

app.dependency_overrides[admin_export.get_db] = override_get_db
app.dependency_overrides[admin_export.require_faculty_or_above] = lambda: AdminIdentity(admin_id=2, username='faculty', role='faculty_coordinator', branch='CSE')

with TestClient(app) as client:
    response = client.get('/api/admin/export/submissions?format=csv')
    print(response.status_code)
    print(response.text)
