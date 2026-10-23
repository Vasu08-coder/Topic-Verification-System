from app.services.similarity_service import find_similar_topics


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class DummyQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *criteria, **kwargs):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def one_or_none(self):
        return self._rows[0] if self._rows else None


class DummySession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        return DummyQuery(self._rows)

    def execute(self, query):
        return DummyResult(self._rows)


def test_find_similar_topics_returns_empty_matches_for_empty_archive():
    session = DummySession([])

    matches = find_similar_topics(session, [0.0] * 384, branch="CSE", module_type="seminar", top_k=3)

    assert matches == []
