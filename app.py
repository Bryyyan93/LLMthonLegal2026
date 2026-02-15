from shiny import App, ui, render, reactive
import os
import tempfile

from ocr import extract_text_by_pages, OCRExtractionError
from processor import process_multiple_invoices
from excel_export import export_invoices_to_excel


# ---------------------------
# UI
# ---------------------------

app_ui = ui.page_fluid(

    ui.h2("Procesamiento documental jurídico"),

    ui.layout_sidebar(

        ui.sidebar(

            ui.h4("Subida de documentos"),

            ui.input_file(
                "facturas",
                "Subir facturas (PDF / imágenes)",
                multiple=True,
                accept=[".pdf", ".png", ".jpg", ".jpeg"]
            ),

            ui.input_file(
                "escrituras",
                "Subir escrituras (PDF / imágenes)",
                multiple=True,
                accept=[".pdf", ".png", ".jpg", ".jpeg"]
            ),

            ui.br(),

            ui.input_action_button("procesar", "Procesar"),

            ui.br(),
            ui.br(),

            ui.download_button("download_excel", "Descargar Excel")
        ),

        ui.card(
            ui.card_header("Estado"),
            ui.output_text("status")
        )
    )
)


# ---------------------------
# SERVER
# ---------------------------

def server(input, output, session):

    estado = reactive.Value("Esperando documentos...")
    excel_path = reactive.Value(None)

    @reactive.effect
    @reactive.event(input.procesar)
    def procesar():

        estado.set("Iniciando procesamiento...")

        facturas_input = input.facturas()
        todas_las_facturas = []

        if not facturas_input:
            estado.set("No se han subido facturas.")
            return

        for fileinfo in facturas_input:

            path = fileinfo["datapath"]
            nombre = fileinfo["name"]

            try:
                estado.set(f"Procesando {nombre}...")

                # 1️⃣ OCR por páginas
                pages = extract_text_by_pages(path)

                # 2️⃣ Procesamiento estructurado
                facturas = process_multiple_invoices(pages)

                todas_las_facturas.extend(facturas)

            except OCRExtractionError as e:
                estado.set(f"Error OCR en {nombre}: {e}")
                return
            except Exception as e:
                estado.set(f"Error procesando {nombre}: {e}")
                return

        if not todas_las_facturas:
            estado.set("No se extrajeron facturas.")
            return

        # 3️⃣ Exportar Excel
        tmp_dir = tempfile.gettempdir()
        output_file = os.path.join(tmp_dir, "resultado.xlsx")

        export_invoices_to_excel(todas_las_facturas, output_file)

        excel_path.set(output_file)

        estado.set(f"Proceso finalizado. Facturas procesadas: {len(todas_las_facturas)}")


    @output
    @render.text
    def status():
        return estado.get()


    @output
    @render.download(filename="resultado.xlsx")
    def download_excel():

        path = excel_path.get()

        if path and os.path.exists(path):
            with open(path, "rb") as f:
                yield f.read()


app = App(app_ui, server)
