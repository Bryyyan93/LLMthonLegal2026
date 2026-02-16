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

    Tu tarea es identificar bloques de inventario y adjudicaciones de forma estrictamente literal.

    Devuelve exclusivamente un JSON válido.
    No incluyas explicaciones.
    No incluyas texto adicional.
    No uses comillas triples.
    No inventes datos.

    Estructura obligatoria:

    {{
    "numero_escritura": string | null,
    "inventario": [
        {{
        "numero": int,
        "tipo": "Bien inmueble | Saldo bancario | Valor mobiliario | Ajuar | ...",
        "descripcion": string | null,
        "referencias_catastrales": [string],
        "regimen": "ganancial | privativo | desconocido"
        }}
    ],
    "adjudicaciones": [
        {{
        "numero_inventario": int,
        "cuota": string | null,
        "beneficiario": string | null
        }}
  ],
    "alertas": [string]
    }}

    REGLAS ESTRICTAS:
    - No extraer números de papel timbrado.

    1. NUMERO_ESCRITURA:
    - Solo debe extraerse cuando aparezca precedido por la palabra "NÚMERO" 
        en mayúsculas al inicio de línea. (ej: DOS MIL QUINIENTOS TREINTA Y SEIS)
    - Puede estar escrito en cifra.
    - No extraer códigos alfanuméricos.

    2. IDENTIFICACIÓN DE NÚMERO DE INVENTARIO
    Solo se considera número de inventario cuando:
    - Está seguido inmediatamente por ".-"
    - Patrón válido: ^\s*\d+\s*\.\s*-
    - Ese número es el campo "numero".
    - Es obligatorio extraerlo si existe.
    - No confundir con número de escritura.
    - Ejemplo: "11.- DESCRIPCIÓN"

    3. DESCRIPCIÓN
    - La descripción es todo el texto comprendido desde el encabezado numerado
        hasta antes del siguiente encabezado numerado.
    - Extraerla completa sin resumir.

    4. RÉGIMEN
    - Si el bloque aparece bajo un encabezado que indique:
        "NATURALEZA GANANCIAL" → "ganancial"
        "NATURALEZA PRIVATIVA" → "privativo"
    - Si no aparece ninguna indicación expresa, coge el del chunck anterior.
    - No inferir por contexto implícito.

    5. REFERENCIAS CATASTRALES
    - Solo cadenas que cumplan exactamente:
        7 dígitos + 1 letra + 7 dígitos + 2 letras
    - Exactamente 20 caracteres.
    - No incluir importes.
    - No incluir números aislados.
    - No duplicar.

    6. TIPO
    - Si en la descripción aparecen expresiones como:
        "campo", "vivienda", "finca", "parcela", "solar" → "Bien inmueble"
        "cuenta", "saldo", "IBAN" → "Saldo bancario"
        "acciones", "participaciones", "fondo" → "Valor mobiliario"
    - Si no encaja claramente → "Otro"

    7. ADJUDICACIONES
    - Frases como:
        "mitad indivisa del número X"
        "se adjudica el número X"
        "adjudicado a"
        deben generar entrada en "adjudicaciones".

    8. PROHIBIDO:
    - Inventar datos.
    - Completar información implícita.
    - Reinterpretar unidades antiguas.
    - Cambiar redacción original.

    Si un dato no aparece, usar null.
    
    Texto:
    {chunk}
    """
    #- No crear un elemento en "inventario" a partir de una adjudicación o cuota.
    response = client.chat.completions.create(
        model = modelo,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content