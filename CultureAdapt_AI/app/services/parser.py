from pathlib import Path
import fitz
from docx import Document


def extract_pdf_text(path: str) -> str:
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(p for p in pages if p.strip())


def extract_docx_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        return extract_pdf_text(path)
    if ext == ".docx":
        return extract_docx_text(path)
    if ext == ".txt":
        return Path(path).read_text(encoding="utf-8")

    raise ValueError(f"Unsupported file type: {ext}")
