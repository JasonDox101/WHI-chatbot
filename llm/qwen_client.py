from openai import OpenAI
from typing import List, Dict, Any
from config.settings import WHIConfig

class QwenLLMClient:
    """Qwen LLM client wrapper for medical data analysis."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=WHIConfig.DASHSCOPE_API_KEY,
            base_url=WHIConfig.DASHSCOPE_BASE_URL
        )
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from LLM."""
        try:
            completion = self.client.chat.completions.create(
                model=WHIConfig.MODEL_NAME,
                messages=messages,
                **kwargs
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")
    
    def generate_embedding_query(self, text: str) -> str:
        """Generate optimized query for retrieval."""
        messages = [
            {"role": "system", "content": "You are a professional medical research assistant, skilled at converting user questions into precise retrieval queries."},
            {"role": "user", "content": f"Please convert the following question into keyword queries suitable for retrieval in WHI medical data: {text}"}
        ]
        return self.generate_response(messages)