import json
import logging
from typing import List, Dict, Any

from llm_extractor import extract_deed_chunk
from deed_processor import extract_catastral_refs_regex, validate_references


# ==========================
# CONFIGURACIÓN LOGGING
# ==========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================
# NORMALIZACIÓN DE TEXTO
# ==========================

def normalize_text(full_text) -> str:
    """
    Asegura que el texto siempre sea string.
    Corrige el problema donde OCR devuelve lista de páginas.
    """
    if isinstance(full_text, list):
        logger.info("Convirtiendo lista de páginas a string único.")
        return "\n".join(full_text)

    if not isinstance(full_text, str):
        raise ValueError("El texto de entrada debe ser string o lista de strings.")

    return full_text

def safe_json_load(raw: str):
    """
    Extrae el primer bloque JSON válido de una respuesta LLM.
    """
    import re

    if not raw:
        return None

    # Elimina markdown ```json
    raw = raw.strip()
    raw = re.sub(r"^```json", "", raw)
    raw = re.sub(r"^```", "", raw)
    raw = re.sub(r"```$", "", raw)

    # Busca el primer objeto JSON {...}
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except:
        return None


# ==========================
# CHUNKING SEGURO
# ==========================

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """
    Divide el texto en bloques seguros para modelos 4k.
    4000 caracteres deja margen para el prompt.
    """
    if len(text) <= max_chars:
        logger.info("Texto cabe en un solo chunk.")
        return [text]

    chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    logger.info(f"Texto dividido en {len(chunks)} chunks.")
    return chunks


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================

def process_deed(full_text) -> Dict[str, Any]:

    logger.info("Inicio de procesamiento de escritura.")

    # 🔥 ARREGLO CRÍTICO
    full_text = normalize_text(full_text)

    chunks = chunk_text(full_text)

    all_properties = []
    numero_escritura = None
    tipo = None
    all_alerts = []
    failed_chunks = 0

    for idx, chunk in enumerate(chunks):
        logger.info(f"Procesando chunk {idx + 1}/{len(chunks)}")

        try:
            raw = extract_deed_chunk(chunk)
        except Exception as e:
            logger.error(f"Error LLM en chunk {idx + 1}: {str(e)}")
            all_alerts.append(f"Error LLM en chunk {idx + 1}")
            failed_chunks += 1
            continue

        # Protección adicional
        if not raw or not isinstance(raw, str):
            logger.warning(f"Respuesta vacía o inválida en chunk {idx + 1}")
            failed_chunks += 1
            continue

        try:
            parsed = safe_json_load(raw)
            if not parsed:
                logger.warning(f"JSON inválido en chunk {idx + 1}")
                all_alerts.append(f"JSON inválido en chunk {idx + 1}")
                failed_chunks += 1
                continue
        except Exception:
            logger.warning(f"JSON inválido en chunk {idx + 1}")
            all_alerts.append(f"JSON inválido en chunk {idx + 1}")
            failed_chunks += 1
            continue

        # Datos generales (solo una vez)
        if not numero_escritura:
            numero_escritura = parsed.get("numero_escritura")

        if not tipo:
            tipo = parsed.get("tipo")

        # Inmuebles
        properties = parsed.get("inmuebles", [])
        if isinstance(properties, list):
            all_properties.extend(properties)

        # Alertas
        alerts = parsed.get("alertas", [])
        if isinstance(alerts, list):
            all_alerts.extend(alerts)

    logger.info("Consolidando resultados...")

    # ==========================
    # DEDUPLICACIÓN
    # ==========================

    for prop in all_properties:
        refs = prop.get("referencias_catastrales", [])
        if isinstance(refs, list):
            prop["referencias_catastrales"] = list(set(refs))

    # ==========================
    # VALIDACIÓN GLOBAL REGEX
    # ==========================

    logger.info("Validando referencias catastrales por regex...")

    try:
        regex_refs = extract_catastral_refs_regex(full_text)
    except Exception as e:
        logger.error(f"Error en regex global: {str(e)}")
        regex_refs = []

    llm_refs = []
    for prop in all_properties:
        refs = prop.get("referencias_catastrales", [])
        if isinstance(refs, list):
            llm_refs.extend(refs)

    try:
        validation = validate_references(llm_refs, regex_refs)
    except Exception as e:
        logger.error(f"Error validando referencias: {str(e)}")
        validation = {"error": str(e)}

    logger.info("Proceso finalizado.")

    if failed_chunks == len(chunks):
        logger.error("Todos los chunks fallaron. Resultado inválido.")

    return {
        "numero_escritura": numero_escritura,
        "tipo": tipo,
        "inmuebles": all_properties,
        "alertas_llm": all_alerts,
        "validacion_regex": validation,
        "chunks_procesados": len(chunks),
        "chunks_fallidos": failed_chunks
    }
