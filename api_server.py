"""
FastAPI REST endpoint for NYC Taxi Analytics Pipeline
Runs on port 8100 for on-demand pipeline execution
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
from typing import Optional

# Import local modules
import orchestrator
from usage_tracker import UsageTracker

usage_tracker = UsageTracker()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify configuration on startup"""
    print("=" * 70)
    print("🚀 NYC Taxi Analytics Pipeline - FastAPI Server")
    print("=" * 70)
    print(f"Version: 2.0.0")
    print(f"Port: 8100")
    print(f"API Keys Configured: {'ANTHROPIC_API_KEY' in os.environ}")
    print(f"OpenAI Configured: {'OPENAI_API_KEY' in os.environ}")
    print(f"Daily Spending Limit: ${usage_tracker.DAILY_LIMIT}")
    print(f"Hourly Spending Limit: ${usage_tracker.HOURLY_LIMIT}")
    print("=" * 70)
    print("✅ Server ready at http://0.0.0.0:8100")
    print("📊 Dashboard: http://localhost:8100/api/dashboard")
    print("💰 Costs: http://localhost:8100/api/costs")
    print("=" * 70)
    yield

app = FastAPI(
    title="NYC Taxi Analytics Pipeline",
    version="2.0.0",
    description="On-demand microservice for autonomous schema analysis and code generation",
    lifespan=lifespan
)

# Enable CORS for Jenkins/dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# FRONTEND & HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def serve_frontend():
    """Serve the web UI at the root endpoint"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="Frontend UI not found (index.html missing)")

@app.get("/api/verify_url")
async def verify_url(vehicle_type: str, month: int):
    """Verify if a specific parquet file exists on the CDN"""
    if vehicle_type not in ["green", "yellow", "fhv", "fhvhv", "hvfhv"]:
        raise HTTPException(status_code=400, detail="Invalid vehicle_type")
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="Invalid month")
        
    try:
        # Import requests here to avoid changing top-level imports
        import requests
        from schema_specialist import SchemaSpecialist
        
        # We just need the URL logic, so any provider works (e.g. anthropic)
        specialist = SchemaSpecialist("anthropic")
        
        # Fix hvfhv naming if needed
        vt = "hvfhv" if vehicle_type == "fhvhv" else vehicle_type
        
        target_url = specialist.build_url(vt, month)
        head_check = requests.head(target_url, timeout=5)
        
        is_active = head_check.status_code == 200
        return {
            "active": is_active,
            "url": target_url,
            "status_code": head_check.status_code
        }
    except Exception as e:
        return {"active": False, "error": str(e)}

# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/Kubernetes"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "port": 8100
    }


@app.get("/api/status")
async def status():
    """Detailed service status"""
    ok, msg = usage_tracker.check_spending_limit()
    return {
        "service": "taxi-analytics-api",
        "version": "2.0.0",
        "running": True,
        "spending_limit_ok": ok,
        "limit_message": msg,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/deployment-status")
async def get_deployment_status():
    """Proxy to check Jenkins build status securely"""
    jenkins_token = os.environ.get("JENKINS_API_TOKEN")
    if not jenkins_token:
        # If no token, assume not building to avoid UI breaking
        return {"building": False, "error": "No JENKINS_API_TOKEN configured"}
        
    try:
        import httpx
        # We query the Ubuntu host where Jenkins is running (192.168.6.51)
        url = "http://192.168.6.51:8090/job/taxi-analytics-api-pipeline/lastBuild/api/json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                auth=("admin", jenkins_token),
                timeout=2.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Jenkins API returns a 'building' boolean
                return {"building": data.get("building", False)}
            else:
                return {"building": False, "error": f"Jenkins returned {response.status_code}"}
                
    except Exception as e:
        # If Jenkins is unreachable or errors out, assume not building
        return {"building": False, "error": str(e)}


# ============================================================================
# COST TRACKING ENDPOINTS
# ============================================================================

@app.get("/api/costs")
async def get_costs():
    """Get current spending stats and budget status"""
    usage = usage_tracker.load_historical_usage()
    ok, msg = usage_tracker.check_spending_limit()

    return {
        "spending_summary": {
            "total_input_tokens": usage.get("total_input_tokens", 0),
            "total_output_tokens": usage.get("total_output_tokens", 0),
            "total_cost": round(usage.get("total_cost", 0), 4),
            "total_sessions": len(usage.get("sessions", []))
        },
        "budget_status": {
            "within_limit": ok,
            "message": msg,
            "daily_limit": usage_tracker.DAILY_LIMIT,
            "hourly_limit": usage_tracker.HOURLY_LIMIT
        }
    }


# ============================================================================
# MAIN PIPELINE ENDPOINT
# ============================================================================

@app.post("/api/analyze")
def analyze_data(
    vehicle_type: str,
    month: int,
    task: str,
    provider: str = "anthropic"
):
    """
    Execute analytics pipeline on-demand

    Args:
        vehicle_type: One of [green, yellow, fhv, fhvhv]
        month: Month number (1-12)
        task: User-defined analytics task
        provider: LLM provider (anthropic, openai, ollama)

    Returns:
        Dictionary with execution results or error message

    Example:
        POST /api/analyze
        {
            "vehicle_type": "green",
            "month": 3,
            "task": "Calculate average trip distance and revenue",
            "provider": "anthropic"
        }
    """

    # Validate spending limit BEFORE running
    ok, msg = usage_tracker.check_spending_limit()
    if not ok:
        raise HTTPException(
            status_code=429,
            detail=f"Spending limit exceeded: {msg}. Check /api/costs for details"
        )

    # Validate inputs
    if vehicle_type not in ["green", "yellow", "fhv", "fhvhv"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid vehicle_type: {vehicle_type}. Must be one of: green, yellow, fhv, fhvhv"
        )

    if not 1 <= month <= 12:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid month: {month}. Must be between 1 and 12"
        )

    if not provider in ["anthropic", "openai", "ollama"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {provider}. Must be one of: anthropic, openai, ollama"
        )

    try:
        # Run the pipeline
        result = orchestrator.run_multi_agent_pipeline(
            provider_name=provider,
            vehicle_type=vehicle_type,
            month=month,
            user_task=task
        )

        execution_id = usage_tracker._generate_execution_id()

        return {
            "status": "success",
            "execution_id": execution_id,
            "vehicle_type": vehicle_type,
            "month": month,
            "task": task,
            "provider": provider,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except RuntimeError as e:
        # Spending limit or authentication error
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        # Other errors
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/api/mcp-test")
def mcp_test(prompt: str):
    """Bypass the orchestrator completely and let Claude act as a general agent with tools."""
    from providers import LLMFactory
    
    llm = LLMFactory.get_provider("anthropic")
    system_prompt = "You are a helpful AI assistant equipped with real-time MCP tools. Answer the user's request. Always output the final result strictly as a beautiful HTML dashboard utilizing the tool data you fetched. Never wrap the final output in ```html codeblocks, just return the raw html string."
    
    try:
        result, stats = llm.generate_code(system_prompt, prompt)
        return {"status": "success", "result": result, "usage": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/cache")
async def list_cache():
    """List all Python scripts in the code cache"""
    cache_dir = "code_cache"
    if not os.path.exists(cache_dir):
        return {"files": []}
    
    files_info = []
    for filename in os.listdir(cache_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(cache_dir, filename)
            stat = os.stat(filepath)
            files_info.append({
                "filename": filename,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return {"files": sorted(files_info, key=lambda x: x["modified_at"], reverse=True)}

@app.post("/api/cache/{filename}/rename")
def rename_cache_file(filename: str, new_name: str):
    """Rename a cached python script"""
    import re
    if not filename.endswith(".py") or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid old filename")
    
    if not new_name.endswith(".py"):
        new_name += ".py"
        
    # Sanitize new name (allow alphanumeric, underscores, hyphens)
    if not re.match(r'^[\w\-]+\.py$', new_name):
        raise HTTPException(status_code=400, detail="Invalid new filename")

    old_path = os.path.join("code_cache", filename)
    new_path = os.path.join("code_cache", new_name)
    
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail="Original file not found")
        
    try:
        os.rename(old_path, new_path)
        return {"status": "success", "new_name": new_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rename failed: {str(e)}")

@app.post("/api/analyze/cached")
def run_cached_script(filename: str, vehicle_type: str, month: int):
    """Run an existing script on a new target month/vehicle_type"""
    import re
    if not filename.endswith(".py") or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join("code_cache", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    from schema_specialist import SchemaSpecialist
    from sandbox import Sandbox
    
    specialist = SchemaSpecialist("anthropic") # Provider doesn't matter for URL building
    vt = "hvfhv" if vehicle_type == "fhvhv" else vehicle_type
    target_url = specialist.build_url(vt, month)

    # Regex string replacement inside the Python script to swap the parquet URL
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Swap out any existing TripData parquet URL with the newly requested one
        pattern = r"https://d37ci6vzurychx\.cloudfront\.net/trip-data/[a-z]+_tripdata_2026-\d{2}\.parquet"
        content = re.sub(pattern, target_url, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Execute the modified script
        sandbox = Sandbox()
        result = sandbox.execute_script(filepath)
        
        # Log it as a cached execution
        execution_id = usage_tracker._generate_execution_id()
        log_entry = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "vehicle_type": vehicle_type,
            "month": month,
            "task": f"Cached Run: {filename}",
            "provider": "cache",
            "api_called": False,
            "total_cost": 0,
            "result_summary": result[:100] + "..." if len(result) > 100 else result
        }
        usage_tracker._save_execution_log(log_entry)
        
        return {
            "status": "success",
            "execution_id": execution_id,
            "vehicle_type": vehicle_type,
            "month": month,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/cache/{filename}")
async def delete_cache_file(filename: str):
    """Safely delete a specific cached python script"""
    if not filename.endswith(".py") or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = os.path.join("code_cache", filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return {"status": "success", "message": f"Deleted {filename}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete {filename}: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/api/cache")
async def clear_all_cache():
    """Clear all cached python scripts"""
    cache_dir = "code_cache"
    if not os.path.exists(cache_dir):
        return {"status": "success", "deleted_count": 0}
        
    deleted_count = 0
    errors = []
    for filename in os.listdir(cache_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(cache_dir, filename)
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                errors.append(str(e))
                
    if errors:
        return {"status": "partial_success", "deleted_count": deleted_count, "errors": errors}
    return {"status": "success", "deleted_count": deleted_count}


# ============================================================================
# HISTORY & MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/history")
async def get_history(limit: int = 20):
    """Get recent execution history"""
    try:
        with open("execution_log.json", "r") as f:
            log = json.load(f)
        
        # Return most recent first
        return {
            "total_executions": len(log),
            "recent_limit": limit,
            "executions": log[-limit:][::-1]  # Reverse to show newest first
        }
    except FileNotFoundError:
        return {
            "total_executions": 0,
            "recent_limit": limit,
            "executions": []
        }


@app.get("/api/dashboard")
async def get_dashboard():
    """
    Get all metrics for dashboard rendering

    Returns comprehensive stats including:
    - Spending summary (tokens, cost, sessions)
    - Caching efficiency (cached vs API calls)
    - Recent executions
    - Current budget limits
    """
    usage = usage_tracker.load_historical_usage()

    try:
        with open("execution_log.json", "r") as f:
            executions = json.load(f)
    except FileNotFoundError:
        executions = []

    # Calculate metrics
    total_runs = len(executions)
    cached_count = sum(1 for e in executions if not e.get("api_called"))
    api_count = sum(1 for e in executions if e.get("api_called"))
    total_cost = sum(e.get("total_cost", 0) for e in executions)

    cache_hit_rate = (cached_count / total_runs * 100) if total_runs > 0 else 0
    cost_saved = (cached_count / total_runs * usage.get("total_cost", 0)) if total_runs > 0 else 0

    ok, limit_msg = usage_tracker.check_spending_limit()

    return {
        "spending_summary": {
            "total_input_tokens": usage.get("total_input_tokens", 0),
            "total_output_tokens": usage.get("total_output_tokens", 0),
            "total_cost": round(usage.get("total_cost", 0), 4),
            "total_sessions": len(usage.get("sessions", []))
        },
        "efficiency_metrics": {
            "total_runs": total_runs,
            "cached_runs": cached_count,
            "api_calls": api_count,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "estimated_cost_saved": round(cost_saved, 4)
        },
        "budget_status": {
            "within_limit": ok,
            "message": limit_msg,
            "daily_limit": usage_tracker.DAILY_LIMIT,
            "hourly_limit": usage_tracker.HOURLY_LIMIT
        },
        "recent_executions": executions[-10:],
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8100,
        log_level="info"
    )
