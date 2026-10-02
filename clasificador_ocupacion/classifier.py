import os
import json
from openai import OpenAI
from clasificador_ocupacion.normalization import normalize_text
from clasificador_ocupacion.taxonomy import VALID_OCCUPATIONS, OCCUPATION_TRANSLATIONS, AUTHORIZED_VOCABULARY, INDUSTRY_GROUPS

# Initialize OpenAI client (uses OPENAI_API_KEY environment variable)
def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Fallback to empty client or try to raise a clear message if called
        return None
    return OpenAI(api_key=api_key)

def classify_text_offline(text: str) -> dict:
    """
    Offline fallback classifier that matches common occupation keywords
    when the OpenAI API key is not present.
    """
    normalized = normalize_text(text)
    
    # Map keywords to standardized Spanish occupation labels
    keyword_map = {
        "analyst": "analista",
        "chemist": "quimico",
        "laboratorio": "quimico",
        "quimica": "quimico",
        "microbiologa": "analista",
        "carpinter": "carpinteria",
        "cocin": "cocinero",
        "cook": "cocinero",
        "enferm": "enfermera",
        "emferm": "enfermera",
        "secretar": "secretaria",
        "oficin": "oficinista",
        "recepcionista": "recepcionista",
        "cuidad": "cuidador",
        "cuido": "cuidador",
        "envejeciente": "cuidador",
        "deliber": "repartidor",
        "delivery": "repartidor",
        "driver": "chofer",
        "chofer": "chofer",
        "cliente": "servicio al cliente",
        "customer": "servicio al cliente",
        "hostess": "servicio al cliente",
        "waitress": "servicio al cliente",
        "manten": "mantenimiento",
        "limpieza": "mantenimiento",
        "janitor": "conserje",
        "housekeeping": "ama de llaves",
        "ama de llaves": "ama de llaves",
        "ensambl": "ensamblador",
        "fabric": "ensamblador",
        "fabrica": "operario de produccion",
        "produccion": "operario de produccion",
        "machine operator": "operador de maquinaria",
        "warehouse": "logistica",
        "montacarga": "operador de maquinaria",
        "ventas": "vendedor",
        "vendedor": "vendedor",
        "guardia": "seguridad",
        "seguridad": "seguridad",
        "municipal": "seguridad",
        "policia": "seguridad",
        "construc": "construccion",
        "obrero": "construccion",
        "handyman": "handyman",
        "electricista": "electricista",
        "electricidad": "electricista",
        "refrigerac": "tecnico",
        "ordeñ": "agricola",
        "agricol": "agricola"
    }
    
    for kw, label in keyword_map.items():
        if kw in normalized:
            return {
                "ocupacion": label,
                "occupation": OCCUPATION_TRANSLATIONS.get(label),
                "reasoning": f"Offline matching: matched keyword '{kw}' -> '{label}'",
                "confidence": 0.8
            }
            
    return {
        "ocupacion": None,
        "occupation": None,
        "reasoning": "Offline matching: no keywords matched.",
        "confidence": 0.0
    }

def classify_text_with_llm(text: str) -> dict:
    """
    Call the LLM to classify raw text into the authorized Spanish taxonomy
    and targeted English equivalent.
    """
    client = get_openai_client()
    if not client:
        # Fallback to offline keyword-based matching
        return classify_text_offline(text)
        
    prompt = f"""You are an expert Occupation Classifier specializing in the Puerto Rico employment market.
Your task is to classify a person's raw profile text into a standardized Spanish occupation label (ocupacion) and its English translation (occupation).

Authorized Spanish Occupations List:
{AUTHORIZED_VOCABULARY}

Industry Groups (use these if the text matches general industry categories rather than specific occupations):
{list(INDUSTRY_GROUPS.keys())}

Rules for Classification:
1. Choose the standardized Spanish 'ocupacion' STRICTLY from the lists above. It must be lowercase, exactly matching one of the options.
2. If the text lists multiple occupations (e.g. "AMA DE LLAVES / FACTORIA / COCINA"), default to the first relevant position (e.g. "ama de llaves"), UNLESS one of the secondary positions provides significantly higher industry specificity (e.g. "Directora de Operaciones - Farmacéutica" maps to "farmaceutica").
3. Determine the English 'occupation' translation optimized for professional job search boards (e.g. "servicio al cliente" -> "customer service representative").
4. If the text does not contain any occupational keywords, is too ambiguous, or is just a general education level (like "bachillerato", "cuarto año", "12") without any field specified, return null for both 'ocupacion' and 'occupation'.

Format your response as a JSON object with these keys:
- "ocupacion": "standardized Spanish label" or null
- "occupation": "standardized English label" or null
- "reasoning": "brief explanation of your decision"
- "confidence": score between 0.0 and 1.0

Text to classify:
"{text}"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional occupational classifier."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=300
        )
        result = json.loads(response.choices[0].message.content)
        # Validate that the predicted Spanish occupation is in VALID_OCCUPATIONS or is null
        ocup = result.get("ocupacion")
        if ocup and ocup not in VALID_OCCUPATIONS:
            # If not matching exactly, set to null so rejection loop handles it
            result["ocupacion"] = None
            result["occupation"] = None
        return result
    except Exception as e:
        return {
            "ocupacion": None,
            "occupation": None,
            "reasoning": f"Error during API call: {str(e)}",
            "confidence": 0.0
        }


# Runtime dynamic dictionary for rejection loop updates
DYNAMIC_PATTERNS = {}

def get_direct_match(normalized_text: str) -> dict:
    """
    Check if the normalized text has a direct dictionary mapping
    to bypass LLM calls for simple cases.
    """
    if normalized_text in DYNAMIC_PATTERNS:
        return {
            "ocupacion": DYNAMIC_PATTERNS[normalized_text],
            "occupation": OCCUPATION_TRANSLATIONS.get(DYNAMIC_PATTERNS[normalized_text]),
            "reasoning": "Mapped via dynamically updated rules from rejection loop.",
            "confidence": 1.0
        }
    if normalized_text in VALID_OCCUPATIONS:
        return {
            "ocupacion": normalized_text,
            "occupation": OCCUPATION_TRANSLATIONS.get(normalized_text),
            "reasoning": "Direct exact match found in authorized vocabulary.",
            "confidence": 1.0
        }
    return None


def classify_value(raw_text: str) -> dict:
    """
    Normalize and classify a single string value.
    """
    normalized = normalize_text(raw_text)
    if not normalized or normalized in ["no", "na", "none", "ni", "si", "12", "16", "12mo", "10", "14"]:
        return {
            "ocupacion": None,
            "occupation": None,
            "reasoning": "Empty or negative/educational indicator value.",
            "confidence": 1.0
        }
        
    # Check for direct exact match
    direct = get_direct_match(normalized)
    if direct:
        return direct
        
    # Fallback to LLM
    return classify_text_with_llm(raw_text)


def process_row_by_priority(row: dict) -> dict:
    """
    Determine the standardized 'ocupacion' by checking values sequentially
    in the exact priority chain:
    interestedareaofwork -> interestedareaofstudy -> areaofworkexperience -> areaofstudy -> adiestramientopdl
    """
    priority_chain = [
        "interestedareaofwork",
        "interestedareaofstudy",
        "areaofworkexperience",
        "areaofstudy",
        "adiestramientopdl"
    ]
    
    classification_result = {
        "ocupacion": None,
        "occupation": None,
        "selected_field": None,
        "raw_text": None,
        "reasoning": None,
        "confidence": 0.0
    }
    
    # Check variables sequentially
    for field in priority_chain:
        if field in row and row[field]:
            raw_val = str(row[field]).strip()
            # If the value is not empty
            if raw_val:
                result = classify_value(raw_val)
                # If we succeeded in getting a classification
                if result.get("ocupacion"):
                    classification_result["ocupacion"] = result["ocupacion"]
                    classification_result["occupation"] = result["occupation"]
                    classification_result["selected_field"] = field
                    classification_result["raw_text"] = raw_val
                    classification_result["reasoning"] = result.get("reasoning", "")
                    classification_result["confidence"] = result.get("confidence", 0.0)
                    return classification_result
                    
    # If we reached here, no field was successfully classified.
    # We will try a collective evaluation using the LLM across all fields to see if we can extract an occupation.
    all_fields_text = " | ".join([f"{f}: {row[f]}" for f in priority_chain if f in row and row[f]])
    if all_fields_text.strip():
        result = classify_text_with_llm(all_fields_text)
        if result.get("ocupacion"):
            classification_result["ocupacion"] = result["ocupacion"]
            classification_result["occupation"] = result["occupation"]
            classification_result["selected_field"] = "multiple_fields_fallback"
            classification_result["raw_text"] = all_fields_text
            classification_result["reasoning"] = result.get("reasoning", "") + " (Collective fallback)"
            classification_result["confidence"] = result.get("confidence", 0.0)
            
    return classification_result
