import pytest
from pathlib import Path
from app.models.domain import AnalysisState, DocType
from app.pipeline.nodes.parse_document import parse_document


def test_parse_valid_pdf():
    state = AnalysisState(job_id="test-001")
    with open("tests/fixtures/sample_dpa.pdf", "rb") as f:
        file_bytes = f.read()
    result = parse_document(state, file_bytes=file_bytes, filename="sample_dpa.pdf")
    assert result.raw_text != ""
    assert "Data Processing Agreement" in result.raw_text


def test_parse_valid_docx():
    state = AnalysisState(job_id="test-002")
    with open("tests/fixtures/sample_msa.docx", "rb") as f:
        file_bytes = f.read()
    result = parse_document(state, file_bytes=file_bytes, filename="sample_msa.docx")
    assert "Master Service Agreement" in result.raw_text


def test_rejects_file_over_20mb():
    state = AnalysisState(job_id="test-003")
    big_bytes = b"x" * (21 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds maximum"):
        parse_document(state, file_bytes=big_bytes, filename="big.pdf")


def test_rejects_wrong_magic_bytes():
    state = AnalysisState(job_id="test-004")
    fake_pdf = b"This is not a real PDF"
    with pytest.raises(ValueError, match="(?i)unsupported file type"):
        parse_document(state, file_bytes=fake_pdf, filename="fake.pdf")


def test_doc_type_classified_as_dpa():
    state = AnalysisState(job_id="test-005")
    with open("tests/fixtures/sample_dpa.pdf", "rb") as f:
        file_bytes = f.read()
    result = parse_document(state, file_bytes=file_bytes, filename="sample_dpa.pdf")
    assert result.doc_type == DocType.DPA
