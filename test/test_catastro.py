from catastro_demo.catastro_client import CatastroClient

# provincia="VALENCIA",
# municipio="VALENCIA",
# rc="2270710YJ2727S0001WR"

# ======= PRUEBA LIBRE =======

print("---- CONSULTA LIBRE ----")
cliente_libre = CatastroClient(modo="libre")

resultado_libre = cliente_libre.consultar(
    rc="2270710YJ2727S",
    provincia="VALENCIA",
    municipio="BURJASSOT"
)

print(resultado_libre)


# ======= PRUEBA PROTEGIDA (SIMULADA) =======

print("\n---- CONSULTA PROTEGIDA (DEMO) ----")

cliente_protegido = CatastroClient(
    modo="protegido",
    certificado="certificado_despacho.pem"
)

resultado_protegido = cliente_protegido.consultar(
    rc="2270710YJ2727S0001WR"
)

print(resultado_protegido)