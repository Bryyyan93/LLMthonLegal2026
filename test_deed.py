from ocr import extract_text_by_pages
from deed_validator import process_deed
from deed_excel_exporter import export_deeds_to_excel

def test_deed(path):
    text = extract_text_by_pages(path)
    result = process_deed(text)

    export_deeds_to_excel(result, "resultado_escritura.xlsx")
    print("Excel generado correctamente.")

    import pprint
    pprint.pprint(result)

if __name__ == "__main__":
    test_deed("data/ESCRITURA.pdf")