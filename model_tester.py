import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI, NotFoundError, AuthenticationError, BadRequestError
import google.generativeai as genai

script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'
print(f"Loading environment from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

MODELS_CONFIG_FILE = script_dir / "models.json"

def load_config():
    """
    Load model and provider configurations from JSON file.
    """
    if not os.path.exists(MODELS_CONFIG_FILE):
        raise FileNotFoundError(f"Config file {MODELS_CONFIG_FILE} not found.")
    with open(MODELS_CONFIG_FILE, "r") as f:
        return json.load(f)

def test_model(model_conf, providers_conf):
    provider_name = model_conf["provider"]
    if provider_name not in providers_conf:
        return False, f"Provider {provider_name} not found"
        
    provider_config = providers_conf[provider_name]
    api_key = os.getenv(provider_config["env_key"])
    
    if not api_key:
        return False, f"Missing API Key for {provider_name}"

    test_message = "Hi"
    
    try:
        start_time = time.time()

        # --- Google Gemini Native ---
        if provider_config["type"] == "gemini_native":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_conf["model_id"])
            response = model.generate_content(
                test_message, 
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            if response.text:
                duration = round(time.time() - start_time, 2)
                return True, f"{duration}s"
            
        # --- OpenAI Compatible ---
        elif provider_config["type"] == "openai_compatible":
            client = OpenAI(
                base_url=provider_config.get("base_url"),
                api_key=api_key
            )
            
            is_reasoning_model = "o1" in model_conf["model_id"] or "QwQ" in model_conf["model_id"]
            
            api_params = {
                "model": model_conf["model_id"],
                "messages": [{"role": "user", "content": test_message}],
            }
            
            if not is_reasoning_model:
                api_params["max_tokens"] = 5
            
            client.chat.completions.create(**api_params)
            duration = round(time.time() - start_time, 2)
            return True, f"{duration}s"

    except NotFoundError:
        return False, "Model ID error"
    except BadRequestError as e:
        return False, f"Bad Request: {str(e)[:50]}..."
    except AuthenticationError:
        return False, "Auth Error: Invalid API Key"
    except Exception as e:
        return False, f"API Error: {str(e)[:100]}"

    return False, "Unknown Status"

def main():
    print(f"Time: {datetime.now()}")
    
    try:
        config = load_config()
    except Exception as e:
        print(f"Critical Error: {e}")
        return

    providers = config["providers"]
    models = config["models"]
    
    print(f"Found {len(models)} models to test.\n")
    
    working_models = []
    broken_models = []

    for idx, model in enumerate(models):
        model_name = model["name"]
        model_id = model["model_id"]
        
        print(f"[{idx+1}/{len(models)}] Testing {model_name:<25} ...", end=" ", flush=True)
        
        is_ok, result_msg = test_model(model, providers)
        
        if is_ok:
            print(f"DONE ({result_msg}) [Success]")
            working_models.append(model_name)
        else:
            print(f"DONE -> {result_msg} [Fail]")
            broken_models.append({
                "name": model_name, 
                "id": model_id, 
                "error": result_msg
            })

    print("\n" + "="*40)
    print(f"Active Models: {len(working_models)}")
    print(f"Failed Models: {len(broken_models)}")
    
    if broken_models:
        print("\nAction Required for models.json:")
        for m in broken_models:
            print(f"   - Remove {m['name']} (ID: {m['id']})")
            print(f"     Reason: {m['error']}")
    
    print(f"\n=== Check Completed at {datetime.now().strftime('%H:%M:%S')} ===")

if __name__ == "__main__":
    main()