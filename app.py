from shiny import ui, App, render, reactive
import pandas as pd
import os
import tempfile
import logging
import traceback

from ocr import extract_text_by_pages, OCRExtractionError
from envoice_processor import process_multiple_invoices
from envoice_excel_export import export_invoices_to_excel
from deed_validator import process_deed
from deed_excel_exporter import export_deeds_to_excel, flatten_deed
from catastro_demo.catastro_client import CatastroClient

logging.basicConfig(
    level=logging.INFO,  # DEBUG se quiere más detalle
    format="%(levelname)s : %(asctime)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ---------------------------
# UI
# ---------------------------
app_ui = ui.page_fluid(
    ui.div(
        ui.img(
            src="logo.png",
            style="max-height:70px;"
        ),
        style="margin-bottom:20px;"
    ),
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
            ui.output_ui("descargar_escrituras_ui"),
            width=400
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

    catastro_state = reactive.Value("")

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

        logger.info("Inicio procesamiento de factura")
        for fileinfo in archivos:
            path = fileinfo["datapath"]
            nombre = fileinfo["name"]

            try:
                pages = extract_text_by_pages(path)
                logger.info("OCR completado")
                facturas = process_multiple_invoices(pages)
                logger.info("Extracción LLM completada")

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
        logger.info("Procesamiento finalizado")
        estado.set("finalizado")

    # -----------------------
    # PROCESAR ESCRITURAS
    # -----------------------
    # flujo
    # 1 PDF → 1 estructura → 1 Excel
    @reactive.effect
    @reactive.event(input.procesar_escrituras)
    def procesar_escrituras():
        archivos = input.escrituras()
        if not archivos:
            return

        estado.set("procesando")

        fileinfo = archivos[0]  # SOLO uno
        path = fileinfo["datapath"]
        nombre = fileinfo["name"]

        pages = extract_text_by_pages(path)

        result = process_deed(pages)

        result["archivo_origen"] = nombre

        df = pd.DataFrame(flatten_deed(result))  # opcional para mostrar tabla
        df_escrituras.set(df)

        tmp_dir = tempfile.gettempdir()
        output_file = os.path.join(tmp_dir, "escritura.xlsx")

        export_deeds_to_excel(result, output_file)

        excel_escrituras_path.set(output_file)

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

    # -----------------------
    # BOTÓN DESCARGA ESCRITURAS
    # -----------------------
    @output
    @render.ui
    def descargar_escrituras_ui():
        if excel_escrituras_path.get() is not None:
            return ui.layout_columns(
                ui.download_button(
                    "download_escrituras",
                    "Descargar Excel escrituras",
                    width="100%"
                ),
                ui.input_action_button(
                    "abrir_catastro",
                    "Obtener Catastro",
                    width="100%"
                ),
                col_widths=[6, 6]
            )
        return ui.div()

    @output
    @render.download(filename="escrituras.xlsx")
    def download_escrituras():

        path = excel_escrituras_path.get()

        if path and os.path.exists(path):
            with open(path, "rb") as f:
                yield f.read()

    def obtener_rc_disponibles():
        df = df_escrituras.get()
        if df is None:
            return []
        if "referencia_catastral" not in df.columns:
            return []
        return sorted(df["referencia_catastral"].dropna().unique().tolist())

    @reactive.effect
    @reactive.event(input.abrir_catastro)
    def abrir_modal_catastro():
        catastro_state.set("")

        ui.modal_show(
            ui.modal(
                ui.h4("Consulta Catastro"),

                ui.navset_tab(

                    # =========================
                    # TAB CONSULTA LIBRE
                    # =========================
                    ui.nav_panel(
                        "Consulta libre",

                        ui.input_text("rc_manual_libre", "Referencia Catastral"),

                        ui.input_action_button(
                            "mostrar_rc_libre",
                            "Mostrar RC del documento"
                        ),

                        ui.output_ui("selector_rc_libre"),

                        ui.input_text("provincia", "Provincia"),
                        ui.input_text("municipio", "Municipio"),

                        ui.hr(),
                        ui.input_action_button("consulta_libre", "Ejecutar consulta"),
                    ),

                    # =========================
                    # TAB CONSULTA PROTEGIDA
                    # =========================
                    ui.nav_panel(
                        "Consulta protegida",

                        ui.input_text("rc_manual_protegida", "Referencia Catastral"),

                        ui.input_action_button(
                            "mostrar_rc_protegida",
                            "Mostrar RC del documento"
                        ),

                        ui.output_ui("selector_rc_protegida"),

                        ui.input_file(
                            "certificado_digital",
                            "Subir certificado digital (.pem)",
                            accept=[".pem"]
                        ),

                        ui.hr(),
                        ui.input_action_button("consulta_protegida", "Ejecutar consulta"),
                    ),
                ),

                ui.hr(),
                ui.output_ui("resultado_catastro"),

                easy_close=True,
                size="l"
            )
        )

    @output
    @render.ui
    def selector_rc_libre():
        if input.mostrar_rc_libre() is None:
            return ui.div()

        rc_list = obtener_rc_disponibles()

        if not rc_list:
            return ui.div("No se han detectado referencias catastrales.")

        return ui.input_select(
            "rc_select_libre",
            "Seleccionar RC detectada",
            choices=rc_list
        )

    @output
    @render.ui
    def selector_rc_protegida():
        if input.mostrar_rc_protegida() is None:
            return ui.div()

        rc_list = obtener_rc_disponibles()

        if not rc_list:
            return ui.div("No se han detectado referencias catastrales.")

        return ui.input_select(
            "rc_select_protegida",
            "Seleccionar RC detectada",
            choices=rc_list
        )

    @reactive.effect
    @reactive.event(input.consulta_libre)
    def ejecutar_consulta_libre():
        try:
            rc = input.rc_manual_libre()

            # Leer selector dinámico sin romper
            try:
                rc_select = reactive.isolate(input.rc_select_libre())
                if rc_select:
                    rc = rc_select
            except:
                pass

            if not rc:
                catastro_state.set("Debe indicar una referencia catastral.")
                return

            provincia = input.provincia()
            municipio = input.municipio()

            if not provincia or not municipio:
                catastro_state.set("Provincia y municipio son obligatorios.")
                return

            cliente = CatastroClient(modo="libre")

            resultado = cliente.consultar(
                rc=rc,
                provincia=provincia.upper(),
                municipio=municipio.upper()
            )

            catastro_state.set(resultado)

        except Exception as e:
            catastro_state.set(str(e))



    @reactive.effect
    @reactive.event(input.consulta_protegida)
    def ejecutar_consulta_protegida():

        try:
            rc = input.rc_manual_protegida()

            # Intentar usar selector dinámico si existe
            try:
                rc_select = reactive.isolate(input.rc_select_protegida())
                if rc_select:
                    rc = rc_select
            except:
                pass

            if not rc:
                catastro_state.set("Debe indicar una referencia catastral.")
                return

            # Validar certificado
            cert_files = input.certificado_digital()

            if not cert_files:
                catastro_state.set("Debe subir un certificado digital (.pem).")
                return

            cert_path = cert_files[0]["datapath"]

            cliente = CatastroClient(
                modo="protegido",
                certificado=cert_path
            )

            resultado = cliente.consultar(rc=rc)

            catastro_state.set(resultado)

        except Exception as e:
            catastro_state.set(f"Error consulta protegida: {str(e)}")

    @output
    @render.ui
    def resultado_catastro():

        data = catastro_state.get()

        if not data:
            return ui.div()

        if isinstance(data, str):
            return ui.pre(data)

        if isinstance(data, dict) and "error" in data:
            return ui.card(
                ui.card_header("Error en consulta"),
                ui.p(data["error"], style="color:#dc3545; font-weight:500;")
            )

        try:

            # =================================================
            # CONSULTA LIBRE (ya viene formateada)
            # =================================================
            if isinstance(data, dict) and data.get("tipo") == "libre":

                lista_construcciones = ui.tags.ul(
                    *[
                        ui.tags.li(
                            f"{c.get('tipo','-')} – {c.get('superficie','-')} m²"
                        )
                        for c in data.get("construcciones", [])
                    ]
                ) if data.get("construcciones") else ui.p("No constan construcciones.")

                return ui.card(

                    ui.card_header("Ficha Catastral"),

                    ui.h4(data.get("direccion") or "Dirección no disponible"),
                    ui.p(
                        f"{data.get('municipio','-')} "
                        f"({data.get('provincia','-')})",
                        style="color:gray;"
                    ),

                    ui.hr(),

                    ui.layout_columns(
                        ui.div(
                            ui.p("Referencia Catastral", style="font-weight:500;"),
                            ui.p(data.get("referencia_catastral","-"))
                        ),
                        ui.div(
                            ui.p("Uso principal", style="font-weight:500;"),
                            ui.p(data.get("uso") or "-")
                        ),
                        col_widths=[6,6]
                    ),

                    ui.layout_columns(
                        ui.div(
                            ui.p("Superficie total", style="font-weight:500;"),
                            ui.p(f"{data.get('superficie_total') or '-'} m²")
                        ),
                        ui.div(
                            ui.p("Año construcción", style="font-weight:500;"),
                            ui.p(data.get("anio_construccion") or "-")
                        ),
                        col_widths=[6,6]
                    ),

                    ui.p(
                        f"Participación: {data.get('porcentaje_participacion') or '-'}",
                        style="color:gray;"
                    ),

                    ui.hr(),

                    ui.h5("Construcciones"),
                    lista_construcciones
                )

            # =================================================
            # CONSULTA PROTEGIDA (estructura cruda)
            # =================================================
            if isinstance(data, dict) and "consulta_dnpbi" in data:

                bi = data["consulta_dnpbi"]["bico"]["bi"]

                titular = bi.get("titularidad", {}).get("titular", {})
                valor = bi.get("valor_catastral", {})
                dt = bi.get("dt", {})

                return ui.card(

                    ui.card_header("Ficha Catastral Protegida"),

                    ui.h3(
                        f"{valor.get('importe','-')} €",
                        style="color:#0d6efd; margin-bottom:0;"
                    ),
                    ui.p(
                        f"Valor catastral · Ejercicio {valor.get('ejercicio','-')}",
                        style="color:gray;"
                    ),

                    ui.hr(),

                    ui.layout_columns(
                        ui.div(
                            ui.p("Referencia Catastral", style="font-weight:500;"),
                            ui.p(bi.get("idbi", {}).get("rc","-"))
                        ),
                        ui.div(
                            ui.p("Uso principal", style="font-weight:500;"),
                            ui.p(dt.get("luso","-"))
                        ),
                        col_widths=[6,6]
                    ),

                    ui.layout_columns(
                        ui.div(
                            ui.p("Superficie total", style="font-weight:500;"),
                            ui.p(f"{dt.get('sfc','-')} m²")
                        ),
                        ui.div(
                            ui.p("Año construcción", style="font-weight:500;"),
                            ui.p(dt.get("ant","-"))
                        ),
                        col_widths=[6,6]
                    ),

                    ui.hr(),

                    ui.h5("Titularidad"),

                    ui.p(f"Titular: {titular.get('nombre','-')}"),
                    ui.p(f"NIF: {titular.get('nif','-')}"),
                    ui.p(f"Participación: {titular.get('porcentaje','-')}")
                )

            return ui.pre(str(data))

        except Exception as e:
            return ui.pre(f"Error renderizando resultado: {str(e)}")



app = App(
    app_ui,
    server,
    static_assets=os.path.join(os.path.dirname(__file__), "docs")
)
