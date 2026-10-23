from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.archive_topic import ArchiveTopic
from app.models.branch import Branch

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - dependency may not be installed in some environments
    SentenceTransformer = None


# Load the embedding model once so repeated calls don't reinitialize it.
# This is intentionally isolated behind a stable signature so a teammate can swap
# in a different embedding pipeline later without changing the service contract.
_EMBEDDING_MODEL: Any | None = None
_EMBEDDING_MODEL_ERROR: str | None = None


def _get_embedding_model() -> Any | None:
    global _EMBEDDING_MODEL, _EMBEDDING_MODEL_ERROR

    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL

    if SentenceTransformer is None:
        _EMBEDDING_MODEL_ERROR = "sentence-transformers is not installed"
        return None

    try:
        _EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        _EMBEDDING_MODEL_ERROR = str(exc)
        _EMBEDDING_MODEL = None

    return _EMBEDDING_MODEL


def embed_text(title: str, abstract: str) -> list[float]:
    """Create a 384-dimensional embedding for the submitted topic text."""
    model = _get_embedding_model()
    if model is None:
        raise RuntimeError(_EMBEDDING_MODEL_ERROR or "sentence-transformers model could not be loaded")

    text = f"{title}\n{abstract}".strip()
    embedding = model.encode(text, convert_to_numpy=False)
    return [float(value) for value in embedding]


def find_similar_topics(
    db_session: Session,
    embedding: list[float],
    branch: str | int,
    module_type: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Find similar archived topics using pgvector cosine similarity.

    Returns an empty list if the relevant archive has no rows for the branch.
    """
    if top_k <= 0:
        return []

    if module_type not in {"seminar", "project"}:
        return []

    branch_id: int | None = branch if isinstance(branch, int) else None
    if branch_id is None and isinstance(branch, str):
        branch_row = db_session.query(Branch).filter((Branch.code == branch) | (Branch.name == branch)).one_or_none()
        branch_id = branch_row.id if branch_row is not None else None

    if branch_id is None:
        return []

    query = (
        select(
            ArchiveTopic.id.label("archive_id"),
            ArchiveTopic.title,
            (1 - ArchiveTopic.embedding.cosine_distance(embedding)).label("similarity"),
        )
        .where(ArchiveTopic.module == module_type)
        .where(ArchiveTopic.branch_id == branch_id)
        .order_by(ArchiveTopic.embedding.cosine_distance(embedding))
        .limit(top_k)
    )

    result = db_session.execute(query)
    rows = result.mappings().all()

    if not rows:
        return []

    matches: list[dict[str, Any]] = []
    for row in rows:
        similarity = float(row.similarity or 0.0)
        matches.append(
            {
                "archive_id": int(row.archive_id),
                "title": str(row.title),
                "year": None,
                "similarity": similarity,
            }
        )

    return matches
