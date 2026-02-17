from pycatastro import PyCatastro


class CatastroLibreClient:

    def __init__(self):
        self.client = PyCatastro()

    def consultar_por_rc(self, rc, provincia=None, municipio=None):
        raw = self.client.Consulta_DNPRC(
            provincia=provincia,
            municipio=municipio,
            rc=rc
        )

        return self._formatear_respuesta(raw)

    # -------------------------
    # FORMATEO COMPLETO AQUÍ
    # -------------------------
    def _formatear_respuesta(self, data):

        if not data or "consulta_dnp" not in data:
            return {"error": "No se pudo obtener información del inmueble"}

        try:
            bi = data["consulta_dnp"]["bico"]["bi"]

            # dt contiene provincia/municipio
            dt = bi.get("dt", {})

            provincia = dt.get("np")
            municipio = dt.get("nm")

            # OJO: ldt y debi están al mismo nivel que dt
            direccion = bi.get("ldt")

            debi = bi.get("debi", {})

            uso = debi.get("luso")
            superficie_total = debi.get("sfc")
            anio = debi.get("ant")
            porcentaje = debi.get("cpt")

            # Referencia catastral completa
            rc_data = bi.get("idbi", {}).get("rc", {})

            rc_completa = (
                rc_data.get("pc1", "")
                + rc_data.get("pc2", "")
                + rc_data.get("car", "")
                + rc_data.get("cc1", "")
                + rc_data.get("cc2", "")
            )

            # Construcciones
            # Construcciones (OJO: están en bico, no en bi)
            bico = data["consulta_dnp"]["bico"]
            construcciones_raw = bico.get("lcons", {}).get("cons", [])

            if isinstance(construcciones_raw, dict):
                construcciones_raw = [construcciones_raw]

            construcciones = []
            for c in construcciones_raw:
                construcciones.append({
                    "tipo": c.get("lcd"),
                    "superficie": c.get("dfcons", {}).get("stl")
                })

            return {
                "tipo": "libre",
                "direccion": direccion,
                "provincia": provincia,
                "municipio": municipio,
                "referencia_catastral": rc_completa,
                "uso": uso,
                "superficie_total": superficie_total,
                "anio_construccion": anio,
                "porcentaje_participacion": porcentaje,
                "construcciones": construcciones
            }

        except Exception as e:
            return {"error": f"Error formateando respuesta: {str(e)}"}


