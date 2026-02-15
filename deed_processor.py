import re

CATASTRAL_PATTERN = r"\b[0-9A-Z]{14}[A-Z]{2}\b"

def extract_catastral_refs_regex(text):
    return list(set(re.findall(CATASTRAL_PATTERN, text)))

def validate_references(llm_refs, full_text_refs):
    llm_set = set(llm_refs)
    full_set = set(full_text_refs)

    missing = full_set - llm_set
    extra = llm_set - full_set

    return {
        "missing_from_llm": list(missing),
        "unexpected_from_llm": list(extra)
    }
