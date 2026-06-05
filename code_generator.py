from providers import LLMFactory

class CodeGenerator:
    def __init__(self, provider_name: str):
        self.llm = LLMFactory.get_provider(provider_name)

    def generate_analytics_code(self, target_url: str, user_task: str, schema_profile: str) -> str:
        system_prompt = f"""You are an elite Databricks Data Engineer. Write clean Python code using pandas to process data from: '{target_url}'
        1. Read file using: df = pd.read_parquet('{target_url}')
        2. Assign final human-readable string output to a local variable named 'FINAL_OUTPUT'.
        3. Output raw python text only. Never wrap code blocks in markdown fences like ```python."""
        
        user_prompt = f"TASK: {user_task}\nSCHEMA:\n{schema_profile}\nWrite the processing script now."
        return self.llm.generate_code(system_prompt, user_prompt)
