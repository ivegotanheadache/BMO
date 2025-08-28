#included in basehandler.py
import requests
import json
import sseclient
from basehandler import BaseMod
#IMPORT LOGGING?
LOCALURL = "http://192.168.1.52:9999"




##Spostare tuuto come modulo su rpi4 e usare l'apiserver unicamente come API dell'llm pure
class MistralMod(BaseMod):
    
    
    
    default_params = {
        "max_tokens": 100,
        "temperature":1.5,
        "repeat_penalty": 2,
        "mirostat_mode": 2,
        "mirostat_tau": 1.8,
        "stop": ["STOP"],
        
    }
    
    
    
    
    def __init__(self):
        super().__init__()
        try:
            requests.get(f"{LOCALURL}/")
            self.llm = requests.post(f"{LOCALURL}/llm/set")
        except Exception as e:
            print(f" Error server : {str(e)}")
        
    
    
  
    
    def get_chat_recap(self):
        chat_content = self.get_chat_as_string(True)
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
        r = requests.post(f"{LOCALURL}/llm/chat/completions",json=payload)
        print(r.json)
        #print(c, r["choices"][0]["text"] +'\n')
        return r["choices"][0]["text"] +'\n'
        
        
    
    
    ##stream response returns a text
    def stream_response(self, prompt: str, rag_content: str = "", user_params: dict = {}):
        if rag_content != "":
            self.add_rag_content(rag_content)
            
        self.chat.append({"role": "user", "content": prompt}) 

        # Prepare configuration
        full_config = {"messages": self.chat, **self.default_params, **user_params}

        headers = {
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }
        url = F"{LOCALURL}/generate/text/stream"
        
        # Usa stream=True per ricevere in streaming
        response = requests.post(url, json={'config': full_config}, headers=headers, stream=True)
        response.raise_for_status()

        # Usa sseclient per parsare gli eventi SSE
        client = sseclient.SSEClient(response)

        full_message = ""
        for event in client.events():
            try:
                
                data = json.loads(event.data)
                if data.get("type") == "chunk":
                    # Stampa il chunk in tempo reale
                    chunk_content = data.get("content", "")
                    print(chunk_content, end="", flush=True)
                    full_message +=chunk_content

                elif data.get("type") == "complete":
                    print("\n")  # Nuova riga alla fine
                    final_message = data.get("content", "")
                    full_message+=final_message
                    return full_message
                
                elif data.get("type") == "error":
                    print(f"\nError: {data.get('content', 'Unknown error')}")
                    return None

            except Exception as e:
                print(f"\nUnexpected error: {e}")
                continue
    
    
    def text_response(self, prompt: str,  rag_content : str =  "", user_params: dict = {},):
        if rag_content != "":
            self.add_rag_content(rag_content)
        self.chat.append({"role": "user", "content": prompt})
            
        full_config = {"stream": False,
                       "messages": self.chat, 
                       **self.default_params, 
                       **user_params, }
        
        
        try:
            r = requests.post(f"{LOCALURL}/llm/chat/completions", json={'config':full_config})
            self.chat.append({"role": "assistant", "content": r.text})
            return r.json()["choices"][0]["message"]["content"]# #message
                
        except Exception as e:
            self.chat.pop()
            return f"[X] Error in generating response:\n{e}"
        
        
    
    
   

# Example usage
if __name__ == "__main__":
    
    c = {
        "personality":"You are BMO of adventure time, you are a kind and lovely robot who loves to play and dance, You are ALWAYS gentle, happy and kind with a lot of childish energy."
    }
    MistralMod.set_chat_config(**c)
    Ll = MistralMod()
    #print(Ll.chatbot_params, Ll.chat_config)
    print(Ll.text_response(prompt="whats you name?!"))