import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

class UsageTracker:
    """Tracks API usage, tokens, costs, and enforces spending limits"""
    
    USAGE_FILE = "api_usage.json"
    EXECUTION_LOG = "execution_log.json"
    
    # Claude Haiku pricing (per million tokens)
    CLAUDE_HAIKU_INPUT_COST = 0.80 / 1_000_000
    CLAUDE_HAIKU_OUTPUT_COST = 4.00 / 1_000_000
    
    # Spending limits (set to None to disable)
    DAILY_LIMIT = 10.00  # $ per day
    HOURLY_LIMIT = 1.00   # $ per hour
    
    def __init__(self):
        self.current_session_usage = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "api_calls": [],
            "api_called": False,
            "execution_id": self._generate_execution_id()
        }
        self.load_historical_usage()
    
    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def load_historical_usage(self) -> dict:
        """Load historical usage data"""
        if os.path.exists(self.USAGE_FILE):
            with open(self.USAGE_FILE, 'r') as f:
                self.historical_usage = json.load(f)
            
            # Ensure keys exist if file was initialized empty
            for key, default in [("total_input_tokens", 0), ("total_output_tokens", 0), 
                                 ("total_cost", 0.0), ("sessions", [])]:
                if key not in self.historical_usage:
                    self.historical_usage[key] = default
        else:
            self.historical_usage = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "sessions": []
            }
        return self.historical_usage
    
    def check_spending_limit(self) -> tuple[bool, str]:
        """
        Check if we're within spending limits.
        Returns: (is_ok: bool, message: str)
        """
        now = datetime.now()
        today = now.date()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        daily_cost = 0.0
        hourly_cost = 0.0
        
        # Load execution log
        if os.path.exists(self.EXECUTION_LOG):
            with open(self.EXECUTION_LOG, 'r') as f:
                executions = json.load(f)
        else:
            executions = []
        
        # Calculate daily and hourly costs
        for exec_record in executions:
            exec_time = datetime.fromisoformat(exec_record["timestamp"])
            exec_date = exec_time.date()
            
            if exec_date == today:
                daily_cost += exec_record.get("cost", 0)
                
                # Check hourly
                if exec_time.replace(minute=0, second=0, microsecond=0) == current_hour:
                    hourly_cost += exec_record.get("cost", 0)
        
        # Check limits
        if self.DAILY_LIMIT and daily_cost >= self.DAILY_LIMIT:
            return False, f"❌ DAILY LIMIT EXCEEDED: ${daily_cost:.4f} >= ${self.DAILY_LIMIT:.2f}"
        
        if self.HOURLY_LIMIT and hourly_cost >= self.HOURLY_LIMIT:
            return False, f"❌ HOURLY LIMIT EXCEEDED: ${hourly_cost:.4f} >= ${self.HOURLY_LIMIT:.2f}"
        
        return True, "✅ Within spending limits"
    
    def track_api_call(self, input_tokens: int, output_tokens: int, model: str, attempt: int = 1) -> dict:
        """Track a single API call"""
        input_cost = input_tokens * self.CLAUDE_HAIKU_INPUT_COST
        output_cost = output_tokens * self.CLAUDE_HAIKU_OUTPUT_COST
        total_cost = input_cost + output_cost
        
        call_data = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "attempt": attempt,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": total_cost
        }
        
        # Update current session
        self.current_session_usage["total_input_tokens"] += input_tokens
        self.current_session_usage["total_output_tokens"] += output_tokens
        self.current_session_usage["total_cost"] += total_cost
        self.current_session_usage["api_calls"].append(call_data)
        self.current_session_usage["api_called"] = True
        
        # Update historical
        self.historical_usage["total_input_tokens"] += input_tokens
        self.historical_usage["total_output_tokens"] += output_tokens
        self.historical_usage["total_cost"] += total_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost
        }
    
    def save_session(self, vehicle_type: str, month: int, task: str, success: bool, code_hash: str = "", code_path: str = ""):
        """Save current session to historical data"""
        session_data = {
            "execution_id": self.current_session_usage["execution_id"],
            "timestamp": datetime.now().isoformat(),
            "vehicle_type": vehicle_type,
            "month": month,
            "task": task,
            "success": success,
            "api_called": self.current_session_usage["api_called"],
            "input_tokens": self.current_session_usage["total_input_tokens"],
            "output_tokens": self.current_session_usage["total_output_tokens"],
            "total_cost": self.current_session_usage["total_cost"],
            "api_calls_count": len(self.current_session_usage["api_calls"]),
            "code_hash": code_hash,
            "code_path": code_path
        }
        
        self.historical_usage["sessions"].append(session_data)
        self._persist_usage()
        
        # Also log to execution log
        self._log_execution(session_data)
    
    def _log_execution(self, session_data: dict):
        """Log execution to execution log"""
        if os.path.exists(self.EXECUTION_LOG):
            with open(self.EXECUTION_LOG, 'r') as f:
                executions = json.load(f)
        else:
            executions = []
        
        executions.append(session_data)
        
        with open(self.EXECUTION_LOG, 'w') as f:
            json.dump(executions, f, indent=2)
    
    def _persist_usage(self):
        """Save usage data to file"""
        with open(self.USAGE_FILE, 'w') as f:
            json.dump(self.historical_usage, f, indent=2)
