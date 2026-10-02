import json
from clasificador_ocupacion.normalization import normalize_text
from clasificador_ocupacion.taxonomy import VALID_OCCUPATIONS, INDUSTRY_GROUPS, AUTHORIZED_VOCABULARY
from clasificador_ocupacion.classifier import get_openai_client, classify_value, classify_text_with_llm

def get_industry_group(ocupacion: str) -> str:
    """
    Return the industry group name that this occupation belongs to.
    """
    if not ocupacion:
        return None
    # If the occupation is itself an industry group key
    if ocupacion in INDUSTRY_GROUPS:
        return ocupacion
    # Search in values
    for group_name, members in INDUSTRY_GROUPS.items():
        if ocupacion in members:
            return group_name
    return None


def run_masked_evaluation(records: list, target_field: str = "interestedareaofwork") -> dict:
    """
    Mask one field (e.g. interestedareaofwork) and ask the LLM to predict it
    using only the other 3 columns. Logging reasoning steps and calculating accuracy.
    """
    client = get_openai_client()

    results = []
    matches = 0
    valid_evals = 0

    print(f"\n--- Starting Masked Evaluation on target field: {target_field} ---")

    for i, record in enumerate(records):
        # 1. Establish ground truth by classifying the target field alone (if it has text)
        raw_target_val = record.get(target_field, "")
        if not raw_target_val or normalize_text(raw_target_val) in ["no", "na", "none", "ni", "si"]:
            continue
            
        true_classification = classify_value(raw_target_val)
        true_ocupacion = true_classification.get("ocupacion")
        if not true_ocupacion:
            continue  # If we couldn't classify it originally, we can't evaluate it
            
        valid_evals += 1
        
        # 2. Build the context with the other columns (remaining 3 columns)
        remaining_context = {}
        for k, v in record.items():
            if k not in ["id_persona", target_field] and v:
                remaining_context[k] = v
                
        # 3. Predict the masked variable
        if client:
            context_str = json.dumps(remaining_context, ensure_ascii=False)
            prompt = f"""You are an expert Occupation Classifier evaluating a self-supervised training task.
We have masked the '{target_field}' column for a user profile.
Based ONLY on the other profile variables provided below, predict the standardized Spanish occupation ('ocupacion') that belongs in the masked '{target_field}' column.

Profile Context:
{context_str}

Authorized Spanish Occupations List:
{AUTHORIZED_VOCABULARY}

Industry Groups:
{list(INDUSTRY_GROUPS.keys())}

Rules:
1. Choose the standardized Spanish 'ocupacion' STRICTLY from the lists above. It must be lowercase.
2. Return a JSON object with:
   - "predicted_ocupacion": the predicted Spanish occupation label, or null if it cannot be inferred.
   - "reasoning": your explicit, step-by-step reasoning for this prediction based on the other fields.
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
                pred_result = json.loads(response.choices[0].message.content)
                predicted_ocup = pred_result.get("predicted_ocupacion")
                reasoning = pred_result.get("reasoning", "")
            except Exception as e:
                predicted_ocup = None
                reasoning = f"Error during prediction call: {str(e)}"
        else:
            # Offline prediction strategy: check remaining columns in priority order and classify
            predicted_ocup = None
            reasoning = "Offline prediction from remaining active fields."
            for col_name in ["interestedareaofwork", "interestedareaofstudy", "areaofworkexperience", "areaofstudy"]:
                if col_name in remaining_context and remaining_context[col_name]:
                    val = str(remaining_context[col_name]).strip()
                    pred_res = classify_value(val)
                    if pred_res.get("ocupacion"):
                        predicted_ocup = pred_res["ocupacion"]
                        reasoning = f"Offline prediction: inferred from active column '{col_name}' value '{val}' -> '{predicted_ocup}'."
                        break

        # Compare predicted with true classification
        is_match = (predicted_ocup == true_ocupacion)
        # Check if they belong to the same industry family if not exact match
        true_group = get_industry_group(true_ocupacion)
        pred_group = get_industry_group(predicted_ocup)
        is_family_match = (true_group and pred_group and true_group == pred_group)

        if is_match or is_family_match:
            matches += 1

        results.append({
            "id_persona": record.get("id_persona"),
            "true_text": raw_target_val,
            "true_ocupacion": true_ocupacion,
            "predicted_ocupacion": predicted_ocup,
            "reasoning": reasoning,
            "exact_match": is_match,
            "family_match": is_family_match
        })
        
        print(f"Record {record.get('id_persona')}: True='{true_ocupacion}', Pred='{predicted_ocup}', Exact={is_match}, Family={is_family_match}")

    accuracy = (matches / valid_evals) if valid_evals > 0 else 0.0
    print(f"Masked Evaluation Complete. Accuracy (Exact or Family match): {accuracy:.2%} ({matches}/{valid_evals} records)")
    
    return {
        "accuracy": accuracy,
        "valid_evaluations": valid_evals,
        "results": results
    }


def run_consensus_measurement(records: list) -> dict:
    """
    Cross-checking testing mechanism.
    Evaluates predictions generated independently down each active column.
    Counts a score of 1.0 (Success) if predictions across columns converge
    on the exact same occupation or the same industry group.
    """
    columns_to_check = [
        "interestedareaofwork",
        "interestedareaofstudy",
        "areaofworkexperience",
        "areaofstudy"
    ]
    
    total_consensus_score = 0.0
    measurable_records = 0
    results = []

    print("\n--- Starting Cross-Checking Consensus Measurement ---")

    for record in records:
        predictions = {}
        
        # 1. Generate independent predictions for each active column
        for col in columns_to_check:
            val = record.get(col, "")
            if val:
                norm = normalize_text(val)
                # Ignore trivial/non-occupational strings
                if norm and norm not in ["no", "na", "none", "ni", "si", "12", "16", "12mo", "10", "14"]:
                    pred_res = classify_value(val)
                    ocup = pred_res.get("ocupacion")
                    if ocup:
                        predictions[col] = ocup

        # If we have fewer than 2 independent predictions, consensus is not measurable
        if len(predictions) < 2:
            results.append({
                "id_persona": record.get("id_persona"),
                "predictions": predictions,
                "score": 0.0,
                "status": "not_measurable",
                "reason": "Fewer than 2 active columns with valid occupation predictions."
            })
            continue

        measurable_records += 1
        unique_preds = list(set(predictions.values()))
        
        # 2. Check for exact agreement
        if len(unique_preds) == 1:
            score = 1.0
            status = "exact_consensus"
            reason = f"All active columns converged on the same occupation: '{unique_preds[0]}'"
        else:
            # 3. Check for industrial family consensus
            groups = [get_industry_group(p) for p in unique_preds]
            # Clean None values from groups
            valid_groups = [g for g in groups if g]
            
            # If all mapped to the same group and we didn't have unmapped categories
            if len(set(valid_groups)) == 1 and len(valid_groups) == len(unique_preds):
                score = 1.0
                status = "family_consensus"
                reason = f"Columns converged on the same industrial group '{valid_groups[0]}' (Predictions: {unique_preds})"
            else:
                score = 0.0
                status = "no_consensus"
                reason = f"Columns diverged. Predictions: {predictions}"

        total_consensus_score += score
        results.append({
            "id_persona": record.get("id_persona"),
            "predictions": predictions,
            "score": score,
            "status": status,
            "reason": reason
        })
        
        print(f"Record {record.get('id_persona')}: Predictions={predictions}, Score={score} ({status})")

    consensus_metric = (total_consensus_score / measurable_records) if measurable_records > 0 else 0.0
    print(f"Consensus Measurement Complete. Convergence confidence: {consensus_metric:.2%} (over {measurable_records} measurable records)")

    return {
        "convergence_confidence": consensus_metric,
        "measurable_records": measurable_records,
        "results": results
    }
