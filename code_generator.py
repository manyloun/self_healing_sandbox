import json
from providers import LLMFactory

class CodeGenerator:
    def __init__(self, provider_name: str):
        self.llm = LLMFactory.get_provider(provider_name)

    def _format_schema_for_llm(self, schema_profile) -> str:
        """Format schema (dict or string) into readable text for LLM"""
        tlc_mappings = """
KNOWN TLC DATA MAPPINGS:
- VendorID (Provider): 
  1: CMT (Creative Mobile Technologies)
  2: VeriFone / Curb
  3: Uber Technologies
  4: Lyft
  5: Via / Via Transportation
  6: Juno (acquired by Gett; historical data only)
  7: Other / Miscellaneous Licensed Dispatch Provider
"""
        formatted = ""
        if isinstance(schema_profile, dict):
            # Convert schema dict to readable format
            formatted_fields = []
            if "fields" in schema_profile:
                for field in schema_profile["fields"]:
                    formatted_fields.append(f"  - {field['name']}: {field['type']}")
            formatted = "SCHEMA FIELDS:\n" + "\n".join(formatted_fields)
        else:
            # Already a string
            formatted = schema_profile
            
        return formatted + "\n" + tlc_mappings

    def generate_analytics_code(self, target_url: str, user_task: str, schema_profile) -> tuple:
        """
        Generate analytics code.
        Returns: (code: str, usage_stats: dict)
        """
        schema_formatted = self._format_schema_for_llm(schema_profile)
        
        system_prompt = f"""You are an elite Databricks Data Engineer. Write clean Python code using pandas to process data from: '{target_url}'
        1. Read file using: df = pd.read_parquet('{target_url}')
        2. Assign the requested final output (e.g. text or a full HTML document) to a local variable named 'FINAL_OUTPUT'.
        3. Output raw python text only. Never wrap code blocks in markdown fences like ```python."""
        
        user_prompt = f"TASK: {user_task}\n\n{schema_formatted}\n\nWrite the processing script now."
        code, usage_stats = self.llm.generate_code(system_prompt, user_prompt)
        return code, usage_stats
