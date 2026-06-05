import io
import sys
import os
from providers import LLMFactory
from sandbox import SafeSandbox
from schema_specialist import SchemaSpecialist
from code_generator import CodeGenerator

def run_multi_agent_pipeline(provider_name: str, vehicle_type: str, month: int, user_task: str):
    eye_agent = SchemaSpecialist(provider_name)
    brain_agent = CodeGenerator(provider_name)
    
    verified_url, schema_brief = eye_agent.profile_data(vehicle_type, month)
    if "CIRCUIT_BREAKER_TRIGGERED" in schema_brief:
        print(f"\n❌ [Orchestrator Error]: Pipeline aborted. Details: {schema_brief}")
        return None
        
    print(f"\n📋 [Orchestrator] Schema Brief Received:\n{schema_brief}\n" + "-"*50)
    current_task_prompt = user_task
    
    for attempt in range(1, 4):
        print(f"🔄 [Orchestrator]: Requesting script from Generator (Attempt {attempt})...")
        raw_code = brain_agent.generate_analytics_code(verified_url, current_task_prompt, schema_brief)
        
        lines = raw_code.strip().split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1] # Fixed Python list slice tracking to strip closing markdown flags
        raw_code = "\n".join(lines)
            
        print("⚡ [Orchestrator]: Running code inside Safe Sandbox...")
        result = SafeSandbox.execute(raw_code)
        
        if result["success"]:
            print(f"🎉 [Orchestrator]: Job validation successful for domain {vehicle_type.upper()}.")
            return result["output"]
            
        print(f"❌ [Orchestrator]: Sandbox exception triggered:\n{result['error']}")
        current_task_prompt = f"Your code failed: {result['error']}\nPlease rewrite it and fix the bugs."

    raise RuntimeError("Multi-Agent pipeline failed to converge.")

if __name__ == "__main__":
    print("\n==================== GREEN TAXI PIPELINE DEVELOPMENT MODE ====================")
    green_taxi_goal = "Calculate the total trip count, average trip distance, and average fare amount grouped by payment_type."
    report = run_multi_agent_pipeline("anthropic", "green", 1, green_taxi_goal)
    if report: print(f"\n🚀 SHIPPED REPORT:\n{report}")
