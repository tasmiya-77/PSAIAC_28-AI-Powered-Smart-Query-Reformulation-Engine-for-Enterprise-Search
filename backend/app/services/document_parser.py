import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content to detect duplicate uploads."""
    return hashlib.sha256(content).hexdigest()


def extract_text_from_pdf(content: bytes) -> Tuple[str, int]:
    """Extract raw text and total page count from PDF bytes using pypdf."""
    import io
    from pypdf import PdfReader

    try:
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text_pages = []
        total_pages = len(reader.pages)

        if total_pages == 0:
            raise ValueError("PDF file has 0 pages.")

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_pages.append(f"--- Page {idx + 1} ---\n{page_text.strip()}")

        full_text = "\n\n".join(text_pages).strip()
        if not full_text:
            raise ValueError("No extractable text found in PDF document (may be scanned image or empty).")

        return full_text, total_pages
    except Exception as e:
        logger.error(f"[INGEST] Failed to extract text from PDF: {str(e)}")
        raise ValueError(f"Corrupted or invalid PDF file: {str(e)}") from e


def extract_text_from_docx(content: bytes) -> Tuple[str, int]:
    """Extract raw text and paragraph count from DOCX bytes using python-docx."""
    import io
    import docx

    try:
        docx_file = io.BytesIO(content)
        doc = docx.Document(docx_file)
        text_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]

        full_text = "\n\n".join(text_paragraphs).strip()
        if not full_text:
            raise ValueError("No extractable text found in DOCX document.")

        return full_text, max(1, len(text_paragraphs))
    except Exception as e:
        logger.error(f"[INGEST] Failed to extract text from DOCX: {str(e)}")
        raise ValueError(f"Corrupted or invalid DOCX file: {str(e)}") from e


def extract_text_and_metadata(
    filename: str, content: bytes
) -> Tuple[str, Dict[str, Any]]:
    """Extract text and metadata from PDF, DOCX, TXT, or Markdown files."""
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    file_hash = calculate_file_hash(content)
    upload_date = datetime.utcnow().isoformat() + "Z"
    file_size = len(content)

    total_units = 1
    if ext == "pdf":
        text, total_units = extract_text_from_pdf(content)
    elif ext in ["docx", "doc"]:
        text, total_units = extract_text_from_docx(content)
    else:
        # TXT or Markdown
        try:
            text = content.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="ignore").strip()

        if not text:
            raise ValueError("Uploaded text document is empty.")

    metadata = {
        "filename": filename,
        "file_type": ext,
        "file_size_bytes": file_size,
        "file_hash": file_hash,
        "upload_date": upload_date,
        "total_units": total_units,
    }

    logger.info(
        f"[INGEST] Extracted {len(text)} characters ({total_units} units) from '{filename}' (SHA256: {file_hash[:10]}...)"
    )
    return text, metadata


def split_text_into_chunks(
    text: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> List[str]:
    """
    Split text into semantic chunks using paragraph/sentence boundaries with sliding overlap.
    """
    if not text or not text.strip():
        return []

    clean_text = re.sub(r"\n{3,}", "\n\n", text).strip()
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]

    chunks: List[str] = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + p).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)

            if len(p) > chunk_size:
                # Split large paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", p)
                sub_chunk = ""
                for sent in sentences:
                    if len(sub_chunk) + len(sent) + 1 <= chunk_size:
                        sub_chunk = (sub_chunk + " " + sent).strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sent
                if sub_chunk:
                    # Apply overlap from previous chunk end if available
                    if chunks and chunk_overlap > 0:
                        overlap_prefix = chunks[-1][-chunk_overlap:]
                        current_chunk = (overlap_prefix + " " + sub_chunk).strip()
                    else:
                        current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                if chunks and chunk_overlap > 0:
                    overlap_prefix = chunks[-1][-chunk_overlap:]
                    current_chunk = (overlap_prefix + " " + p).strip()
                else:
                    current_chunk = p

    if current_chunk:
        chunks.append(current_chunk)

    logger.info(f"[INGEST] Created {len(chunks)} chunks (chunk_size={chunk_size}, overlap={chunk_overlap})")
    return chunks

