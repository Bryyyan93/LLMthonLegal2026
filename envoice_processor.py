"""
processor.py

Módulo de procesamiento para:
- Ejecutar la extracción de facturas usando extract_invoice (NO modificar).
- Limpiar la respuesta del modelo.
- Convertir a JSON seguro.
- Validar estructura obligatoria.
- Verificar tipos numéricos.
- Manejar errores de forma controlada.

Preparado para ser importado desde app.py.
"""

import json
import re
from typing import Dict, Any

from llm_extractor import extract_invoice


# Campos obligatorios definidos por contrato con el modelo
REQUIRED_FIELDS = [
   # "numero_orden", -> quitamos numero de orden (no esta en la factura, lo asignamos nosotros)
    "numero_factura",
    "fecha",
    "cif",
    "proveedor",
    "comunidad_autonoma",
    "articulo",
    "cantidad",
]


class InvoiceProcessingError(Exception):
    """Excepción base para errores de procesamiento de factura."""
    pass


class InvalidJSONError(InvoiceProcessingError):
    """Error cuando la respuesta del modelo no contiene JSON válido."""
    pass


class MissingFieldsError(InvoiceProcessingError):
    """Error cuando faltan campos obligatorios."""
    pass


class InvalidAmountError(InvoiceProcessingError):
    """Error cuando el campo cantidad no es numérico."""
    pass


def extract_json_block(text: str) -> str:
    """
    Extrae bloque JSON ya sea array [...] o objeto {...}
    """
    if not text:
        raise InvalidJSONError("Respuesta vacía del modelo.")

    text = text.strip()

    # Si empieza por array, devolver desde primer [ hasta último ]
    if text.startswith("["):
        start = text.find("[")
        end = text.rfind("]")
    else:
        start = text.find("{")
        end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise InvalidJSONError("No se encontró un bloque JSON válido.")

    return text[start:end + 1]


def parse_model_response(response_text: str):

    if not response_text:
        raise InvalidJSONError("Respuesta vacía del modelo.")

    cleaned = response_text.strip()

    # Eliminar bloques markdown ```json ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned)
        cleaned = cleaned.rstrip("`").strip()

    # Extraer bloque JSON (array u objeto)
    json_block = extract_json_block(cleaned)

    try:
        data = json.loads(json_block)
    except json.JSONDecodeError as e:
        raise InvalidJSONError(f"JSON inválido: {str(e)}")

    # Si devuelve objeto único, convertir en lista
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        raise InvalidJSONError("La respuesta no es un array JSON válido.")

    return data



def validate_required_fields(data: Dict[str, Any]) -> None:
    """
    Verifica que el JSON contenga todos los campos obligatorios.
    """
    missing = [field for field in REQUIRED_FIELDS if field not in data]

    if missing:
        raise MissingFieldsError(
            f"Faltan campos obligatorios: {', '.join(missing)}"
        )


def validate_amount_field(data: Dict[str, Any]) -> None:
    """
    Verifica que el campo 'cantidad' sea numérico o null.
    """
    amount = data.get("cantidad")

    if amount is None:
        return

    if not isinstance(amount, (int, float)):
        raise InvalidAmountError(
            "El campo 'cantidad' debe ser numérico o null."
        )


def normalize_data_types(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza tipos básicos si fuese necesario.
    Convierte strings numéricos a float en el campo cantidad.
    """
    amount = data.get("cantidad")

    if isinstance(amount, str):
        # Limpia posibles espacios o separadores
        cleaned = re.sub(r"[^\d.,-]", "", amount)
        cleaned = cleaned.replace(",", ".")

        try:
            data["cantidad"] = float(cleaned)
        except ValueError:
            raise InvalidAmountError(
                "No se pudo convertir 'cantidad' a número."
            )

    return data


def process_invoice_text(text: str) -> Dict[str, Any]:
    raw_response = extract_invoice(text)

    parsed_list = parse_model_response(raw_response)

    validated_items = []

    for item in parsed_list:
        item = normalize_data_types(item)
        validate_required_fields(item)
        validate_amount_field(item)
        validated_items.append(item)

    return validated_items

from typing import List


def process_multiple_invoices(pages_text: List[str]) -> List[Dict[str, Any]]:
    invoices = []
    global_counter = 1  # numeración real por línea

    for page_index, page_text in enumerate(pages_text, start=1):

        if not page_text.strip():
            continue

        try:
            invoice_items = process_invoice_text(page_text)

            for item in invoice_items:
                item["numero_orden"] = global_counter
                invoices.append(item)
                global_counter += 1

        except InvoiceProcessingError as e:
            print(f"Error en página {page_index}: {e}")
            continue

    return invoices
