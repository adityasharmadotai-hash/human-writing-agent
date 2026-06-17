"""Extract plain text from uploaded files (PDF, DOCX, TXT)."""

import logging
from pathlib import Path
from typing import Optional
import io

logger = logging.getLogger(__name__)


def extract_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pdfplumber."""
    try:
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        raise ValueError(f"Could not read PDF: {e}") from e


def extract_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error("DOCX extraction failed: %s", e)
        raise ValueError(f"Could not read DOCX: {e}") from e


def extract_from_txt(file_bytes: bytes) -> str:
    """Decode a TXT file."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file — unknown encoding.")


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route extraction based on file extension."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return extract_from_pdf(file_bytes)
    elif suffix in (".docx", ".doc"):
        return extract_from_docx(file_bytes)
    elif suffix == ".txt":
        return extract_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
