class FakeProtectedService:
    def Consulta_DNPBI(self, rc):
            return {
                "consulta_dnpbi": {
                    "control": {"cuerr": "0"},
                    "bico": {
                        "bi": {
                            "idbi": {
                                "rc": rc
                            },
                            "dt": {
                                "ldt": "CR LLIRIA 116 46100 BURJASSOT (VALENCIA)",
                                "luso": "Ocio y Hosteleria",
                                "sfc": "851",
                                "ant": "1999"
                            },
                            "titularidad": {
                                "titular": {
                                    "nombre": "CLIENTE DEMO S.L.",
                                    "nif": "B12345678",
                                    "porcentaje": "100%"
                                }
                            },
                            "valor_catastral": {
                                "importe": "1.250.000",
                                "ejercicio": "2024"
                            }
                        }
                    }
                }
            }

class FakeProtectedClient:

    def __init__(self, certificado=None):
        if not certificado:
            raise Exception("Certificado requerido")
        self.service = FakeProtectedService()
