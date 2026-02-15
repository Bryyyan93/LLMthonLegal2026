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

from llm_client import extract_invoice


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
    Extrae únicamente el bloque JSON comprendido entre la primera '{'
    y la última '}'.

    Maneja casos donde el modelo devuelve texto adicional.
    """
    if not text:
        raise InvalidJSONError("Respuesta vacía del modelo.")

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise InvalidJSONError("No se encontró un bloque JSON válido.")

    return text[start:end + 1]


def parse_model_response(response_text: str) -> Dict[str, Any]:
    """
    Convierte la respuesta del modelo en un diccionario Python.

    - Extrae únicamente el bloque JSON.
    - Intenta decodificar con json.loads.
    - Lanza error controlado si falla.
    """
    json_block = extract_json_block(response_text)

    try:
        return json.loads(json_block)
    except json.JSONDecodeError as e:
        raise InvalidJSONError(f"JSON inválido: {str(e)}")


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
    """
    Flujo completo de procesamiento:

    1. Llama a extract_invoice (NO modificada).
    2. Extrae y parsea JSON.
    3. Normaliza tipos.
    4. Valida estructura obligatoria.
    5. Valida campo numérico.
    6. Devuelve diccionario limpio y validado.

    Esta función es la que debe ser llamada desde app.py.
    """
    raw_response = extract_invoice(text)

    parsed_data = parse_model_response(raw_response)

    parsed_data = normalize_data_types(parsed_data)

    validate_required_fields(parsed_data)

    validate_amount_field(parsed_data)

    return parsed_data

from typing import List


def process_multiple_invoices(pages_text: List[str]) -> List[Dict[str, Any]]:
    """
    Procesa múltiples facturas (una por página).

    Recibe:
        Lista de textos (uno por página).

    Devuelve:
        Lista de diccionarios validados listos para exportación.
    """

    invoices = []

    for index, page_text in enumerate(pages_text, start=1):
        if not page_text.strip():
            continue  # Saltar páginas vacías

        try:
           # Procesar factura individual
            invoice_data = process_invoice_text(page_text)

            #AQUÍ va el número de orden
            invoice_data["numero_orden"] = index

            #Añadir a la lista final
            invoices.append(invoice_data)

        except InvoiceProcessingError as e:
            # Puedes decidir:
            # - Saltar factura
            # - Loguear error
            # - O añadir registro de error estructurado
            print(f"Error en página {index}: {e}")
            continue

    return invoices
