from pathlib import Path

from pypdf import PdfReader


def extract_text(file_path: Path) -> str:
    """File se plain text nikaalta hai (PDF ya TXT)."""
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    raise ValueError(f"Unsupported file type: {suffix}. Only .pdf and .txt allowed.")
