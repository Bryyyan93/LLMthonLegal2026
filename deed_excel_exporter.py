"""
deed_excel_exporter.py

Generador de Excel para escrituras.
"""

from typing import Dict, Any, List
from openpyxl import Workbook
from openpyxl.styles import Font


EXCEL_COLUMNS = [
    ("numero_escritura", "Nº ESCRITURA"),
    ("tipo", "TIPO"),
    ("descripcion", "DESCRIPCIÓN"),
    ("referencia_catastral", "REFERENCIA CATASTRAL"),
]


class ExcelExportError(Exception):
    """Error durante la generación del Excel."""
    pass


def flatten_deed(deed_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convierte la estructura jerárquica de escritura
    en una lista plana de filas.
    """

    rows = []

    numero = deed_result.get("numero_escritura")
    tipo = deed_result.get("tipo")

    for inmueble in deed_result.get("inmuebles", []):
        descripcion = inmueble.get("descripcion")
        refs = inmueble.get("referencias_catastrales", [])

        if not refs:
            rows.append({
                "numero_escritura": numero,
                "tipo": tipo,
                "descripcion": descripcion,
                "referencia_catastral": None
            })
        else:
            for ref in refs:
                rows.append({
                    "numero_escritura": numero,
                    "tipo": tipo,
                    "descripcion": descripcion,
                    "referencia_catastral": ref
                })

    return rows


def export_deeds_to_excel(
    deed_result: Dict[str, Any],
    output_path: str
) -> None:

    rows = flatten_deed(deed_result)

    if not rows:
        raise ExcelExportError("No hay datos para exportar.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Escrituras"

    # Cabecera
    for col_index, (_, column_title) in enumerate(EXCEL_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_index)
        cell.value = column_title
        cell.font = Font(bold=True)

    # Filas
    for row_index, row in enumerate(rows, start=2):
        for col_index, (field_key, _) in enumerate(EXCEL_COLUMNS, start=1):
            ws.cell(
                row=row_index,
                column=col_index,
                value=row.get(field_key)
            )

    # Ajuste ancho
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[column].width = max_length + 2

    try:
        wb.save(output_path)
    except Exception as e:
        raise ExcelExportError(f"Error guardando Excel: {e}")
