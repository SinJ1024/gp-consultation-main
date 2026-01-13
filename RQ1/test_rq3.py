import pandas as pd
from tqdm import tqdm
from data_loader import DataLoader
from evaluator import FineSurEEvaluator
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)              
GENERATED_RESULTS_DIR = os.path.join(PROJECT_ROOT, "RQ3_output")
BASE_DATA_PATH = os.path.join(PROJECT_ROOT, "examples_gp_consultation")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "rq3_evaluation_results")

# "fact_checking", "fact_alignment", "conciseness"
EVALUATION_METRICS = ["fact_checking", "fact_alignment"]

STRATEGIES = ["few_shot"]
MAX_WORKERS = 20
LANGUAGES = ["EN", "NL"]

def process_case(case_id, model_json_dir, strategy, loader, evaluator, active_metrics):
    """
    Worker function: Dynamically Process a single case based on active_metrics.
    """
    # 1. Load Data
    data = loader.load_case_data(case_id)
    key_facts = data.get('key_facts', {})
    transcript = data.get('transcript', "") 
    
    # 2. Locate JSON
    safe_case_id = case_id.replace(" ", "_")
    json_filename = f"{safe_case_id}_{strategy}.json"
    json_path = os.path.join(model_json_dir, json_filename)

    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_json = json.load(f)
    except Exception:
        return None
    
    # 3. Key Mapping (Normalization)
    generated_soap = {"Subjective": "", "Objective": "", "Assessment": "", "Plan": ""}
    raw_json_normalized = {
        k.lower().strip().replace(":", "").replace("*", "").replace("#", ""): v 
        for k, v in raw_json.items()
    }
    
    mapping_rules = {
        "Subjective": ["subjective", "subjectief"],
        "Objective":  ["objective", "objectief"],
        "Assessment": ["assessment"],
        "Plan":       ["plan"]
    }

    for standard_key, aliases in mapping_rules.items():
        for alias in aliases:
            match = next((k for k in raw_json_normalized if alias in k), None)
            if match:
                generated_soap[standard_key] = raw_json_normalized[match]
                break

    # 4. Evaluate Dynamically
    # Stores results for requested metrics: {'metric_name': result_dict}
    case_results = {}

    try:
        # --- Fact Checking (Hallucination) ---
        if "fact_checking" in active_metrics:
            report = evaluator.fact_checking(generated_soap, transcript)
            case_results["fact_checking"] = {
                "Case_ID": case_id,
                "Overall_Score": report.get('overall_score', 0),
                **{k: report.get('scores', {}).get(k, 0) for k in ["Subjective", "Objective", "Assessment", "Plan"]}
            }

        # --- Fact Alignment (Completeness) ---
        if "fact_alignment" in active_metrics:
            report = evaluator.fact_alignment(generated_soap, key_facts)
            case_results["fact_alignment"] = {
                "Case_ID": case_id,
                "Overall_Score": report.get('overall_score', 0),
                **{k: report.get('scores', {}).get(k, 0) for k in ["Subjective", "Objective", "Assessment", "Plan"]}
            }

        # --- Conciseness ---
        if "conciseness" in active_metrics:
            report = evaluator.conciseness(generated_soap, key_facts)
            case_results["conciseness"] = {
                "Case_ID": case_id,
                "Overall_Score": report.get('overall_score', 0),
                **{k: report.get('scores', {}).get(k, 0) for k in ["Subjective", "Objective", "Assessment", "Plan"]}
            }

    except Exception as e:
        print(f"[Err] {case_id} ({strategy}): {e}")
        return None
    
    return case_results

def main():
    print(f"[Init] Root: {PROJECT_ROOT}")
    print(f"[Config] Metrics to run: {EVALUATION_METRICS}")
    
    evaluator = FineSurEEvaluator(model="deepseek-ai/DeepSeek-V3.2")
    
    for lang in LANGUAGES:
        print(f"\n{'='*40}")
        print(f"Processing Language: {lang}")
        print(f"{'='*40}")

        current_data_path = os.path.join(BASE_DATA_PATH, lang)
        current_gen_path = os.path.join(GENERATED_RESULTS_DIR, lang)
        current_output_dir = os.path.join(OUTPUT_DIR, lang)

        if not os.path.exists(current_data_path) or not os.path.exists(current_gen_path):
            print(f"[Skip] Path not found for {lang}")
            continue

        loader = DataLoader(base_path=current_data_path)
        case_ids = loader.get_all_case_ids()
        model_dirs = [d for d in os.listdir(current_gen_path) if os.path.isdir(os.path.join(current_gen_path, d))]
        
        for model_name in model_dirs:
            for strategy in STRATEGIES:
                print(f'\n>> Model: {model_name} | Strategy: {strategy} [{lang}]')
                
                model_json_dir = os.path.join(current_gen_path, model_name)
                
                # Initialize result containers for active metrics
                aggregator = {metric: [] for metric in EVALUATION_METRICS}
                
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    # Pass EVALUATION_METRICS to the worker
                    future_to_case = {
                        executor.submit(process_case, cid, model_json_dir, strategy, loader, evaluator, EVALUATION_METRICS): cid 
                        for cid in case_ids
                    }
                    
                    for future in tqdm(as_completed(future_to_case), total=len(case_ids), desc=f"Evaluating"):
                        result_dict = future.result()
                        if result_dict:
                            # Distribute results to appropriate lists
                            for metric_name, data in result_dict.items():
                                if metric_name in aggregator:
                                    aggregator[metric_name].append(data)

                # Save Results for each metric
                os.makedirs(current_output_dir, exist_ok=True)
                
                for metric_name, results in aggregator.items():
                    if results:
                        df = pd.DataFrame(results).replace("N/A", pd.NA)
                        avg = df.mean(numeric_only=True)
                        avg['Case_ID'] = 'Average'
                        df.loc[len(df)] = avg
                        
                        output_file = os.path.join(current_output_dir, f"{model_name}_{strategy}_{metric_name}.csv")
                        df.to_csv(output_file, index=False)
                        print(f"[Saved] {metric_name} -> {output_file}")

    print("\n[Done] All requested evaluations completed.")

if __name__ == "__main__":
    main()