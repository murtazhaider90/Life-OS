from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import CourseChunk, CourseDocument
from app.services.assistant import handle_assistant_message
from app.services.rag import index_chunk


def add_doc(db):
    doc = CourseDocument(
        title="Aerodynamics Lecture",
        module="Aerodynamics",
        topic="Boundary layers",
        document_type="lecture",
        source="user_upload",
        original_filename="lecture.txt",
        sha256="z" * 64,
    )
    db.add(doc); db.flush()
    chunk = CourseChunk(
        document_id=doc.id,
        chunk_index=0,
        page=12,
        content="Boundary layer separation occurs when the near-wall flow reverses under an adverse pressure gradient.",
    )
    db.add(chunk); db.flush(); index_chunk(db, chunk, doc); db.commit()


def test_assistant_answers_from_course_material(db):
    add_doc(db)
    now = datetime(2026, 11, 19, 12, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(
        db,
        "Explain boundary layer separation from my course material",
        now,
    )
    assert result["action"] == "academic_answer"
    assert "[S1]" in result["reply"]
    assert "Aerodynamics Lecture" in result["reply"]


def test_assistant_generates_source_backed_quiz(db):
    add_doc(db)
    now = datetime(2026, 11, 19, 12, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(db, "Quiz me on boundary layer separation", now)
    assert result["action"] == "academic_quiz"
    assert result["data"]["questions"]
    assert "Source-backed retrieval quiz" in result["reply"]
