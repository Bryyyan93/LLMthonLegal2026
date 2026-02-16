import re

# ---------------------------------------------------------
# Patrón oficial de referencia catastral estándar (20 caracteres):
# 7 dígitos + 1 letra + 7 dígitos + 2 letras
# ---------------------------------------------------------
CATASTRAL_PATTERN = re.compile(r"\b\d{7}[A-Z]\d{7}[A-Z]{2}\b")

# Extrae todas las referencias catastrales válidas encontradas en un texto completo.
def extract_catastral_refs_regex(text):
    text = text.upper()
    return list(set(re.findall(CATASTRAL_PATTERN, text)))

# Valida una referencia individual.
def is_valid_ref_cat(ref: str) -> bool:
    ref = ref.strip().upper()
    return bool(CATASTRAL_PATTERN.fullmatch(ref))

# Compara referencias detectadas por el LLM frente a las detectadas por regex en el texto completo.
def validate_references(llm_refs, full_text_refs):
    llm_set = set(ref.upper() for ref in llm_refs)
    full_set = set(ref.upper() for ref in full_text_refs)

    missing = full_set - llm_set
    extra = llm_set - full_set

    return {
        "missing_from_llm": list(missing),
        "unexpected_from_llm": list(extra)
    }
