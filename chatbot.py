from llmrouter import get_llm

class ChatBot:
    llm_name = None 
    llm_mod = None 
    
    @classmethod
    def load_llm(cls):
        cls.llm_name, cls.llm_mod= get_llm()
        
    
    
    def __init__(self):
        self.chatbot_params = {
            "personality": "",
            "chat_instructions": "",
            "action_instructions": "",
        }

        self.chat_config = self.chatbot_params["personality"] + "\n" + self.chatbot_params["chat_instructions"]

        self.chat = [
            {"role": "system", "content": self.chat_config},
        ]


    def update_chatbot_params(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self.chatbot_params:
                raise ValueError(f"Invalid chatbot param: {k}")
            self.chatbot_params[k] = v
        self.chat_config = self.chatbot_params["personality"] + self.chatbot_params["chat_instructions"]
        self.reset_chat()
        
    def update_chat(self, new_chat: str):
        if not new_chat.strip():
            return

        roles = {
            "User: ": "user",
            "System: ": "system",
            "Assistant: ": "assistant"
        }

        existing = {(entry["role"], entry["content"]) for entry in self.chat}

        for line in new_chat.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            for prefix, role in roles.items():
                if line.startswith(prefix):
                    content = line[len(prefix):].strip()
                    if (role, content) not in existing:
                        self.chat.append({"role": role, "content": content})
                    break
            else:
                print(f"[!] Warning: Skipping line with unknown role format: {line}")

    def get_chat_as_string(self, include_roles=True):
        lines = []
        for msg in self.chat:
            role = msg["role"].capitalize()
            content = msg["content"].strip()
            if include_roles:
                lines.append(f"{role}: {content}")
            else:
                lines.append(content)
        return "\n".join(lines)

    def reset_chat(self):
        self.chat = [
            {"role": "system", "content": self.chat_config},
        ]

    def summarize(self):
        recap = self.get_chat_recap()
        self.reset_chat()
        self.chat.append({"role": "system", "content": f"Resume of previous chat: {recap}"})
        return recap

    def add_rag_content(self, content):
        self.chat.append({
            "role": "assistant",
            "content": f"here is some additional content to retrieve information:\n{content}"
        })
        print(self.chat)

    def update_llm(self):
        newllm, llm = get_llm()
        if newllm != self.llm_name:
            self.llm_name = newllm
            self.llm_mod = llm

    def get_chat_recap(self):
        #self.update_llm()
        chat = self.get_chat_as_string(include_roles=True)
        return self.llm_mod.get_chat_recap(chat)

    def stream_response(self, prompt: str, rag_content: str = "", user_params: dict = {}):
        #self.update_llm()
        if rag_content:
            self.add_rag_content(rag_content)
        return self.llm_mod.stream_response(self.chat, prompt, user_params)

    def text_response(self, prompt: str, rag_content: str = "", user_params: dict = {}):
        #self.update_llm()
        if rag_content:
            self.add_rag_content(rag_content)
        return self.llm_mod.text_response(self.chat, prompt, user_params)

  