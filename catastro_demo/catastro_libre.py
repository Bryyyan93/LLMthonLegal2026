from pycatastro import PyCatastro


class CatastroLibreClient:

    def __init__(self):
        self.client = PyCatastro()

    def consultar_por_rc(self, rc, provincia=None, municipio=None):
        return self.client.Consulta_DNPRC(
            provincia=provincia,
            municipio=municipio,
            rc=rc
        )
