import os
import sys
from pathlib import Path

# Add project root to sys.path
base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from clasificador_ocupacion.utils import load_json_dataset, save_csv_dataset, make_search_link_esp, make_search_link_eng
from clasificador_ocupacion.classifier import process_row_by_priority
from clasificador_ocupacion.validation import run_rejection_loop
from clasificador_ocupacion.evaluation import run_consensus_measurement, run_masked_evaluation

def main():
    # 1. Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("[WARNING] OPENAI_API_KEY environment variable is not set.")
        print("Please set the key to run the active LLM classifier. Running in mock/offline mode otherwise.")

    # 2. Define file paths
    current_dir = Path(__file__).resolve().parent
    data_path = current_dir / "datos_ocupaciones_raw.json"
    output_csv = current_dir / "resultados_ocupaciones.csv"
    
    print(f"Loading raw dataset from {data_path}...")
    records = load_json_dataset(str(data_path))
    
    print("\n--- Starting Initial Priority-Based Classification Pipeline ---")
    # 3. Classify all records initially
    for record in records:
        classification = process_row_by_priority(record)
        record.update(classification)
        
    print("\n--- Running Mandatory Rejection Loop & Export Validation ---")
    # 4. Enforce self-correcting validation (rejection loop)
    validated_records = run_rejection_loop(records)
    
    print("\n--- Generating Search Links ---")
    # 5. Populate Spanish and English job links based on final classification
    for record in validated_records:
        ocup = record.get("ocupacion")
        occ = record.get("occupation")
        
        record["ocup_link_esp"] = make_search_link_esp(ocup)
        record["ocup_link_eng"] = make_search_link_eng(occ)

    # 6. Save outputs to CSV
    print(f"\nSaving final validated records to CSV: {output_csv}...")
    save_csv_dataset(validated_records, str(output_csv))
    
    # 7. Run Consensus Measurement
    print("\n=============================================")
    print("Running Consensus Measurement (Cross-Checking)")
    print("=============================================")
    consensus_report = run_consensus_measurement(validated_records)
    
    # 8. Run Masked Evaluation (Self-Supervised Testing)
    print("\n==========================================")
    print("Running Masked Evaluation (Self-Supervised)")
    print("==========================================")
    masked_report = run_masked_evaluation(validated_records, target_field="interestedareaofwork")

    # 9. Log final performance statistics
    print("\n==========================================")
    print("           PIPELINE METRICS SUMMARY       ")
    print("==========================================")
    print(f"Total processed records: {len(validated_records)}")
    print(f"Consensus Measurable Records: {consensus_report['measurable_records']}")
    print(f"Convergence Confidence Score: {consensus_report['convergence_confidence']:.2%}")
    print(f"Masked Evaluation Accuracy:   {masked_report['accuracy']:.2%} ({masked_report['valid_evaluations']} evaluated)")
    print("==========================================\n")

if __name__ == "__main__":
    main()
