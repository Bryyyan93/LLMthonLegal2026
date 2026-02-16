from shiny import ui, App, render, reactive
import pandas as pd
import os
import tempfile

from ocr import extract_text_by_pages, OCRExtractionError
from envoice_processor import process_multiple_invoices
from envoice_excel_export import export_invoices_to_excel


# ---------------------------
# UI
# ---------------------------
app_ui = ui.page_fluid(
    ui.h2("Procesamiento documental jurídico"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Facturas"),
            ui.input_file(
                "facturas",
                "Subir facturas (PDF / imágenes)",
                multiple=True,
                accept=[".pdf", ".png", ".jpg", ".jpeg"]
            ),

            ui.input_action_button("procesar_facturas", "Procesar facturas"),
            ui.output_ui("descargar_facturas_ui"),
            ui.hr(),
            ui.h4("Escrituras"),
            ui.input_file(
                "escrituras",
                "Subir escrituras (PDF / imágenes)",
                multiple=True,
                accept=[".pdf", ".png", ".jpg", ".jpeg"]
            ),

            ui.input_action_button("procesar_escrituras", "Procesar escrituras"),
            ui.output_ui("descargar_escrituras_ui")
        ),

        ui.div(
            ui.output_ui("estado_valuebox"),
            ui.br(),
            ui.card(
                ui.card_header("Resultado"),
                ui.output_data_frame("tabla_resultado")
            )
        )
    )
)

# ---------------------------
# SERVER
# ---------------------------

def server(input, output, session):
    estado = reactive.Value("esperando")
    df_facturas = reactive.Value(None)
    excel_facturas_path = reactive.Value(None)

    df_escrituras = reactive.Value(None)
    excel_escrituras_path = reactive.Value(None)

    # -----------------------
    # VALUE BOX
    # -----------------------
    @output
    @render.ui
    def estado_valuebox():

        estado_actual = estado.get()

        if estado_actual == "esperando":
            color = "secondary"
            texto = "Esperando documentos..."
        elif estado_actual == "procesando":
            color = "primary"
            texto = "Procesando..."
        else:
            color = "success"
            texto = "Finalizado"

        return ui.value_box(
            title="Estado",
            value=texto,
            theme=color
        )

    # -----------------------
    # PROCESAR FACTURAS
    # -----------------------
    @reactive.effect
    @reactive.event(input.procesar_facturas)
    def procesar_facturas():

        archivos = input.facturas()
        if not archivos:
            return

        estado.set("procesando")

        todas = []

        for fileinfo in archivos:
            path = fileinfo["datapath"]
            nombre = fileinfo["name"]

            try:
                pages = extract_text_by_pages(path)
                facturas = process_multiple_invoices(pages)

                for f in facturas:
                    f["archivo_origen"] = nombre

                todas.extend(facturas)

            except OCRExtractionError as e:
                estado.set(f"Error OCR: {e}")
                return

        if not todas:
            estado.set("esperando")
            return

        df = pd.DataFrame(todas)
        df_facturas.set(df)

        tmp_dir = tempfile.gettempdir()
        output_file = os.path.join(tmp_dir, "facturas.xlsx")

        export_invoices_to_excel(todas, output_file)

        excel_facturas_path.set(output_file)

        estado.set("finalizado")

    # -----------------------
    # TABLA RESULTADO
    # -----------------------
    @output
    @render.data_frame
    def tabla_resultado():

        df = df_facturas.get()
        if df is not None:
            return df

        df2 = df_escrituras.get()
        if df2 is not None:
            return df2

        return pd.DataFrame()

    # -----------------------
    # BOTÓN DESCARGA FACTURAS
    # -----------------------
    @output
    @render.ui
    def descargar_facturas_ui():

        if excel_facturas_path.get() is not None:
            return ui.download_button(
                "download_facturas",
                "Descargar Excel facturas"
            )

        return ui.div()

    @output
    @render.download(filename="facturas.xlsx")
    def download_facturas():

        path = excel_facturas_path.get()

        if path and os.path.exists(path):
            with open(path, "rb") as f:
                yield f.read()

app = App(app_ui, server)
