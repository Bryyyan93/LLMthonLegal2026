from .catastro_libre import CatastroLibreClient
from .catastro_protegido import FakeProtectedClient


class CatastroClient:

    def __init__(self, modo="libre", certificado=None):
        self.modo = modo

        if modo == "libre":
            self.client = CatastroLibreClient()

        elif modo == "protegido":
            self.client = FakeProtectedClient(certificado=certificado)

        elif modo == "demo":
            self.client = FakeProtectedClient(certificado="demo")

        else:
            raise ValueError("Modo no válido")

    def consultar(self, rc, provincia=None, municipio=None):

        if self.modo == "libre":
            return self.client.consultar_por_rc(
                rc=rc,
                provincia=provincia,
                municipio=municipio
            )

        else:
            return self.client.service.Consulta_DNPBI(rc)
