import json
from clasificador_ocupacion.normalization import normalize_text
from clasificador_ocupacion.taxonomy import VALID_OCCUPATIONS, AUTHORIZED_VOCABULARY, INDUSTRY_GROUPS
from clasificador_ocupacion.classifier import get_openai_client, DYNAMIC_PATTERNS, process_row_by_priority

def has_valid_input_text(record: dict) -> bool:
    """
    Check if a record contains any actual human-input text in the priority fields.
    """
    priority_chain = [
        "interestedareaofwork",
        "interestedareaofstudy",
        "areaofworkexperience",
        "areaofstudy",
        "adiestramientopdl"
    ]
    
    for field in priority_chain:
        if field in record and record[field]:
            val = str(record[field]).strip()
            norm = normalize_text(val)
            if norm and norm not in ["no", "na", "none", "ni", "si", "12", "16", "12mo", "10", "14"]:
                return True
    return False


def get_offline_suggestion_for_unclassified(raw_text: str) -> dict:
    """
    Offline suggestion fallback when OpenAI client is missing.
    Matches keywords to return a valid fallback occupation.
    """
    norm = normalize_text(raw_text)
    if "analyst" in norm or "chemist" in norm or "microbiologa" in norm or "quimic" in norm:
        return {"suggested_ocupacion": "quimico", "reasoning": "Offline fallback suggestion for lab/chemistry."}
    if "carpinter" in norm:
        return {"suggested_ocupacion": "carpinteria", "reasoning": "Offline fallback suggestion for carpenter."}
    if "cocin" in norm or "cook" in norm:
        return {"suggested_ocupacion": "cocinero", "reasoning": "Offline fallback suggestion for kitchen/cook."}
    if "enferm" in norm or "emferm" in norm:
        return {"suggested_ocupacion": "enfermera", "reasoning": "Offline fallback suggestion for nurse."}
    if "secretar" in norm:
        return {"suggested_ocupacion": "secretaria", "reasoning": "Offline fallback suggestion for secretary."}
    if "cuidad" in norm or "cuido" in norm or "envejeciente" in norm:
        return {"suggested_ocupacion": "cuidador", "reasoning": "Offline fallback suggestion for caregiver."}
    if "deliber" in norm or "delivery" in norm or "chofer" in norm or "driver" in norm:
        return {"suggested_ocupacion": "repartidor", "reasoning": "Offline fallback suggestion for driver/delivery."}
    if "cliente" in norm or "customer" in norm or "hostess" in norm or "waitress" in norm:
        return {"suggested_ocupacion": "servicio al cliente", "reasoning": "Offline fallback suggestion for customer service."}
    if "manten" in norm or "limpieza" in norm or "janitor" in norm or "housekeeping" in norm:
        return {"suggested_ocupacion": "mantenimiento", "reasoning": "Offline fallback suggestion for maintenance."}
    if "ensambl" in norm or "fabrica" in norm or "producci" in norm:
        return {"suggested_ocupacion": "operario de produccion", "reasoning": "Offline fallback suggestion for production."}
    if "ventas" in norm or "vendedor" in norm:
        return {"suggested_ocupacion": "vendedor", "reasoning": "Offline fallback suggestion for sales."}
    if "guardia" in norm or "seguridad" in norm:
        return {"suggested_ocupacion": "seguridad", "reasoning": "Offline fallback suggestion for security."}
    if "construc" in norm or "obrero" in norm or "handyman" in norm:
        return {"suggested_ocupacion": "construccion", "reasoning": "Offline fallback suggestion for construction."}
    if "electr" in norm or "refriger" in norm:
        return {"suggested_ocupacion": "electricista", "reasoning": "Offline fallback suggestion for technical/electrician."}
    if "ordeñ" in norm or "agric" in norm:
        return {"suggested_ocupacion": "agricola", "reasoning": "Offline fallback suggestion for agriculture."}
    
    return {"suggested_ocupacion": "ayudante", "reasoning": "Generic offline fallback."}

def get_llm_suggestion_for_unclassified(raw_text: str) -> dict:
    """
    Ask the LLM to suggest which authorized category/vocabulary term 
    the raw unclassified text should map to, providing context.
    """
    client = get_openai_client()
    if not client:
        return get_offline_suggestion_for_unclassified(raw_text)
        
    prompt = f"""You are an expert Occupation Classifier.
We have encountered a raw human profile text that our pipeline failed to classify into our strict authorized list.

Raw text:
"{raw_text}"

Authorized Spanish Occupations List:
{AUTHORIZED_VOCABULARY}

Industry Groups:
{list(INDUSTRY_GROUPS.keys())}

Your task:
1. Analyze the raw text and find the single most appropriate Spanish occupation from the authorized lists that best fits or represents this profile.
2. Even if it is a loose match or a generic classification, you MUST choose one category. Use common fallbacks like 'ayudante', 'empleo de verano', 'tecnico', 'oficinista', 'construccion', or 'servicio al cliente' if no specific match is found.
3. Return a JSON object with:
   - "suggested_ocupacion": "the chosen category name" (strictly from the list, lowercase)
   - "reasoning": "brief reasoning explaining why this is the best match"
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
            max_tokens=200
        )
        result = json.loads(response.choices[0].message.content)
        sug = result.get("suggested_ocupacion")
        if sug and sug in VALID_OCCUPATIONS:
            return result
        else:
            result["suggested_ocupacion"] = "ayudante"  # Default fallback if LLM returned invalid category
            return result
    except Exception as e:
        return {"suggested_ocupacion": "ayudante", "reasoning": f"Error: {str(e)}"}


def run_rejection_loop(records: list, max_iterations: int = 3) -> list:
    """
    Mandatory export validation:
    1. Identify any problematic rows with active text but null classification assignments.
    2. Stop execution/pause, isolate the unclassified strings, dynamically print suggestion context.
    3. Update the dynamic patterns registry.
    4. Automatically re-run the classification algorithm.
    5. Repeat until all rows with text are classified.
    """
    iteration = 0
    
    # We will compute/update classifications in place in the records list
    # First, ensure all records have initial classifications
    for r in records:
        if "ocupacion" not in r:
            res = process_row_by_priority(r)
            r.update(res)

    while iteration < max_iterations:
        iteration += 1
        problematic_records = []
        
        # Identify problematic rows
        for r in records:
            # Has human text, but classification is null/empty
            if has_valid_input_text(r) and not r.get("ocupacion"):
                problematic_records.append(r)
                
        if not problematic_records:
            print(f"Rejection loop check passed: 100% of rows with human text have been classified (Iteration {iteration-1}).")
            return records
            
        print(f"\n[ALERT] Rejection loop triggered (Iteration {iteration})!")
        print(f"Isolated {len(problematic_records)} unclassified rows containing active text.")
        
        # Stop and isolate specific unclassified strings
        for pr in problematic_records:
            # Find the first field containing the raw text that failed
            raw_text = pr.get("raw_text") or pr.get("interestedareaofwork") or pr.get("areaofworkexperience")
            norm_text = normalize_text(raw_text)
            
            print(f"  - Record {pr['id_persona']}: Unclassified text '{raw_text}' (normalized: '{norm_text}')")
            
            # Suggestion context
            suggestion = get_llm_suggestion_for_unclassified(raw_text)
            suggested_ocup = suggestion.get("suggested_ocupacion")
            reasoning = suggestion.get("reasoning", "")
            
            print(f"    --> Suggestion: Map to '{suggested_ocup}' because: {reasoning}")
            
            # Dynamically update the pattern dictionary matching parameters
            if norm_text and suggested_ocup:
                DYNAMIC_PATTERNS[norm_text] = suggested_ocup
                print(f"    --> Dynamically updated DYNAMIC_PATTERNS: '{norm_text}' -> '{suggested_ocup}'")
                
        # Automatically re-run the classification algorithm for the problematic records
        print("Automatically re-running classification with updated matching rules...")
        for pr in problematic_records:
            res = process_row_by_priority(pr)
            pr.update(res)
            
    # If we exited the loop and still have problematic rows, raise an error
    final_problematic = [r for r in records if has_valid_input_text(r) and not r.get("ocupacion")]
    if final_problematic:
        ids = [r["id_persona"] for r in final_problematic]
        raise RuntimeError(f"Export validation failed! The following rows have active text but could not be classified: {ids}")
        
    return records
