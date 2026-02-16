from openai import OpenAI

#modelo = "qwen2.5-7b-instruct-1m"
modelo = "google/gemma-3-4b"

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

# Test: conectar con lm studio
def test_connection():
    response = client.chat.completions.create(
        model = modelo,
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

    Analiza el siguiente texto extraído de una factura.

    Devuelve EXCLUSIVAMENTE un ARRAY JSON válido.
    No escribas explicaciones.
    No escribas texto adicional.
    No uses comillas triples.
    No añadas comentarios.
    Devuelve solo el array JSON.
    Cada elemento del array debe representar una línea de factura.

    Formato obligatorio de salida (respetar exactamente esta estructura):

    [
        {{
            "numero_orden": string | null,
            "numero_factura": string | null,
            "fecha": string | null,
            "cif": string | null,
            "proveedor": string | null,
            "comunidad_autonoma": string | null,
            "articulo": string | null,
            "cantidad": number | null
        }}
    ]

    Reglas estrictas:

    - El resultado debe ser SIEMPRE un array.
    - Incluso si solo existe una línea, devolver un array con un único elemento.
    - Si la factura contiene varias líneas de producto, generar un objeto por cada línea.
    - No devolver múltiples objetos separados fuera de un array.
    - No incluir texto fuera del JSON.
    - No incluir campos adicionales.
    - Si un dato no aparece, usar null.
    - No inventar datos.

    Reglas para "cantidad":
    - En cada línea de consumo, la tabla sigue esta estructura:
        - Ref. Fecha / Hora Producto Establecimiento Matrícula Km Cantidad P.Un. Dto. Importe
        - La "cantidad" es el valor numérico situado inmediatamente antes de la columna "P.Un.".
    - No debe formar parte del nombre del producto (ejemplo: "Gasol 5").
    - Copiar EXACTAMENTE el signo que aparece en el texto.
    - Ignorar números entre corchetes [ ].
    - Si no hay símbolo "-" delante del número, la cantidad es positiva.
    - No inferir signos negativos.
    Es decir:
    - Es el número que aparece justo antes del precio unitario.
    - No es el precio unitario.
    - No es el descuento.
    - No es el importe final.
    - Ignorar números que aparezcan en secciones como:
        "Totales", "Resumen de Carburantes", "Desglose de Impuestos".
    - La cantidad debe extraerse exclusivamente de la línea de consumo individual.

    Reglas para "fecha":
    - Formato obligatorio YYYY-MM-DD.
    - Si aparece en formato DD/MM/YYYY o DD-MM-YYYY, convertirlo.

    Texto de la factura:
    {text}
    """

    response = client.chat.completions.create(
        model = modelo,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content


def extract_deed_chunk(chunk):
    prompt = f"""
    Eres un sistema experto en análisis de escrituras notariales españolas.

    Extrae únicamente la información presente en el texto.

    Devuelve exclusivamente un JSON válido.
    No incluyas explicaciones.
    No incluyas texto adicional.
    No uses comillas triples.
    No inventes datos.

    Estructura obligatoria:

    {{
    "numero_escritura": string | null,
    "tipo": string | null,
    "inmuebles": [
        {{
        "descripcion": string | null,
        "direccion": string | null,
        "municipio": string | null,
        "referencias_catastrales": [string],
        "regimen": "ganancial" | "privativo" | null
        }}
    ],
    "alertas": [string]
    }}

    Reglas:
    - Si un dato no aparece, usar null.
    - No duplicar referencias catastrales.
    - Extraer referencias catastrales exactamente como aparecen.
    - No interpretar, solo extraer.
    - Solo considerar como referencia catastral códigos alfanuméricos largos (mínimo 10 caracteres).
    - No incluir números de inventario.
    - No incluir importes.
    - No incluir números aislados.
    - Si el inmueble está dentro de un bloque que indique "ACTIVOS DE NATURALEZA GANANCIAL", marcar "regimen": "ganancial".
    - Si el inmueble está dentro de un bloque que indique "ACTIVO DE NATURALEZA PRIVATIVA", marcar "regimen": "privativo".
    - Si no se puede determinar, usar null.

    Texto:
    {chunk}
    """

    response = client.chat.completions.create(
        model = modelo,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content