from handlers.basehandler import OpenAImod,MistralMod
import json
import os
import tiktoken 

enc = tiktoken.encoding_for_model("gpt-4")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "config.json")

with open(file_path, "r", encoding="utf-8") as f:
    prefs = json.load(f)

handlers = {
    "openai":OpenAImod,
    "mistral":MistralMod
}

ordered = {
        **({prefs["default"]: handlers[prefs["default"]]} if prefs["default"] in handlers else {}),
        **{k: v for k, v in handlers.items() if k != prefs["default"]}
        }

def get_llm(sel_by_token=False, prompt=""):
    if not sel_by_token:
     
        for key, creator in ordered.items():
            try:
                print(f"[+] Trying {key}...",ordered.items(),creator.is_up())
                if creator.is_up():  
                    return key, creator()  
                else:
                    continue
            except Exception as e:
                print(f"[x] Error with {key}: {e}")
                print(f"[+] Falling back to next handler...")
            continue  # Importante: continua al prossimo handler
        
      
        raise RuntimeError("Couldn't start any handler - all failed")
        return None
    
    # la funzione viene chiamata per scegliere il server in base ai token OpenAI disponibili
    elif sel_by_token and prompt != "":
        tkns = len(enc.encode(prompt))
        low = prefs["openai"]["down"]
        high = prefs["openai"]["up"]
        
       
        if low <= tkns <= high and "openai" in handlers:
            print(f"[+] Tokens {tkns} in OpenAI range ({low}-{high}), trying OpenAI first")
            try:
                return "openai",handlers["openai"]()  
            except Exception as e:
                print(f"[x] Error starting OpenAI: {e}")
                print(f"[+] Falling back to preference order...")
        
        # Fallback su tutti gli altri handler nell'ordine di preferenza
        for key, creator in ordered.items():
            try:
                print(f"[+] Fallback: trying {key}...")
                return key, creator()  # Istanzia la classe
            except Exception as e:
                print(f"[x] Error with {key}: {e}")
                continue  # Continua al prossimo
        
        raise RuntimeError("Couldn't start any handler - all failed")
        return None
    
    else:
        raise ValueError("Must specify a prompt when using sel_by_token=True")
        return None
