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

# Strategy list as requested
STRATEGIES = ["standard", "fewshot", "cot", "refine"]
MAX_WORKERS = 10
LANGUAGES = ["NL"]

def process_case(case_id, model_json_dir, strategy, loader, evaluator):
    """
    Worker function: Process a single case for Conciseness evaluation.
    """
    # 1. Load Data
    data = loader.load_case_data(case_id)
    key_facts = data.get('key_facts', {})
    # transcript = data.get('transcript', "") # Commented out as fact_checking is disabled
    
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

    # 4. Evaluate (Conciseness only)
    try:
        # Fact checking and alignment are commented out per request
        # checking_report = evaluator.fact_checking(generated_soap, transcript)
        # alignment_report = evaluator.fact_alignment(generated_soap, key_facts)
        concise_report = evaluator.conciseness(generated_soap, key_facts)
    except Exception as e:
        print(f"[Err] {case_id} ({strategy}): {e}")
        return None

    # 5. Format Output
    res_con = {
        "Case_ID": case_id,
        "Overall_Score": concise_report['overall_score'],
        **{k: concise_report['scores'].get(k, 0) for k in ["Subjective", "Objective", "Assessment", "Plan"]}
    }
    
    return res_con

def main():
    print(f"[Init] Root: {PROJECT_ROOT}")
    
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
            # Iterate through all specified strategies
            for strategy in STRATEGIES:
                print(f'\n>> Model: {model_name} | Strategy: {strategy} [{lang}]')
                
                model_json_dir = os.path.join(current_gen_path, model_name)
                co_results = []
                
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    future_to_case = {
                        executor.submit(process_case, cid, model_json_dir, strategy, loader, evaluator): cid 
                        for cid in case_ids
                    }
                    
                    for future in tqdm(as_completed(future_to_case), total=len(case_ids), desc=f"Evaluating {strategy}"):
                        result = future.result()
                        if result:
                            co_results.append(result)

                # Save Conciseness Results
                os.makedirs(current_output_dir, exist_ok=True)
                
                if co_results:
                    df = pd.DataFrame(co_results).replace("N/A", pd.NA)
                    avg = df.mean(numeric_only=True)
                    avg['Case_ID'] = 'Average'
                    df.loc[len(df)] = avg
                    
                    output_file = os.path.join(current_output_dir, f"{model_name}_{strategy}_conciseness.csv")
                    df.to_csv(output_file, index=False)
                    print(f"[Saved] {output_file}")

    print("\n[Done] Conciseness evaluation for all strategies completed.")

if __name__ == "__main__":
    main()