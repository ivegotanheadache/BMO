import json
import queue
import threading 
import sys
import time
import os
import multiprocessing as mp
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SpkModel 
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# --- CONFIGURAZIONE ---
BASEPATH = Path(__file__).parent.parent 
CONFIG_FILE = BASEPATH / "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    conf_file = json.load(f)
    
MODEL_PATH = conf_file["paths"]["VOSKPATH"]
SPK_MODEL_PATH = str(BASEPATH / "stt" / "vosk-model-spk-0.4")
VOICES_FILE = str(BASEPATH / "stt" / "known_voices.json")
CONFIDENCE_THRESHOLD = 0.5 

# --- VARIABILI GLOBALI PER IL CALLBACK ---
internal_audio_buffer = queue.Queue()  # QUESTA RESTA queue.Queue (threading)
global_pause_event = None 

def load_voices():
    if os.path.exists(VOICES_FILE):
        try:
            with open(VOICES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Audio callback
def callback(indata, frames, time_info, status):
    if status:
        print(status)
    
    # Se NON siamo in pausa, registriamo
    if not global_pause_event.is_set():
        internal_audio_buffer.put(bytes(indata))
        

# --- FUNZIONE PRINCIPALE ---
def run_stt(main_output_queue, pause_event):
    import os
    pid = os.getpid()
    print(f"[STT] AVVIO PROCESSO - PID: {pid}")
    
    global global_pause_event
    global_pause_event = pause_event
    
    # Carichiamo i modelli dentro il processo
    try:
        model = Model(MODEL_PATH)
        spk_model = SpkModel(SPK_MODEL_PATH)
    except Exception as e:
        print(f"[STT] Errore modelli: {e}")
        return
    
    known_voices = load_voices()
    samplerate = 32000
    rec = KaldiRecognizer(model, samplerate, spk_model)
    
    print("[STT] Avviato.")
    
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, channels=1, dtype='int16', callback=callback):
        while True:
            # Gestione Pausa: svuota buffer e attendi
            if pause_event.is_set():
                time.sleep(0.1)
                continue
            
            # Preleva audio dalla coda interna
            try:
                data = internal_audio_buffer.get()
            except queue.Empty:
                continue
            
            if rec.AcceptWaveform(data):
                result_json = json.loads(rec.Result())
                text = result_json.get('text', '')
                spk_vector = result_json.get('spk') 
                
                if text.strip():
                    packet = {
                        "voice": "Unknown",
                        "text": text,
                        "confidence": 0.0
                    }
                    
                    if spk_vector and len(text) > 5:
                        best_score = -1.0
                        best_voice = "Unknown"
                        
                        for name, vector in known_voices.items():
                            try:
                                score = cosine_similarity([spk_vector], [vector])[0][0]
                            except:
                                score = 0
                            
                            if score > best_score:
                                best_score = score
                                best_voice = name
                        
                        if best_score > CONFIDENCE_THRESHOLD:
                            packet["voice"] = best_voice
                            packet["confidence"] = float(best_score)
                    
                    # INVIA AL MAIN (Coda Esterna - multiprocessing.Queue)
                    try:
                        main_output_queue.put(packet)
                    except Exception as e:
                        print(f"[STT] Errore invio a main: {e}")
                        
if __name__=="__main__":
    q= queue.Queue()
    m = mp.Event()
    run_stt(q,m)