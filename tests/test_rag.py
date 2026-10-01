from app.models import CourseChunk, CourseDocument
from app.services.rag import index_chunk, search_course


def test_local_course_retrieval(db):
    doc = CourseDocument(title="Aerodynamics Handbook", module="Aerodynamics", topic="Boundary layers", document_type="handbook", source="user_upload", original_filename="a.txt", sha256="a"*64)
    db.add(doc); db.flush()
    chunk = CourseChunk(document_id=doc.id, chunk_index=0, page=17, content="The boundary layer contains strong velocity gradients near the wall.")
    db.add(chunk); db.flush(); index_chunk(db, chunk, doc); db.commit()
    results = search_course(db, "boundary velocity", module="Aerodynamics")
    assert results
    assert results[0]["page"] == 17
    assert "velocity gradients" in results[0]["content"]
