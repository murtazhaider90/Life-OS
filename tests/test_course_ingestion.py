import io

from docx import Document
from pptx import Presentation

from app.models import CourseDocument
from app.services.course_ingestion import DuplicateDocumentError, ingest_document_bytes
from app.services.documents import extract_pages, infer_document_type


def test_document_type_inference():
    assert infer_document_type("MECH302_Module_Handbook.pdf") == "handbook"
    assert infer_document_type("Coursework Brief.docx") == "coursework_spec"
    assert infer_document_type("Lecture 05 Boundary Layers.pptx") == "lecture"
    assert infer_document_type("Marking Rubric.pdf") == "marking_criteria"


def test_docx_and_pptx_text_extraction():
    doc = Document()
    doc.add_paragraph("Learning outcome: Apply conservation of energy.")
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_pages = extract_pages("guide.docx", doc_bytes.getvalue())
    assert "conservation of energy" in doc_pages[0][1]

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Boundary layers"
    ppt_bytes = io.BytesIO()
    prs.save(ppt_bytes)
    ppt_pages = extract_pages("lecture.pptx", ppt_bytes.getvalue())
    assert any("Boundary layers" in text for _, text in ppt_pages)


def test_ingestion_deduplicates_and_runs_analysis(db):
    data = (
        b"Learning outcomes:\n"
        b"Apply the momentum equation to a control volume.\n"
        b"Assessment: Problem set due 2026-12-10 worth 20%."
    )
    result = ingest_document_bytes(
        db,
        filename="module_syllabus.txt",
        data=data,
        module="Fluid Mechanics",
        document_type="syllabus",
        academic_year="2026/27",
    )
    assert result["chunks"] >= 1
    assert result["analysis"]["learning_objectives_created"] >= 1
    assert db.query(CourseDocument).count() == 1

    try:
        ingest_document_bytes(
            db,
            filename="copy.txt",
            data=data,
            module="Fluid Mechanics",
        )
    except DuplicateDocumentError:
        pass
    else:
        raise AssertionError("duplicate content must be rejected")
