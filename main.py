import subprocess
import multiprocessing as mp
import json
import sys
import time
import queue 
from pathlib import Path
from datetime import datetime
from handlers.stthandler import run_stt
from handlers.camera import run_video
from chatbot import ChatBot
from rag_diary import cosine, extractday

BASEPATH = Path(__file__).parent 

TEMP_TTS_FILE = BASEPATH / "temp_tts_input.txt"

with open(f"{BASEPATH}/config.json", "r", encoding="utf-8") as f:
    conf_file = json.load(f)
file_path = f"{BASEPATH}/interact/cache.txt"
    
MODELPATH = conf_file["paths"]["PIPERPATH_MODEL"] 
CONFIGPATH = conf_file["paths"]["PIPERPATH_CONFIG"]  

chatbot = ChatBot()
chatbot.update_chatbot_params(**{"personality":"Sei BMO di adventure time, se simpatico, vivace e sempre gentile, ti piace giocare ai videogiochi, ballare, cantare e raccontare battute. Quando parli sei sempre gentile e cortese e pieno di energia frizzante, carina e infantile, e anche abbastanza drammatica"})

agent = ChatBot()
agent.update_chatbot_params(**{"personality":"Sei un agente AI che lavore per un chatbot con la personalità di BMO. HAi il compito di dire se una determinats domanda da parte dell'utente necessita di informazioni passate, contenute nella memoria di BMO, da prendere con la RAG. Se la domanda necessita informazioni specifiche eventi passate o giornate, scrivi [yes], altrimenti se la domanda è abbastanza generica [no]"})

rag_content=""

def speak(bot: ChatBot, prompt: str, info: list, pause_listening, queue_obj, rag_content: str = "a"):
    # Pause listening
    pause_listening.set()
    
    if info!=['']:
        prompt = f"{prompt} parla in massimo 17 parole e usando frasi di massimo 7 parole. \n  Adesso stai vedendo difronte a te queste cose, SOLO se necessario, citale: {info}" 
    else:
        f"{prompt} parla in massimo 17 parole e usando frasi di massimo 7 parole."

    for line in bot.stream_response(prompt= prompt, user_params={"max_tokens":20}, rag_content=rag_content):
        
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
        aplay_proc = subprocess.Popen(aplay_cmd, stdin=piper_proc.stdout)

        piper_proc.stdout.close()
        aplay_proc.communicate() 
        
    while not queue_obj.empty():
        queue_obj.get()

    pause_listening.clear()


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    
    ChatBot.load_llm()
    
    audio_queue = mp.Queue()
    video_queue = mp.Queue()
    pause_listening = mp.Event() #
    
    objects_seen = [""]
    rag_content=""
    todaydate = datetime.now().strftime("%Y-%m-%d")

    face_process = subprocess.Popen(["python3", "face.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
   
    listen = mp.Process(target=run_stt, args=(audio_queue, pause_listening)) 
    camera = mp.Process(target=run_video, args=(video_queue,))
    
    listen.start()
    camera.start()
    
    try:
        while True:
            
            while not video_queue.empty():
                try:
                    objects_seen = video_queue.get_nowait() 
                    print(f"Oggetti visti: {objects_seen}")
                except queue.Empty:
                    break
            
            
            while not audio_queue.empty():
                try:
                    result = audio_queue.get_nowait()
                    result_text = result["text"] 
                    
                    if result_text:
                        print(f"\nRecorded sentence: {result_text}")
                        
                        agentfilter = agent.text_response(prompt=f"Dimmi se la risposta utente non ha senso (scrivi: [no]), sembra incompleta (scrivi: [inc]) oppre se ha senso compiuto (scrivi: [ok]) \n Risposta utente: {result_text}",  user_params={"max_tokens":5})
                        

                        if not "[no]" in agentfilter:
                            
                            if len(result_text)>20:
                                agentyesno = agent.text_response(prompt=f"Dimmi se la risposta utente neccessita RAG [yes]/[no] \n Risposta utente: {result_text}", user_params={"max_tokens":5})   
                                if "[yes]" in agentyesno:
                                    try:
                                        rrr = agent.text_response(prompt=f"Dimmi se la risposta utente neccessita di una data nelformato anno-mese-giorno, pasandoti eventualmente sulla data di oggi. Oggi è: {todaydate} [yes, %Y-%m-%d]/[no] \n Risposta utente: {result_text}", user_params={"max_tokens":14})
                                       
                                        if "yes" in rrr:
                                            r, date_str = rrr[1:-1].split(", ")
                                            rag_content = extractday(date_str)
                                        else:
                                            rag_content = cosine(result_text)
                                    except Exception as e:
                                        print(f"RAG Error: {e}")
                                        rag_content=""

                            speak(chatbot, result_text, objects_seen, pause_listening, audio_queue, rag_content=rag_content)
            
                        if "[inc]" in agentfilter:
                            pass
                
                except queue.Empty:
                    break    
                except Exception as e:
                    print(f"Error in loop: {e}")
                    break
                
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n? [+] BMO is going to sleep... ")
    
    except Exception as e:
        print(f"\n?[X] BMO Critic error! {e}")
        import traceback
        traceback.print_exc()
                
    finally:
        try:
            resume = chatbot.get_chat_recap()
            with open(f"{BASEPATH}/memories/diary.txt", "a") as f:
                f.write("[page]\n"+todaydate+"[date]"+resume+"\n")
        except Exception as e:
            print(f"[+] Error in writing in diary.txt : {e}")
        
        listen.terminate()
        camera.terminate()
        face_process.terminate()