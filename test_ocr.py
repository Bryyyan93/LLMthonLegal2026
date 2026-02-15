from ocr import extract_text, OCRExtractionError
from llm_client import extract_invoice
from processor import process_invoice_text

def test_file(path):
    try:
        text = extract_text(path)
        print("\n--- TEXTO EXTRAÍDO ---\n")
        print(text[:1000])  # Mostrar solo primeros 1000 caracteres
        print("\nLongitud total:", len(text))
        return text
    except OCRExtractionError as e:
        print("Error OCR:", e)

if __name__ == "__main__":
    print("Cargar el fichero")
    text = test_file("./data/PRUEBA 1.pdf")   # Cambia por tu archivo
    print(text)
    print("Extraer datos")
    resultado = extract_invoice(text)
    print(resultado)
    print("Procesar")
    processor = process_invoice_text(resultado)
    print(processor)
