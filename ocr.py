# Extraer los datos desde PDF o imagen
import re
from typing import Optional

import pdfplumber
import pytesseract
from PIL import Image


SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
SUPPORTED_PDF_EXTENSIONS = (".pdf",)


class OCRExtractionError(Exception):
    """Custom exception for OCR extraction errors."""
    pass


def clean_text(text: str) -> str:
    """
    Perform basic text cleaning:
    - Remove duplicated spaces
    - Remove excessive newlines
    - Strip leading/trailing whitespace
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove duplicated spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def extract_text_from_pdf_text_layer(file_path: str) -> str:
    """
    Extract text directly from a PDF text layer using pdfplumber.
    """
    extracted_text = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
    except Exception as e:
        raise OCRExtractionError(f"Error extracting text from PDF: {e}")

    return "\n".join(extracted_text)


def extract_text_from_pdf_ocr(file_path: str) -> str:
    """
    Convert PDF pages to images and apply OCR using pytesseract.
    """
    extracted_text = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                pil_image = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(pil_image)
                if text:
                    extracted_text.append(text)
    except Exception as e:
        raise OCRExtractionError(f"Error performing OCR on PDF: {e}")

    return "\n".join(extracted_text)


def extract_text_from_image(file_path: str) -> str:
    """
    Apply OCR to an image file (jpg, jpeg, png).
    """
    try:
        with Image.open(file_path) as img:
            text = pytesseract.image_to_string(img)
    except Exception as e:
        raise OCRExtractionError(f"Error performing OCR on image: {e}")

    return text or ""


def is_pdf(file_path: str) -> bool:
    return file_path.lower().endswith(SUPPORTED_PDF_EXTENSIONS)


def is_image(file_path: str) -> bool:
    return file_path.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)


def extract_text(file_path: str) -> str:
    """
    Main entry point for text extraction from invoices.

    - If PDF:
        1) Try extracting from text layer.
        2) If no meaningful text found, fallback to OCR.
    - If image:
        Apply OCR.
    """
    if not file_path:
        raise OCRExtractionError("File path is empty.")

    if is_pdf(file_path):
        text = extract_text_from_pdf_text_layer(file_path)

        # If text layer is empty or too short, fallback to OCR
        if not text or len(text.strip()) < 20:
            text = extract_text_from_pdf_ocr(file_path)

    elif is_image(file_path):
        text = extract_text_from_image(file_path)

    else:
        raise OCRExtractionError("Unsupported file type.")

    return clean_text(text)
