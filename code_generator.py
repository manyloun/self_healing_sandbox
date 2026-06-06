from providers import LLMFactory

class CodeGenerator:
    def __init__(self, provider_name: str):
        self.llm = LLMFactory.get_provider(provider_name)

    def generate_analytics_code(self, target_url: str, user_task: str, schema_profile: str) -> str:
        """Generates explicit pandas parsing pipelines bound strictly by the Schema profile."""
        system_prompt = f"""You are an elite Databricks Data Engineer. Write clean Python code using pandas to process data from: '{target_url}'
        
        CRITICAL ENGINE LIMITS:
        1. You must read the data file using: df = pd.read_parquet('{target_url}')
        2. You MUST use the provided Schema Profile to verify column names. Do not invent or assume column structures.
        3. Assign your final human-readable string output to a local variable named 'FINAL_OUTPUT'.
        4. Output raw python text only. Never wrap code blocks in markdown fences like ```python.
        """
        
        user_prompt = f"""
        TARGET ANALYTICAL TASK: {user_task}
        
        VERIFIED DATA SCHEMA PROFILE:
        {schema_profile}
        
        Write the processing pipeline execution script now.
        """
        return self.llm.generate_code(system_prompt, user_prompt)
