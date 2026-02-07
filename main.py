import subprocess
import multiprocessing as mp
import json
import time
import yaml
import queue 
from pathlib import Path
from datetime import datetime
from handlers.stthandler import run_stt
from handlers.camera import run_video
from chatbot import ChatBot
from rag_diary import cosine, extractday
from openai import OpenAIError

BASEPATH = Path(__file__).parent 

TEMP_TTS_FILE = BASEPATH / "temp_tts_input.txt"

with open(f"{BASEPATH}/config.json", "r", encoding="utf-8") as f:
    conf_file = json.load(f)
file_path = f"{BASEPATH}/interact/cache.txt"
with open(f"{BASEPATH}/memories/whoami.yaml", "r") as f:
    yaml_conf = yaml.safe_load(f)

language = conf_file['language']
yaml_conf = yaml_conf[language]


 
    
MODELPATH = conf_file["paths"]["PIPERPATH_MODEL"] 
CONFIGPATH = conf_file["paths"]["PIPERPATH_CONFIG"]  

chatbot = ChatBot()
chatbot.update_chatbot_params(**{
    "personality": yaml_conf['robot_personality'],
    "chat_instructions": yaml_conf['robot_chat_instructions']
    }
)

agent = ChatBot()
agent.update_chatbot_params(**{
    "personality":yaml_conf['agent_personality']},
    )

rag_content=""

print(f"YAML Loaded: {yaml_conf.keys()}")

def recognize_speaker(people_seen: list, voices_data: dict, last_voice: str):
    
    if len(people_seen) == 0:
        if voices_data['confidence'] >= 0.5:
            return voices_data['name']
        else:
            return last_voice
    if len(people_seen) == 1:
        if voices_data['confidence'] >= 0.8:
            return voices_data['name']
        else:
            return people_seen[0]
    if len(people_seen) >= 2:
        if voices_data['confidence'] >= 0.8 or voices_data['name'] in people_seen:
            return voices_data['name']
        else:
            return last_voice 
    

def speak(bot: ChatBot, prompt: str, info: list, pause_listening, queue_obj, rag_content: str = ""):
    # Pause listening
    pause_listening.set()
    
    ##DIFFERENZAÌIARE BENE PROMPT DELLA CHAT E ISTRUIZONI PER RISPONDERE! Mosidicare eventualmente la classe per usare il ruolo [system] in questi casi
    
    if info!=['']:
        new_prompt = yaml_conf['speak_with_context'].format(objects=", ".join(info), prompt=prompt)
    else:
        new_prompt = yaml_conf['speak_no_context'].format(prompt=prompt)

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
    #fare dei test perchè non ricordo come ho gestito il fallback nel caso in cui il modello abbiadei problemi durante l'uso. Nel caso,
    #potrei provare con exception Chatbot.update_llm() dentro speak() e vedere se funziona.
    
    
    audio_queue = mp.Queue()
    video_queue = mp.Queue()
    pause_listening = mp.Event() #
    
    objects_seen = [""]
    rag_content = ""
    last_voice = "Unknown"
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
                    voice_packet = result
                    
                    
                    if result_text:
                        print(f"\nRecorded sentence: {result_text}")
                        
                        agentfilter = agent.text_response(prompt=yaml_conf['filter_prompt'].format(result_text=result_text), user_params={"max_tokens":5}).lower()

                        if "[ok]" in agentfilter:
                            last_voice = recognize_speaker(objects_seen, voice_packet, last_voice)
                            print(f"Speaker recognized as: {last_voice}")

                            if len(result_text) > 20:
                                agentyesno = agent.text_response(prompt=yaml_conf['rag_decision'].format(result_text=result_text), user_params={"max_tokens":5}).lower()

                                if "[yes]" in agentyesno:
                                    try:
                                        rrr = agent.text_response(prompt=yaml_conf['rag_selection'].format(todaydate=todaydate, result_text=result_text), user_params={"max_tokens":20})

                                        if "[yes" in rrr.lower():
                                            date_str = rrr.split(",")[1].strip().replace("]", "")
                                            rag_content = extractday(date_str)
                                        else:
                                            rag_content = cosine(result_text)
                                    except Exception as e:
                                        print(f"RAG Error: {e}")
                                        rag_content = ""

                            speak(chatbot, result_text, objects_seen, pause_listening, audio_queue, rag_content=rag_content)

                        if "[inc]" in agentfilter:
                            pass
                
                except queue.Empty:
                    break    
                except OpenAIError as e:
                    ChatBot.get_llm()
                    print(f"OpenAI error in loop: {e}. Trying to switch LLM...")
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