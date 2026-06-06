import io
import sys
import os
import traceback
from providers import LLMFactory
from sandbox import SafeSandbox
from schema_specialist import SchemaSpecialist
from code_generator import CodeGenerator

def run_multi_agent_pipeline(provider_name: str, vehicle_type: str, month: int, user_task: str):
    """Orchestrates the metadata verification, code generation, and self-healing loop."""
    eye_agent = SchemaSpecialist(provider_name)
    brain_agent = CodeGenerator(provider_name)
    
    # Step 1: Data Profiling (The Eyes)
    verified_url, schema_brief = eye_agent.profile_data(vehicle_type, month)
    
    if "CIRCUIT_BREAKER_TRIGGERED" in schema_brief:
        print(f"\n❌ [Orchestrator Error]: Pipeline aborted for {vehicle_type.upper()} Month {month}.")
        print(f"Details: {schema_brief}")
        return None
        
    print(f"\n✅ [Orchestrator]: Pipeline safely locked onto active data layer endpoint.")
    print(f"📋 [Orchestrator] Schema Brief Received:\n{schema_brief}\n" + "-"*50)
    
    current_task_prompt = user_task
    
    # Step 2: Self-Correction Compiler Loop
    for attempt in range(1, 4):
        print(f"🔄 [Orchestrator]: Requesting script from Generator (Attempt {attempt})...")
        raw_code = brain_agent.generate_analytics_code(verified_url, current_task_prompt, schema_brief)
        
        # Clean formatting tokens safely
        lines = raw_code.strip().split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]  # Correct Python slice syntax to strip trailing backticks
        raw_code = "\n".join(lines)
            
        print("⚡ [Orchestrator]: Running code inside Safe Sandbox...")
        result = SafeSandbox.execute(raw_code)
        
        if result["success"]:
            print(f"🎉 [Orchestrator]: Job verification successful for domain {vehicle_type.upper()}.")
            return result["output"]
            
        print(f"❌ [Orchestrator]: Sandbox exception triggered:\n{result['error']}")
        print("⚠️ [Orchestrator]: Retrying execution path with structural feedback parameters...")
        
        current_task_prompt = f"""Your generated python code failed inside the sandbox environment:
        {result['error']}
        
        Please rewrite the full script cleanly, correct errors, and assign your answer to 'FINAL_OUTPUT'."""

    raise RuntimeError(f"Multi-Agent pipeline failed to converge for domain {vehicle_type.upper()}.")

if __name__ == "__main__":
    # DEVELOPMENT ENGINE PARAMETERS
    # Constraining the engine scope strictly to Green Taxis to optimize processing weight
    MODEL_PROVIDER = "anthropic" 
    VEHICLE_TYPE = "green"  # Rigidly locked onto the Green Taxi sub-domain
    MONTH = 1              # Targeting the January data partition
    
    print("\n" + "="*20 + " GREEN TAXI PIPELINE DEVELOPMENT MODE " + "="*20)
    
    # An analytics task tailored to Green Taxi operations (Street hails outside Manhattan core zones)
    green_taxi_goal = (
        "Calculate the total trip count, the average trip distance, "
        "and find the average fare amount grouped by payment_type."
    )
    
    try:
        # Launch our multi-agent self-healing loop
        development_report = run_multi_agent_pipeline(
            provider_name=MODEL_PROVIDER, 
            vehicle_type=VEHICLE_TYPE, 
            month=MONTH, 
            user_task=green_taxi_goal
        )
        
        if development_report:
            print(f"\n🚀 SHIPPED REPORT (GREEN TAXI DOMAIN):\n{development_report}")
            
    except Exception as pipeline_error:
        print(f"\n❌ Pipeline failed during development processing loop: {pipeline_error}")

