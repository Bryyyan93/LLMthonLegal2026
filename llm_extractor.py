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
    prompt = rf"""
    Eres un sistema experto en análisis de escrituras notariales españolas.

    Tu tarea es extraer EXCLUSIVAMENTE bienes inmuebles del inventario.

    Devuelve exclusivamente un JSON válido.
    No incluyas explicaciones.
    No incluyas texto adicional.
    No uses comillas triples.
    No inventes datos.

    Estructura obligatoria:

    {{
    "inventario": [
        {{
        "tipo": "Bien inmueble",
        "descripcion": string | null,
        "referencias_catastrales": [string],
        "regimen": "ganancial | privativo | desconocido"
        }}
    ],
  ],
    "alertas": [string]
    }}

    REGLAS ESTRICTAS:
    - No extraer números de papel timbrado.
    - Un bloque solo puede incluirse si comienza con un encabezado numerado con el formato:
        ^\s*\d+\s*\.\s*-
    - Si el texto no comienza con un encabezado numerado válido:
        - NO es inventario.
        - NO incluirlo.

    - Solo se incluirán en el array "inventario" aquellos bloques cuya descripción
    contenga de forma literal alguna de las siguientes palabras:
        "finca"
        "vivienda"
        "departamento"
        "parcela"
        "solar"
        "local"
        "garaje"
        "trastero"
        "campo"
    - Si NO contiene ninguna de esas palabras → NO incluir el bloque en el JSON.

    - En ese caso simplemente ignorarlo.
    - No añadirlo como "Otro".
    - No añadirlo con null.
    - No generar alerta.

    DESCRIPCIÓN
    - La descripción es todo el texto comprendido desde el encabezado numerado
        hasta antes del siguiente encabezado numerado.
    - Extraerla completa sin resumir.
    - Si esta vacio, ignorarlo

    RÉGIMEN
    - Si el bloque aparece bajo un encabezado que indique:
        "NATURALEZA GANANCIAL" → "ganancial"
        "NATURALEZA PRIVATIVA" → "privativo"
    - Si no aparece ninguna indicación expresa, coge el del chunck anterior.
    - No inferir por contexto implícito.

    REFERENCIAS CATASTRALES
    - Exactamente 20 caracteres
    - Sin espacios
    - Sin guiones
    - Sin puntos
    - Solo mayúsculas
    - Solo incluir referencias que cumplan EXACTAMENTE el patrón del ejemplo:
        - Ejemplo válido: 9959606YI1895N0001XY
        - Ejemplo inválido: 70625591

    - Si una cadena no cumple EXACTAMENTE ese patrón:
        - NO incluirla en el bloque en el inventario
        - Ignorarla completamente

    PROHIBIDO:
    - Inventar datos.
    - Completar información implícita.
    - Reinterpretar unidades antiguas.
    - Cambiar redacción original.
    
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