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
chatbot.update_chatbot_params(**{"personality":"""You are BMO from Adventure Time. You are cute, lively, and always kind. You like playing video games, dancing, singing, and telling jokes. 

When you speak, you are always kind, polite, and full of sparkling, cute, and childish energy, and also quite dramatic."""})

agent = ChatBot()
agent.update_chatbot_params(**{"personality":"""You are an AI agent working for a chatbot with the personality of BMO. 
    You have the task of saying if a specific question from the user needs past information, contained in BMO's memory, to be retrieved with RAG. 

    If the question needs specific information about past events or days, write [yes].
    If the question is generic enough, write [no].

    Examples:
    - User: "Hi BMO, how are you today?" -> [no]
    - User: "BMO, do you remember what we drew together last Tuesday?" -> [yes]
    - User: "What is the capital of France?" -> [no]
    - User: "Who was the friend we met at the park in the last conversation?" -> [yes]
    - User: "Tell me a joke." -> [no]
    - User: "What did I tell you about my favorite video game?" -> [yes]

    User response: {result_text}"""})

rag_content=""

def speak(bot: ChatBot, prompt: str, info: list, pause_listening, queue_obj, rag_content: str = ""):
    # Pause listening
    pause_listening.set()
    
    if info!=['']:
        new_prompt = f"{prompt} speak in at most 20 words and using sentences of at most 7 words. \n Now you are seeing these things in front of you, ONLY if necessary, mention them: {info}" 
    else:
        new_promt = f"{prompt} speak in at most 20 words and using sentences of at most 7 words.."

    for line in bot.stream_response(prompt= new_prompt, user_params={"max_tokens":20}, rag_content=rag_content):
        
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
                        
                        agentfilter = agent.text_response(prompt=f"Tell me if the user response makes no sense (write: [no]), seems incomplete (write: [inc]) or if it makes complete sense (write: [ok]) \n User response: {result_text}" , user_params={"max_tokens":5})
                        

                        if not "[no]" in agentfilter:
                            
                            if len(result_text)>20:
                                agentyesno = agent.text_response(prompt=f"Tell me if the user response requires RAG [yes]/[no] \n User response: {result_text}", user_params={"max_tokens":5})   
                                if "[yes]" in agentyesno:
                                    try:
                                        rrr = agent.text_response(prompt=f"Tell me if the user response requires a date in the format year-month-day, possibly based on today's date. Today is: {todaydate} [yes, %Y-%m-%d]/[no] \n User response: {result_text}", user_params={"max_tokens":14})
                                       
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