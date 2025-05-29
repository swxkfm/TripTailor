from openai import OpenAI
import warnings
warnings.filterwarnings("ignore")
class ChatClient:

    def __init__(self, model_name="", api_key='', base_url=''):
        self.model_name = model_name
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
           
    def chat_completion(self, user_message: str, temperature=1) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": user_message}],
            temperature=temperature
        )
        return response.choices[0].message.content
