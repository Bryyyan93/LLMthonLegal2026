from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

# Test: conectar con lm studio
def test_connection():
    response = client.chat.completions.create(
        model="google/gemma-3-4b",
        messages=[
            {"role": "user", "content": "Responde solo con la palabra OK"}
        ],
        temperature=0
    )
    
    print(response.choices[0].message.content)

# Extraer datos de factura
def extract_invoice(text):
    prompt = f"""
    Eres un sistema experto en análisis documental jurídico-contable.

    Analiza el siguiente texto extraído de una factura y devuelve EXCLUSIVAMENTE un JSON válido.

    No escribas explicaciones.
    No escribas texto adicional.
    No uses comillas triples.
    No añadas comentarios.
    Devuelve solo el objeto JSON.

    Campos obligatorios:
    - numero_orden (string o null si no aparece)
    - numero_factura (string o null)
    - fecha (formato YYYY-MM-DD o null)
    - cif (string o null)
    - proveedor (string o null)
    - comunidad_autonoma (string o null)
    - articulo (string o null)
    - cantidad (número o null)

    Reglas:
    - Si un dato no aparece, usar null.
    - Convertir importes a número sin símbolo €.
    - No inventar datos.
    - La cantidad debe ser número sin símbolos.
    - La fecha debe ir en formato YYYY-MM-DD.

    Texto de la factura:
    {text}
    """

    response = client.chat.completions.create(
        model="google/gemma-3-4b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content


# if __name__ == "__main__":
#     #models = client.models.list()
#     #print(models)
#     #test_connection()
    
#     factura_prueba = """
#     Amado Gestión S.L.
#     AV Autovia CV35 KM 32
#     46160 Lliria
#     Valencia
#     CIF: B98044571
#     Dirección Fiscal Dirección Facturación
#     512
#     46171 CASINOS
#     Valencia - ESPAÑA -
#     46171 CASINOS
#     Valencia - ESPAÑA -
#     48440246S
#     Fecha Factura 31/08/2014
#     Núm. Factura 1400001185 Página 1 de 1 Fecha Operación 20/08/2014
#     Nº de Tarjeta: 99999500051200019 Nº de Matrícula: 3652LJM
#     Ref. Fecha / Hora Producto Establecimiento Matrícula Km Cantidad P.Un. Dto. Importe
#     5446 20-08-2014 11:33 Gasol 5 Amado Gestion, S.L 52,84 1,444€ 1,59€ 74,71€
#     Totales: 52,84 1,59€ 74,71€
#     Resumen de Carburantes
#     Producto Unidades Dto. Importe
#     Gasol 5 [ 95 ] 52,84 1,59 74,71€
#     Totales 52,84 1,59€ 74,71€
#     Desglose de Impuestos
#     Base Imponible IVA/IGIC Cuota
#     61,74€ 21,00% 12,97€
#     Total: 61,74€ Total: 12,97€
#     Resumen de Recibos
#     Vencimiento Forma de Pago Importe Recibo
#     10/09/2014 RECIBO DOMICILIADO 74,71 €
#     Banco: Cuenta:CCRIES2AXXXES50****************035222
#     Importe Total Factura: 74,71€
#     "setenta y cuatro € con setenta y un céntimos"
#     Amado Gestión S.L.
#     """

#     resultado = extract_invoice(factura_prueba)
#     print(resultado)