import os
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_code(self, system_prompt: str, user_prompt: str) -> tuple:
        """Returns (code: str, usage_stats: dict)"""
        pass

class AnthropicProvider(LLMProvider):
    def generate_code(self, system_prompt: str, user_prompt: str) -> tuple:
        from anthropic import Anthropic, AuthenticationError
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "\n" + "="*70 +
                "\n🔑 ANTHROPIC API KEY NOT FOUND" +
                "\n" + "="*70 +
                "\nThe ANTHROPIC_API_KEY environment variable is not set." +
                "\n\nTo fix this, run one of the following:" +
                "\n\n  PowerShell:" +
                "\n  $env:ANTHROPIC_API_KEY = 'your-api-key-here'" +
                "\n\n  Command Prompt:" +
                "\n  set ANTHROPIC_API_KEY=your-api-key-here" +
                "\n\nGet your API key at: https://console.anthropic.com/keys" +
                "\n" + "="*70 + "\n"
            )
        
        try:
            client = Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5", 
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            # Extract usage stats from response
            usage_stats = {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "model": "claude-haiku-4-5"
            }
            # FIX: Extract the text field from the first item in the content list
            return message.content[0].text, usage_stats
        except AuthenticationError as e:
            raise RuntimeError(
                "\n" + "="*70 +
                "\n❌ ANTHROPIC AUTHENTICATION FAILED" +
                "\n" + "="*70 +
                "\nYour API key is invalid or expired." +
                "\n\nPlease:" +
                "\n  1. Visit https://console.anthropic.com/keys" +
                "\n  2. Generate a new API key" +
                "\n  3. Update your ANTHROPIC_API_KEY environment variable" +
                "\n\nError details: " + str(e) +
                "\n" + "="*70 + "\n"
            )


class OpenAIProvider(LLMProvider):
    def generate_code(self, system_prompt: str, user_prompt: str) -> tuple:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        )
        usage_stats = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "model": "gpt-4o"
        }
        return response.choices[0].message.content, usage_stats

class OllamaProvider(LLMProvider):
    def generate_code(self, system_prompt: str, user_prompt: str) -> tuple:
        import requests
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "qwen2.5-coder:7b",
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False
        }
        response = requests.post(url, json=payload).json()
        usage_stats = {
            "input_tokens": 0,  # Ollama doesn't provide token counts
            "output_tokens": 0,
            "model": "qwen2.5-coder:7b (local)"
        }
        return response['response'], usage_stats

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
