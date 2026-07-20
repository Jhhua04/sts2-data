import os
import time
import json
import requests

API_URL = "https://beta.spire-codex.com/api/"
ONE_WEEK_IN_SECONDS = 7 * 24 * 60 * 60

def get_json(filename, api_endpoint, keys_to_keep=None):
    url = API_URL + api_endpoint
    needs_update = True
    if os.path.exists(filename):
        file_age = time.time() - os.path.getmtime(filename)
        if file_age < ONE_WEEK_IN_SECONDS:
            needs_update = False

    if needs_update:
        try:
            print(f"Updating {filename} from API...")
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            api_data = res.json()
                
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(api_data, f, indent=4)
                
        except Exception as e:
            print(f"Warning: Could not update {filename} from API. Error: {e}")
            if not os.path.exists(filename):
                raise

    with open(filename, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    if keys_to_keep:
        if isinstance(data, list):
            return [{k: v for k, v in entry.items() if k in keys_to_keep} for entry in data]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if k in keys_to_keep}
    return data