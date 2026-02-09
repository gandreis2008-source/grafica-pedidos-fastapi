from PyPDF2 import PdfReader
from docx import Document


def contar_paginas_pdf(caminho: str) -> int:
    try:
        reader = PdfReader(caminho)
        return len(reader.pages)
    except Exception as e:
        raise ValueError(f"Erro ao ler PDF: {e}")


def contar_paginas_docx(caminho: str) -> int:
    # MVP: estimativa
    try:
        doc = Document(caminho)
        total_paragrafos = len(doc.paragraphs)
        return max(1, total_paragrafos // 30 + 1)
    except Exception as e:
        raise ValueError(f"Erro ao ler DOCX: {e}")
