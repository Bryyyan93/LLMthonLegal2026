from pycatastro import PyCatastro

cat = PyCatastro()

resultado = cat.Consulta_DNPRC(
    provincia="MADRID",
    municipio="MADRID",
    rc="8180917VH5279S"
)

print(resultado)
