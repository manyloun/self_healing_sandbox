import os
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_code(self, system_prompt: str, user_prompt: str) -> tuple:
        """Returns (code: str, usage_stats: dict)"""
        pass

class AnthropicProvider(LLMProvider):
    async def _generate_with_mcp(self, client, system_prompt: str, user_prompt: str) -> tuple:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        import json
        import os

        # We must use an absolute path or relative to current working directory
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"],
            env={**os.environ} # Pass environment variables so it has ALPHAVANTAGE_API_KEY
        )
        
        messages = [{"role": "user", "content": user_prompt}]
        usage_stats = {"input_tokens": 0, "output_tokens": 0, "model": "claude-haiku-4-5"}
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = await session.list_tools()
                
                anthropic_tools = []
                for tool in mcp_tools.tools:
                    anthropic_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    })
                
                while True:
                    response = client.messages.create(
                        model="claude-haiku-4-5", 
                        max_tokens=2000,
                        system=system_prompt,
                        messages=messages,
                        tools=anthropic_tools if anthropic_tools else None
                    )
                    
                    usage_stats["input_tokens"] += response.usage.input_tokens
                    usage_stats["output_tokens"] += response.usage.output_tokens
                    
                    if response.stop_reason != "tool_use":
                        for block in response.content:
                            if block.type == "text":
                                return block.text, usage_stats
                        return "", usage_stats
                    
                    # Claude wants to use a tool
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            try:
                                result = await session.call_tool(block.name, arguments=block.input)
                                tool_result_text = "\n".join(
                                    [c.text for c in result.content if hasattr(c, 'text')]
                                )
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": tool_result_text
                                })
                            except Exception as e:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {e}",
                                    "is_error": True
                                })
                    
                    messages.append({"role": "user", "content": tool_results})

    def generate_code(self, system_prompt: str, user_prompt: str) -> tuple:
        from anthropic import Anthropic, AuthenticationError
        import asyncio
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        
        try:
            client = Anthropic(api_key=api_key)
            return asyncio.run(self._generate_with_mcp(client, system_prompt, user_prompt))
        except AuthenticationError as e:
            raise RuntimeError(f"Anthropic Authentication Failed: {e}")


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
