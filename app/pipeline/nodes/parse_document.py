import fitz  # PyMuPDF
from docx import Document as DocxDocument
from io import BytesIO
from app.models.domain import AnalysisState, DocType
from app.config import settings

_PDF_MAGIC = b"%PDF"
_DOCX_MAGIC = b"PK\x03\x04"  # ZIP-based format
_MAX_BYTES = settings.max_upload_mb * 1024 * 1024

_DOC_TYPE_KEYWORDS: dict[DocType, list[str]] = {
    DocType.DPA: ["data processing agreement", "data processor agreement", "dpa"],
    DocType.MSA: ["master service agreement", "master services agreement", "msa"],
    DocType.NDA: ["non-disclosure agreement", "confidentiality agreement", "nda"],
    DocType.SOW: ["statement of work", "scope of work", "sow", "purchase order"],
    DocType.POLICY: ["privacy policy", "security policy", "information security"],
}


def _classify_doc_type(text: str) -> DocType:
    lower = text[:2000].lower()
    for doc_type, keywords in _DOC_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return doc_type
    return DocType.UNKNOWN


def _extract_text_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = [page.get_text() for page in doc]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            "Could not extract text from this PDF. "
            "It may be a scanned image-only document. "
            "Please provide a text-based PDF or DOCX."
        )
    return text


def _extract_text_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_document(
    state: AnalysisState,
    file_bytes: bytes,
    filename: str,
) -> AnalysisState:
    if len(file_bytes) > _MAX_BYTES:
        raise ValueError(
            f"File size exceeds maximum allowed size of {settings.max_upload_mb}MB."
        )

    if file_bytes[:4] == _PDF_MAGIC:
        raw_text = _extract_text_pdf(file_bytes)
    elif file_bytes[:4] == _DOCX_MAGIC:
        raw_text = _extract_text_docx(file_bytes)
    else:
        raise ValueError(
            "Unsupported file type. Only PDF and DOCX files are accepted. "
            f"File '{filename}' does not match expected format."
        )

    doc_type = _classify_doc_type(raw_text)

    return state.model_copy(update={
        "raw_text": raw_text,
        "doc_type": doc_type,
    })
