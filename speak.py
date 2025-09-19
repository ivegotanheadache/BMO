import os
import json
import time
import threading
import subprocess
import sounddevice as sd
import queue
import sys
from vosk import Model, KaldiRecognizer, SetLogLevel
from chatbot import ChatBot
from pathlib import Path
SetLogLevel(0)

############################################
# Paths


BASEPATH = Path(__file__).parent 
with open(f"{BASEPATH}/config.json", "r", encoding="utf-8") as f:
    conf_file = json.load(f)
    
MODELPATH = conf_file["paths"]["PIPERPATH_MODEL"] #path to piper voice, without ".gguf" at the end 
CONFIGPATH = conf_file["paths"]["PIPERPATH_CONFIG"]  #path to json piper
VOSKMODEL = conf_file["paths"]["VOSKPATH"] #path - name of vosk model
file_path = f"{BASEPATH}/interact/cache.txt"

# Audio
q = queue.Queue()
samplerate = 32000

pause_listening = threading.Event()
pause_listening.clear()

###########################################
def speak(bot: ChatBot, prompt: str):
    # Pause listening
    pause_listening.set()
    #print(bot.chat_config, bot.chat)
    for line in bot.stream_response(prompt=prompt, user_params={"max_tokens":15}):
        #print("Line: ",line)
        with open(file_path, 'w') as f:
            f.write(line)

        # Piper TTS command
        piper_cmd = [
            "piper",
            "--speaker", "3",
            "--model", MODELPATH,
            "--config", CONFIGPATH,
            "--input_file", file_path,
            "--output_raw",
            "--output_file", "-"  # Output to stdout
        ]

        sox_cmd = [
            "sox",
            "-t", "raw",             
            "-r", "23050",            # sample rate
            "-e", "signed",           # signed int
            "-b", "16",               # bit depth
            "-c", "1",                # mono
            "-",                      # stdin
            "-t", "wav", "-",        
            "tempo", "0.9",                 
            "highpass", "300",               # cut rumble
            "lowpass", "4000",               # toy speaker feel
            "compand", "0.3,1", "6:-70,-60,-20", "-5", "-90", "0.2",  # still compressed
            "rate", "8000",                  # simulate low-fi speaker
            "reverb", "10", "50", "20"
        ]

        
        
        
        
        # aplay command
        aplay_cmd = [
            "aplay",
            "-f", "S16_LE",
            "-r", "23050",
            "-c", "1"
        ]
        piper_proc = subprocess.Popen(piper_cmd, stdout=subprocess.PIPE)
        sox_proc = subprocess.Popen(sox_cmd, stdin=piper_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        aplay_proc = subprocess.Popen(aplay_cmd, stdin=sox_proc.stdout)

        piper_proc.stdout.close()
        sox_proc.stdout.close() 
        aplay_proc.communicate() 
        
    while not q.empty():
        q.get()

    pause_listening.clear()

###########################################
# Audio callback
def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    if not pause_listening.is_set():
        q.put(bytes(indata))

###########################################
model = Model(VOSKMODEL)
recognizer = KaldiRecognizer(model, samplerate)

# Initialize chatbot
chatbot = ChatBot()
chatbot.update_chatbot_params(**{"personality":"You are BMO of adventure time, you are a kind and lovely robot who loves to play and dance, You are ALWAYS gentle, happy and kind with a lot of childish energy."})








#input stream
with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    print("? Say something! Ctrl+C to stop.")
    #print(chatbot.chat_config)
    while True:
        if pause_listening.is_set():
            time.sleep(0.1)
            continue

        data = q.get()
        if recognizer.AcceptWaveform(data):
            result_json = json.loads(recognizer.Result())
            result_text = result_json.get('text', '')

            if result_text.strip():
                print("Recorded sentence:", result_text.strip())
                speak(chatbot, result_text)
            #print(chatbot.chat)
