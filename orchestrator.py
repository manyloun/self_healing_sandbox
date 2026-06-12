import io
import sys
import os
import json
from providers import LLMFactory
from sandbox import SafeSandbox
from schema_specialist import SchemaSpecialist
from code_generator import CodeGenerator
from usage_tracker import UsageTracker

CODE_CACHE_DIR = "code_cache"
usage_tracker = UsageTracker()

def _ensure_code_cache_dir():
    """Create code cache directory if it doesn't exist"""
    if not os.path.exists(CODE_CACHE_DIR):
        os.makedirs(CODE_CACHE_DIR)

def _get_cached_code(vehicle_type: str, schema_hash: str, user_task: str) -> str:
    """Try to retrieve cached code for this vehicle type, schema hash, and user task"""
    _ensure_code_cache_dir()
    import hashlib
    task_hash = hashlib.md5(user_task.encode()).hexdigest()[:8]
    cache_file = os.path.join(CODE_CACHE_DIR, f"{vehicle_type}_{schema_hash}_{task_hash}.py")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return f.read()
    return None

def _save_cached_code(vehicle_type: str, schema_hash: str, user_task: str, code: str):
    """Save successfully executed code to cache"""
    _ensure_code_cache_dir()
    import hashlib
    task_hash = hashlib.md5(user_task.encode()).hexdigest()[:8]
    cache_file = os.path.join(CODE_CACHE_DIR, f"{vehicle_type}_{schema_hash}_{task_hash}.py")
    
    with open(cache_file, 'w') as f:
        f.write(code)
    
    print(f"💾 [Orchestrator]: Cached code for {vehicle_type} (hash: {schema_hash}, task_hash: {task_hash})")

def run_multi_agent_pipeline(provider_name: str, vehicle_type: str, month: int, user_task: str):
    eye_agent = SchemaSpecialist(provider_name)
    brain_agent = CodeGenerator(provider_name)
    
    try:
        verified_url, schema_hash, schema_filepath, schema_dict = eye_agent.profile_data(vehicle_type, month)
    except Exception as e:
        print(f"\n❌ [Orchestrator Error]: Pipeline aborted. Details: {str(e)}")
        usage_tracker.save_session(vehicle_type, month, user_task, False, "", "")
        return None
    
    print(f"📦 [Orchestrator] Schema file: {schema_filepath}")
    print(f"🔐 [Orchestrator] Schema hash: {schema_hash}")
    
    # Check for cached code
    cached_code = _get_cached_code(vehicle_type, schema_hash, user_task)
    if cached_code:
        print(f"\n{'='*70}")
        print(f"✅ [Orchestrator]: USING CACHED CODE (No Claude API call needed)")
        print(f"   Schema hash: {schema_hash}")
        print(f"{'='*70}")
        print(f"⚡ [Orchestrator]: Running cached code inside Safe Sandbox...")
        result = SafeSandbox.execute(cached_code)
        
        if result["success"]:
            print(f"🎉 [Orchestrator]: Cached code executed successfully for domain {vehicle_type.upper()}.")
            import hashlib
            task_hash = hashlib.md5(user_task.encode()).hexdigest()[:8]
            code_path = os.path.join(CODE_CACHE_DIR, f"{vehicle_type}_{schema_hash}_{task_hash}.py")
            usage_tracker.save_session(vehicle_type, month, user_task, True, schema_hash, code_path)
            return {
                "answer": result["output"],
                "code": cached_code
            }
        else:
            print(f"⚠️  [Orchestrator]: Cached code failed. Regenerating with Claude...\n{result['error']}")
    
    # Check spending limits BEFORE calling Claude
    is_ok, limit_msg = usage_tracker.check_spending_limit()
    if not is_ok:
        print(f"\n{'='*70}")
        print(f"{limit_msg}")
        print(f"🛑 [Orchestrator]: KILL SWITCH TRIGGERED - API calls blocked")
        print(f"   Please check your spending or update limits in usage_tracker.py")
        print(f"{'='*70}\n")
        usage_tracker.save_session(vehicle_type, month, user_task, False, schema_hash, "BLOCKED_BY_LIMIT")
        raise RuntimeError(f"Spending limit exceeded. {limit_msg}")
    
    # No cached code or cached code failed - generate new code
    print(f"\n{'='*70}")
    print(f"🧠 [Orchestrator]: CALLING CLAUDE FOR CODE GENERATION")
    print(f"   Schema hash: {schema_hash}")
    print(f"   (This will be cached for future use)")
    print(f"{'='*70}")
    print(f"🔄 [Orchestrator]: No valid cache found. Requesting fresh code from Claude...")
    current_task_prompt = user_task
    
    for attempt in range(1, 4):
        print(f"\n🔄 [Orchestrator]: Requesting script from Claude (Attempt {attempt}/3)...")
        raw_code, usage_stats = brain_agent.generate_analytics_code(verified_url, current_task_prompt, schema_dict)
        
        # Track the API call (silently)
        call_stats = usage_tracker.track_api_call(
            usage_stats["input_tokens"],
            usage_stats["output_tokens"],
            usage_stats["model"],
            attempt
        )
        
        lines = raw_code.strip().split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_code = "\n".join(lines)
            
        print("⚡ [Orchestrator]: Running code inside Safe Sandbox...")
        result = SafeSandbox.execute(raw_code)
        
        if result["success"]:
            # Code executed successfully - cache it
            _save_cached_code(vehicle_type, schema_hash, user_task, raw_code)
            print(f"🎉 [Orchestrator]: Job validation successful for domain {vehicle_type.upper()}.")
            import hashlib
            task_hash = hashlib.md5(user_task.encode()).hexdigest()[:8]
            code_path = os.path.join(CODE_CACHE_DIR, f"{vehicle_type}_{schema_hash}_{task_hash}.py")
            usage_tracker.save_session(vehicle_type, month, user_task, True, schema_hash, code_path)
            return {
                "answer": result["output"],
                "code": raw_code
            }
            
        print(f"❌ [Orchestrator]: Sandbox exception triggered:\n{result['error']}")
        current_task_prompt = f"Your code failed: {result['error']}\nPlease rewrite it and fix the bugs."

    usage_tracker.save_session(vehicle_type, month, user_task, False, schema_hash, "")
    raise RuntimeError("Multi-Agent pipeline failed to converge after 3 attempts.")

if __name__ == "__main__":
    print("\n==================== NYC TLC PIPELINE DEVELOPMENT MODE ==========================")
    print("\n=== Data Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page ===")
    tlc_goal = "Calculate the total trip count, average trip distance, and average fare amount grouped by payment_type."
    
    try:
        report = run_multi_agent_pipeline("anthropic", "yellow", 2, tlc_goal)
        if report: 
            print(f"\n🚀 SHIPPED REPORT:\n{report}")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
