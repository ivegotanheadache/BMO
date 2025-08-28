##SI tratta della classe generica per interagire con varie api, succcessivamente 
#se volessi integrare altri moduli, immagini o cose cosi lo faccio direttamente qui


import time


class BaseMod:
    
    
    default_params =  {}
    
    def is_up():
        pass
    
    @classmethod
    def update_default_params(cls, **kwargs):
        for k, v in kwargs.items():
            if k not in cls.default_params:
                raise ValueError(f"Invalid parameter: {k}")
            cls.default_params[k] = v
    
    
    
    def __init__(self):
        pass
    
    
    def get_chat_recap(self):
        pass
    
    
    def stream_response(self, chat:dict,  prompt: str, user_params: dict = {}):
        pass
    
    
    def text_response(self, chat:dict, prompt: str, user_params: dict = {}):
        pass
   
    
    '''
    def generate_action(self, prompt: str, user_params: dict = {}):
        if user_params is None:
            user_params = {}
            
        full_config = {"prompt": prompt, **self.default_params, **user_params}
        
        try:
            result = self.llm(**full_config)
        except Exception as e:
            return f"[X] Error in generating response:\n{e}"
        
        return result["choices"][0]["text"]
    '''
    
    
############################################################################# 

import requests
import json
import httpx
from httpx_sse import connect_sse
#IMPORT LOGGING?





##Spostare tuuto come modulo su rpi4 e usare l'apiserver unicamente come API dell'llm pure
class MistralMod(BaseMod):
    
    LOCALURL = #LOCALURL TO MISTRAL 
    
   
    default_params = {
        "max_tokens": 100,
        "temperature":1.5,
        "repeat_penalty": 2,
        "mirostat_mode": 2,
        "mirostat_tau": 1.8,
        "stop": ["STOP"],
        
    }
    @classmethod
    def is_up(cls):
        try:
            response = requests.get(f"{cls.LOCALURL}/")
            return response.ok  # True if status_code is 200-399
        except requests.RequestException:
            return False
    
    
    
    
    def __init__(self):
        super().__init__()
        try:
            requests.get(f"{self.LOCALURL}/")
            self.llm = requests.post(f"{self.LOCALURL}/llm/set")
        except requests.exceptions.ConnectionError as e:
            print(f" Error server : {str(e)}")
            raise RuntimeError
        
    
    
  
    
    def get_chat_recap(self, chat_as_string):
        chat_content=chat_as_string
        c = f"""I'll give you a chat. Make a brief summary of max 50 words, tell me ONLY and strictly ehat they are talking about and use ONLY descriptive talking like if you are describing a scenario: \n' {chat_content} ' """
        payload={
            "stream": False,
            "prompt": c,
            "max_tokens": 100,
            "temperature": 1,
            "repeat_penalty": 1.5,
            "mirostat_mode": 2,
            "mirostat_tau": 1,
            "stop": ["STOP"]
        }
        r = requests.post(f"{self.LOCALURL}/llm/chat/completions",json=payload)
        print(r.json())
        #print(c, r["choices"][0]["text"] +'\n')
        return r["choices"][0]["text"] +'\n'
        
        
    
    
    ##stream response returns a text
    def stream_response(self, chat: dict, prompt: str, user_params: dict = {}):
        
        chat.append({"role": "user", "content": prompt}) 

        # Prepare configuration
        full_config = {"messages": chat, **self.default_params, **user_params}

        headers = {
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }
        url = F"{self.LOCALURL}/generate/text/stream"
        
    
        full_message = ""
        bibi=""
        
        response = requests.post(
        url, 
        json={'config': full_config}, 
        headers=headers, 
        stream=True,
        timeout=10.0
        )
        response.raise_for_status()
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data = line[6:]  # Rimuovi 'data: '
                
                if data.strip() in ['[DONE]', 'DONE']:
                    break
                    
                if data.strip():  # Skip righe vuote
                    try:
                        event_data = json.loads(data)
                        cont= event_data['content']
                        print(cont, end="", flush=True)
                        full_message+=cont
                        bibi+=cont
                        if ("."  in cont) or ("?" in cont) or ("!" in cont):
                            yield bibi
                            bibi = " "
                        time.sleep(0.1)
                    except Exception as e:
                        print(str(e))
        yield bibi
        print()
        chat.append({"role": "assistant", "content": full_message})
        response.close()
        return full_message
        
            
      
    
    def text_response(self,chat:dict, prompt: str, user_params: dict = {},):
        chat.append({"role": "user", "content": prompt})
            
        full_config = {"stream": False,
                       "messages": chat, 
                       **self.default_params, 
                       **user_params, }
        
        
        try:
            r = requests.post(f"{self.LOCALURL}/llm/chat/completions", json={'config':full_config})
            chat.append({"role": "assistant", "content": r.text})
            return r.text
                
        except Exception as e:
            chat.pop()
            return f"[X] Error in generating response:\n{e}"
        
        
    
    
   

##################################################################################
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('API_KEY') 


class OpenAImod(BaseMod):
    
    @classmethod
    def is_up(cls):
        client = cls.client
        try:
            client.models.list()
            return True
        except client.error.AuthenticationError:
            print("[x] Errore: API key not valid.")
        except client.error.APIConnectionError:
            print("[X]Connection error to client servers.")
        except Exception  as e:
            print("[x] Error: ", str(e))
        return False
        
    client = OpenAI(api_key=API_KEY)
    default_params = {
        "max_tokens": 100,
        "temperature": 1.0,
        "stop": ["\n\n"]
    }


    def __init__(self):
        super().__init__()
        try:
            self.is_up( )
        except Exception as e:
            print("[X]Erron while initializating istance of OpenAI: ",str(e))


  

    def get_chat_recap(self, chat_as_string: str):
        chat_content = chat_as_string
        recap_prompt = f"I'll give you a chat. Make a brief summary of max 50 words, tell me ONLY and strictly ehat they are talking about and use ONLY descriptive talking like if you are describing a scenario:\n'{chat_content}'"

        response = self.client.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  recap_prompt}
            ],
            max_tokens=100,
            temperature=0.8,
        )

        return response["choices"][0]["message"]["content"].strip()

   

    def text_response(self, chat: dict, prompt: str, user_params: dict = {},):
        chat.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=chat,
                **{**self.default_params, **user_params}
            )
            message = response.model_dump()["choices"][0]["message"]["content"]
            chat.append({"role": "assistant", "content": message})
            return message
        except Exception as e:
            chat.pop()
            return f"Error in generating response:\n {e}"

    def stream_response(self, chat: dict, prompt: str, user_params: dict = {}):
        
        chat.append({"role": "user", "content": prompt})
        message = ""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=chat,
                stream=True,
                **{**self.default_params, **user_params}
            )
            
            bibi = ""
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    message += content
                    bibi += content
                    #print(content, (True if "." in content else False))
                    print(content, end="", flush=True) 
                    if ("."  in content) or ("?" in content) or ("!" in content) or (":" in content):
                        yield bibi
                        bibi = " "
                        
                    
                    time.sleep(0.1)
            yield bibi      
            chat.append({"role": "assistant", "content": message})
            
            return message

        except Exception as e:
            print(str(e))
            chat.pop()
            
            
  
        
