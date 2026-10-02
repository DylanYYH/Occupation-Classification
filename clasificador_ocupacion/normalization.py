import re

def clean_mojibake(text: str) -> str:
    """
    Catch and correct common Spanish/English encoding corruptions (mojibake)
    found in the raw dataset.
    """
    if not text:
        return ""
    
    # Specific replacement dictionary for known corrupted patterns
    mojibake_map = {
        # Years / Años corruptions
        "AAFA'O": "año",
        "AÃfÂ'O": "año",
        "AÃfÂ±o": "año",
        "aÃfÂ±o": "año",
        "aÃfÂ'o": "año",
        "afÂto": "año",
        "aÃfÂ±": "año",
        "aÃfÂ'": "año",
        
        # Tecnico corruptions
        "TÄfÃ cnico": "tecnico",
        "tĀfÃ cnico": "tecnico",
        "TÄfÃ©cnico": "tecnico",
        "TÃfÂ©cnico": "tecnico",
        "tÃfÂ©cnico": "tecnico",
        "TÃfÂ©cn": "tecnico",
        "TÃfÂ": "tecnico",
        
        # Construccion corruptions
        "CONSTRUCCIAFAN": "construccion",
        "ConstrucciÃfÂ³n": "construccion",
        "construcciÃfÂ³n": "construccion",
        "CONSTRUCCIÃfÂN": "construccion",
        "CONTRUCCIÃfÂ\"N": "construccion",
        "CONTRUCCIÃfÂ\"": "construccion",
        
        # MÃƒÂ and secretarial anomalies
        "MÃƒÂ, CURSO TAFA": "medica, curso tecnico",
        "MÃƒÂ,CURSO TÃfÂ": "medica, curso tecnico",
        "MÃƒÂ": "medica",
        "MÃfÂ©dica": "medica",
        "mÃfÂ©dica": "medica",
        "MÃfÂ¡quina": "maquina",
        "mÃfÂ¡quina": "maquina",
        "PolÃfÂ": "policia",
        "polÃfÂ": "policia",
        "AlmacÃfÂ©n": "almacen",
        "almacÃfÂ©n": "almacen",
        "DivisiÃfÂ³n": "division",
        "divisiÃfÂ³n": "division",
        "EstetÃfÂ": "estetica",
        "estetÃfÂ": "estetica",
        "CosmetÃfÂ³loga": "cosmetologa",
        "cosmetÃfÂ³loga": "cosmetologa",
        "ReparaciÃfÂ³n": "reparacion",
        "reparaciÃfÂ³n": "reparacion",
        "DiseÃfÂ±o": "diseño",
        "diseÃfÂ±o": "diseño",
        "GrÃfÂ¡fico": "grafico",
        "grÃfÂ¡fico": "grafico",
        "ORDEÃfÂ'ÃfÂ": "ordeñador",
        "ORDEÃfÂ'ADOR": "ordeñador",
        "EspaÃfÂ±ol": "español",
        "espaÃfÂ±ol": "español",
        "ÃfÂREAS VERDES": "areas verdes",
        "ÃfÂreas verdes": "areas verdes",
        "ÃfÂ": "a",  # General fallback
    }
    
    for corrupted, clean in mojibake_map.items():
        text = text.replace(corrupted, clean)
        
    return text


def remove_accents(text: str) -> str:
    """
    Remove accent marks from Spanish vowels (á, é, í, ó, ú, ü)
    while explicitly preserving the letter ñ/Ñ.
    """
    if not text:
        return ""
    
    accent_map = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ü': 'u',
        'Ñ': 'ñ'  # normalize Ñ to lowercase ñ
    }
    
    for accented, clean in accent_map.items():
        text = text.replace(accented, clean)
        
    return text


def normalize_text(text: str) -> str:
    """
    Run the full preprocessing pipeline on raw human input:
    1. Handle encoding anomalies (mojibake)
    2. Convert to lowercase
    3. Drop accent marks (preserving ñ)
    4. Strip leading/trailing spaces and eliminate extra interior whitespaces
    """
    if not isinstance(text, str):
        return ""
        
    cleaned = clean_mojibake(text)
    cleaned = cleaned.lower()
    cleaned = remove_accents(cleaned)
    
    # Replace multiple whitespaces/newlines/tabs with a single space and strip
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned
