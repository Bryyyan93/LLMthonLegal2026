from ocr import extract_text_by_pages, OCRExtractionError
from llm_client import extract_invoice
from processor import process_multiple_invoices
from excel_export import export_invoices_to_excel


def test_file(path):
    try:
        pages = extract_text_by_pages(path)

        print("\n--- PÁGINAS EXTRAÍDAS ---")
        print("Número de páginas:", len(pages))

        for i, page in enumerate(pages, start=1):
            print(f"\n--- Página {i} ---")
            print(page[:500])  # primeros 500 caracteres

        return pages

    except OCRExtractionError as e:
        print("Error OCR:", e)

if __name__ == "__main__":
    print("Cargar el fichero")

    pages = test_file("./data/PRUEBA 1.pdf")

    print("\nProcesar facturas...")
    facturas = process_multiple_invoices(pages)

    print("\nResultado estructurado:")
    for factura in facturas:
        print(factura)


# Exportar a Excel
export_invoices_to_excel(facturas, "resultado.xlsx")