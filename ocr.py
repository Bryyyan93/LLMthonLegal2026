
# ocr.py
# Módulo encargado exclusivamente de extracción de texto por página

#####Ojo, esto no funciona si la factura ocupa dos paginas o hay dos facturas en una misma página####

import re
from typing import List

import pdfplumber
import pytesseract
from PIL import Image


SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
SUPPORTED_PDF_EXTENSIONS = (".pdf",)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OCRExtractionError(Exception):
    """Custom exception for OCR extraction errors."""
    pass


# -------------------------------------------------
# TEXT CLEANING
# -------------------------------------------------
def clean_text(text: str) -> str:
    """
    Clean extracted text:
    - Normalize line endings
    - Remove duplicated spaces
    - Remove excessive blank lines
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


# -------------------------------------------------
# FILE TYPE HELPERS
# -------------------------------------------------
def is_pdf(file_path: str) -> bool:
    return file_path.lower().endswith(SUPPORTED_PDF_EXTENSIONS)


def is_image(file_path: str) -> bool:
    return file_path.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)


# -------------------------------------------------
# PAGE-LEVEL EXTRACTION (MULTI-FACTURA CORE)
# -------------------------------------------------

def _extract_page_text(page) -> str:
    """
    Extract text from a single pdfplumber page.
    Try text layer first, fallback to OCR if needed.
    """
    text = page.extract_text()

    # Fallback to OCR if text layer is empty or too short
    if not text or len(text.strip()) < 20:
        pil_image = page.to_image(resolution=300).original
        text = pytesseract.image_to_string(pil_image)

    return clean_text(text)


def extract_text_by_pages(file_path: str) -> List[str]:
    """
    Main function for multi-page extraction.

    Returns:
        List[str] -> One cleaned text string per page.
    """

    if not file_path:
        raise OCRExtractionError("File path is empty.")

    if is_pdf(file_path):
        return _extract_pdf_by_pages(file_path)

    elif is_image(file_path):
        # Image = single "page"
        text = _extract_image(file_path)
        return [clean_text(text)]

    else:
        raise OCRExtractionError("Unsupported file type.")


# -------------------------------------------------
# PDF HANDLING
# -------------------------------------------------
def _extract_pdf_by_pages(file_path: str) -> List[str]:
    pages_text = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = _extract_page_text(page)
                pages_text.append(text)

    except Exception as e:
        raise OCRExtractionError(f"Error extracting PDF: {e}")

    return pages_text


# -------------------------------------------------
# IMAGE HANDLING
# -------------------------------------------------
def _extract_image(file_path: str) -> str:
    try:
        with Image.open(file_path) as img:
            text = pytesseract.image_to_string(img)
            return text or ""
    except Exception as e:
        raise OCRExtractionError(f"Error performing OCR on image: {e}")
