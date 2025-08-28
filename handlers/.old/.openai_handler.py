
#included in basehandler.py
from openai import OpenAI
from basehandler import BaseMod

    


class OpenAImod(BaseMod):
    
    client = OpenAI(api_key=API_KEY)
    default_params = {
        "max_tokens": 100,
        "temperature": 1.0,
        "stop": ["\n\n"]
    }

    chatbot_params = {
        "personality": "",
        "chat_instructions": "",
        "action_instructions": "",
    }

    
    @classmethod
    def check_health(cls):
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

    

    def __init__(self):
        super().__init__()
        try:
            self.check_health()
        except Exception as e:
            print("[X]Erron while initializating istance of OpenAI: ",str(e))


  

    def get_chat_recap(self):
        chat_content = self.get_chat_as_string(True)
        recap_prompt = f"I'll give you a chat. Make a brief summary of max 50 words, tell me ONLY and strictly ehat they are talking about and use ONLY descriptive talking like if you are describing a scenario:\n'{chat_content}'"

        response = self.client.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  recap_prompt}
            ],
            max_tokens=100,
            temperature=1.0,
        )

        return response["choices"][0]["message"]["content"].strip()

   

    def text_response(self, prompt: str,  rag_content : str =  "", user_params: dict = {},):
        if rag_content != "":
            self.add_rag_content(rag_content)
        self.chat.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=self.chat,
                **{**self.default_params, **user_params}
            )
           # print(response.dict())
            message = response.model_dump()["choices"][0]["message"]["content"]
            self.chat.append({"role": "assistant", "content": message})
            return message
        except Exception as e:
            self.chat.pop()
            return f"Error in generating response:\n {e}"

    def stream_response(self, prompt: str, rag_content : str = "",user_params: dict = {}):
        if rag_content != "":
            self.add_rag_content(rag_content)
            
        self.chat.append({"role": "user", "content": prompt})
        message = ""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=self.chat,
                stream=True,
                **{**self.default_params, **user_params}
            )
            
            print(response)

            for chunk in response:
                delta = chunk["choices"][0]["delta"]
                content = delta.get("content", "")
                if content:
                    message += content
                    print(content, end="")
                    
            self.chat.append({"role": "assistant", "content": message})
            return message

        except Exception as e:
            print(str(e))
            self.chat.pop()
            
            
  
        
if __name__ == "__main__":
    c = {
        "personality":"You are BMO of adventure time, you are a kind and lovely robot who loves to play and dance, You are ALWAYS gentle, happy and kind with a lot of childish energy."
    }
    
    OpenAImod.set_chat_config(**c)
    server = OpenAImod()
    print(server.text_response("HIII"))

