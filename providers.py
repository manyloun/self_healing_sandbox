import os
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        pass

class AnthropicProvider(LLMProvider):
    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        
        message = client.messages.create(
            model="claude-haiku-4-5", 
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        # FIX: Extract the text field from the first item in the content list
        return message.content[0].text


class OpenAIProvider(LLMProvider):
    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        )
        return response.choices.message.content

class OllamaProvider(LLMProvider):
    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        import requests
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "qwen2.5-coder:7b",
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False
        }
        response = requests.post(url, json=payload).json()
        return response['response']

class LLMFactory:
    @staticmethod
    def get_provider(provider_name: str) -> LLMProvider:
        providers = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
            "ollama": OllamaProvider
        }
        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return providers[provider_name]()
