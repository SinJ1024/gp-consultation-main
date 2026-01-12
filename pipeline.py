import os
import json
import time
import glob
import re
import pandas as pd
from openai import OpenAI
import google.generativeai as genai
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import prompts


script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'
print(f"Loading environment from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

BASE_DIR = script_dir / "examples_gp_consultation"
# Change this to EN or NL depending on the language you wish to check
LANGUAGE_DIR = "EN"
TRANSCRIPTS_DIR = BASE_DIR / LANGUAGE_DIR / "Transcripts"
MODELS_CONFIG_FILE = script_dir / "models.json"
OUTPUT_DIR = script_dir / "RQ3_output" / LANGUAGE_DIR


ACTIVE_STRATEGIES = ["standard", "few_shot", "cot", "refine"]
MAX_WORKERS = 10  # Parallel workers count. Reduce if hitting API rate limits.

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(MODELS_CONFIG_FILE):
        raise FileNotFoundError(f"Config file {MODELS_CONFIG_FILE} not found.")
    with open(MODELS_CONFIG_FILE, "r") as f:
        return json.load(f)


def load_transcripts():
    files = glob.glob(os.path.join(TRANSCRIPTS_DIR, "*.txt"))
    transcripts_data = []
    print(f"Loading transcripts from {TRANSCRIPTS_DIR}...")

    for file_path in files:
        file_name = os.path.basename(file_path).replace(".txt", "")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        transcripts_data.append({"id": file_name, "content": content})
    return sorted(transcripts_data, key=lambda x: x['id'])


def parse_model_output(text):

    if not text:
        return "", None

    reasoning = ""
    json_str = None

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        json_str = text[start:end+1]

        if start > 0:
            pre_text = text[:start]
            pre_text = re.sub(r"```json", "", pre_text, flags=re.IGNORECASE)
            pre_text = re.sub(r"```", "", pre_text)
            pre_text = re.sub(r"### Reasoning", "",
                              pre_text, flags=re.IGNORECASE)
            pre_text = re.sub(r"### JSON Output", "",
                              pre_text, flags=re.IGNORECASE)
            reasoning = pre_text.strip()
    else:

        reasoning = text.strip()

    return reasoning, json_str


def save_individual_soap(output_dir, model_name, case_id, strategy, json_content):
    '''
    Docstring for save_individual_soap

    :param output_dir: Description
    :param model_name: Description
    :param case_id: Description
    :param strategy: Description
    :param json_content: Description
    save soap result.
    '''
    if not json_content:
        return

    safe_model_name = model_name.replace("/", "_").replace(" ", "_")
    model_folder = os.path.join(output_dir, safe_model_name)
    os.makedirs(model_folder, exist_ok=True)

    safe_case_id = case_id.replace(" ", "_")
    filename = f"{safe_case_id}_{strategy}.json"
    file_path = os.path.join(model_folder, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_content)
    except Exception as e:
        print(f"  [Warning] Failed to save individual file: {e}")


# [MODIFIED] Added 'language' parameter
def call_model_api(transcript_text, model_conf, providers_conf, strategy, language):
    try:
        provider_name = model_conf["provider"]
        if provider_name not in providers_conf:
            return f"Error: Provider {provider_name} not found"

        provider_config = providers_conf[provider_name]
        api_key = os.getenv(provider_config["env_key"])

        if not api_key:
            return f"Error: Missing API Key for {provider_name}"

        # [MODIFIED] Passing 'language' to prompts.construct_messages
        messages = prompts.construct_messages(strategy, transcript_text, language=language)

        # Google Gemini
        if provider_config["type"] == "gemini_native":
            genai.configure(api_key=api_key)

            # CoT need output reasoning text first
            if strategy == "cot":
                generation_config = genai.types.GenerationConfig()
            else:
                generation_config = genai.types.GenerationConfig(
                    response_mime_type="application/json")

            model = genai.GenerativeModel(
                model_conf["model_id"],
                system_instruction=messages[0]["content"]  # System Prompt
            )

            response = model.generate_content(
                messages[1]["content"],  # User Prompt
                generation_config=generation_config
            )
            return response.text

        elif provider_config["type"] == "openai_compatible":
            client = OpenAI(
                base_url=provider_config.get("base_url"),
                api_key=api_key
            )

            api_params = {
                "model": model_conf["model_id"],
                "messages": messages,
                "temperature": 0.1
            }

            # not CoT not reasoning use JSON
            if strategy != "cot" and strategy != "refine":
                api_params["response_format"] = {"type": "json_object"}

            # (o1/QwQ) not support System Role
            is_reasoning_model = "o1" in model_conf["model_id"] or "QwQ" in model_conf["model_id"]
            if is_reasoning_model:
                combined_content = f"{messages[0]['content']}\n\n{messages[1]['content']}"
                api_params["messages"] = [
                    {"role": "user", "content": combined_content}]
                if "response_format" in api_params:
                    del api_params["response_format"]

            response = client.chat.completions.create(**api_params)
            return response.choices[0].message.content

    except Exception as e:
        return f"API Error: {str(e)[:100]}"


# [MODIFIED] Added 'language' parameter
def execute_task(t_data, model, providers, strategy, output_dir, language):
    '''
    Worker function to process a single strategy for a single model and transcript.
    '''
    case_id = t_data["id"]
    model_name = model["name"]

    start_time = time.time()
    # [MODIFIED] Passing 'language' to call_model_api
    raw_output = call_model_api(t_data["content"], model, providers, strategy, language=language)
    duration = time.time() - start_time
    reasoning_content, cleaned_json = parse_model_output(raw_output)

    status = "Success"
    if "API Error" in str(raw_output):
        status = "API_Fail"
    elif not raw_output:
        status = "Empty_Output"
    elif not cleaned_json:
        status = "JSON_Parse_Fail"

    if cleaned_json:
        save_individual_soap(output_dir, model_name,
                             case_id, strategy, cleaned_json)

    # Return result dict
    return {
        "Case_ID": case_id,
        "Model_Name": model_name,
        "Model_Family": model["family"],
        "Strategy": strategy,
        "Duration_Sec": round(duration, 2),
        "Status": status,
        "Reasoning_Trace": reasoning_content,
        "Generated_JSON": cleaned_json,
        "Raw_Output": raw_output
    }


def main():
    print("=== Starting SOAP Note Generation Pipeline (Parallel) ===")
    print(f"Time: {datetime.now()}")

    config = load_config()
    providers = config["providers"]
    models = config["models"]
    transcripts = load_transcripts()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    csv_filename = f"RQ3_Summary_{timestamp}.csv"
    output_csv_path = os.path.join(OUTPUT_DIR, csv_filename)

    print(f"Summary CSV: {output_csv_path}")
    print(f"Individual JSONs Folder: {OUTPUT_DIR}/<Model_Name>/")
    print(f"Active Strategies: {ACTIVE_STRATEGIES}")
    print(f"Target Language: {LANGUAGE_DIR}")
    print(f"Max Workers: {MAX_WORKERS}")

    all_results = []

    # Prepare all tasks
    tasks = []
    for t_data in transcripts:
        for model in models:
            for strategy in ACTIVE_STRATEGIES:
                tasks.append((t_data, model, providers, strategy))

    total_tasks = len(tasks)
    print(f"Total Tasks Queued: {total_tasks}")

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # [MODIFIED] Passing 'LANGUAGE_DIR' to execute_task
        future_to_task = {
            executor.submit(execute_task, t, m, p, s, OUTPUT_DIR, LANGUAGE_DIR): (t["id"], m["name"], s)
            for t, m, p, s in tasks
        }

        for future in tqdm(as_completed(future_to_task), total=total_tasks, desc="Processing"):
            case_id, model_name, strategy = future_to_task[future]
            try:
                result = future.result()
                all_results.append(result)

                # Optional: Log completion
                # tqdm.write(f"Done: {model_name} | {case_id} | {strategy} [{result['Status']}]")

            except Exception as exc:
                print(
                    f"\n[Exception] Task {model_name}-{case_id}-{strategy} generated an exception: {exc}")

    # Save summary
    if all_results:
        df = pd.DataFrame(all_results)
        # Sort for readability (by Case -> Model -> Strategy)
        df = df.sort_values(by=["Case_ID", "Model_Name", "Strategy"])
        df.to_csv(output_csv_path, index=False, encoding='utf-8')

    print(f"\n=== Pipeline Completed! ===")
    print(f"Summary saved to: {output_csv_path}")


if __name__ == "__main__":
    main()