#!/usr/bin/env python3
"""
Monitoring utility to view API usage, execution history, and spending limits.
Run: python monitor.py
"""

import os
import json
from datetime import datetime, timedelta
from usage_tracker import UsageTracker

class Monitor:
    def __init__(self):
        self.tracker = UsageTracker()
        self.usage_file = UsageTracker.USAGE_FILE
        self.exec_log_file = UsageTracker.EXECUTION_LOG
    
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    
    def show_spending_summary(self):
        """Show overall spending summary"""
        self.print_header("💰 SPENDING SUMMARY")
        
        if os.path.exists(self.usage_file):
            with open(self.usage_file, 'r') as f:
                data = json.load(f)
        else:
            print("No usage data found yet.")
            return
        
        total_input = data.get("total_input_tokens", 0)
        total_output = data.get("total_output_tokens", 0)
        total_cost = data.get("total_cost", 0)
        total_sessions = len(data.get("sessions", []))
        
        print(f"Total Input Tokens:    {total_input:,}")
        print(f"Total Output Tokens:   {total_output:,}")
        print(f"Total Tokens:          {total_input + total_output:,}")
        print(f"Total Cost:            ${total_cost:.4f}")
        print(f"Total Sessions:        {total_sessions}")
        
        if total_sessions > 0:
            avg_cost = total_cost / total_sessions
            print(f"Average Cost/Session:  ${avg_cost:.4f}")
    
    def show_execution_history(self, limit: int = 20):
        """Show recent execution history"""
        self.print_header(f"📋 EXECUTION HISTORY (Last {limit})")
        
        if not os.path.exists(self.exec_log_file):
            print("No execution history found yet.")
            return
        
        with open(self.exec_log_file, 'r') as f:
            executions = json.load(f)
        
        if not executions:
            print("No executions recorded.")
            return
        
        # Sort by timestamp descending
        executions = sorted(executions, key=lambda x: x["timestamp"], reverse=True)[:limit]
        
        print(f"{'ID':<8} {'Time':<8} {'Vehicle':<10} {'API Called':<12} {'Cost':<10} {'Status':<6}")
        print("-" * 80)
        
        for exec_record in executions:
            exec_id = exec_record.get("execution_id", "")[:8]
            timestamp = exec_record.get("timestamp", "")[-8:]  # HH:MM:SS
            vehicle = f"{exec_record.get('vehicle_type', '').upper()}-{exec_record.get('month', ''):02d}"
            api_called = "💰 USED" if exec_record.get("api_called") else "😊 CACHED"
            cost = f"${exec_record.get('total_cost', 0):.4f}"
            success = "✅" if exec_record.get("success") else "❌"
            
            print(f"{exec_id:<8} {timestamp:<8} {vehicle:<10} {api_called:<12} {cost:<10} {success:<6}")
    
    def show_daily_summary(self):
        """Show today's spending"""
        self.print_header("📅 TODAY'S SPENDING")
        
        if not os.path.exists(self.exec_log_file):
            print("No executions recorded yet.")
            return
        
        with open(self.exec_log_file, 'r') as f:
            executions = json.load(f)
        
        today = datetime.now().date()
        today_cost = 0.0
        today_count = 0
        
        for exec_record in executions:
            exec_date = datetime.fromisoformat(exec_record["timestamp"]).date()
            if exec_date == today:
                today_cost += exec_record.get("total_cost", 0)
                today_count += 1
        
        hourly_limit = UsageTracker.HOURLY_LIMIT
        daily_limit = UsageTracker.DAILY_LIMIT
        
        print(f"Executions Today:      {today_count}")
        print(f"Cost Today:            ${today_cost:.4f}")
        print(f"Daily Limit:           ${daily_limit:.2f}")
        print(f"Remaining Today:       ${max(0, daily_limit - today_cost):.4f}")
        
        if hourly_limit:
            print(f"Hourly Limit:          ${hourly_limit:.2f}")
        
        if daily_limit and today_cost >= daily_limit:
            print(f"\n⚠️  DAILY LIMIT REACHED - API calls blocked until reset")
    
    def show_limits(self):
        """Show current spending limits"""
        self.print_header("🛑 SPENDING LIMITS")
        
        daily = UsageTracker.DAILY_LIMIT
        hourly = UsageTracker.HOURLY_LIMIT
        
        print(f"Daily Limit:           ${daily:.2f}" if daily else "Daily Limit:           Disabled")
        print(f"Hourly Limit:          ${hourly:.2f}" if hourly else "Hourly Limit:          Disabled")
        print(f"\nTo change limits, edit usage_tracker.py:")
        print(f"  - DAILY_LIMIT = 10.00")
        print(f"  - HOURLY_LIMIT = 1.00")
    
    def show_api_calls(self, vehicle_type: str = None, limit: int = 50):
        """Show API calls"""
        self.print_header(f"🔌 API CALLS DETAIL (Last {limit})")
        
        if not os.path.exists(self.exec_log_file):
            print("No API calls recorded yet.")
            return
        
        with open(self.exec_log_file, 'r') as f:
            executions = json.load(f)
        
        # Filter if vehicle type specified
        if vehicle_type:
            executions = [e for e in executions if e.get("vehicle_type") == vehicle_type.lower()]
        
        # Sort by timestamp descending
        executions = sorted(executions, key=lambda x: x["timestamp"], reverse=True)[:limit]
        
        api_calls = [e for e in executions if e.get("api_called")]
        
        if not api_calls:
            print("No API calls recorded.")
            return
        
        print(f"{'Timestamp':<20} {'Vehicle':<10} {'Input':<8} {'Output':<8} {'Total':<10} {'Cost':<10}")
        print("-" * 80)
        
        for exec_record in api_calls:
            timestamp = exec_record.get("timestamp", "")[-19:-4]  # YYYY-MM-DD HH:MM
            vehicle = f"{exec_record.get('vehicle_type', '').upper()}-{exec_record.get('month', ''):02d}"
            input_tokens = exec_record.get("input_tokens", 0)
            output_tokens = exec_record.get("output_tokens", 0)
            total = input_tokens + output_tokens
            cost = f"${exec_record.get('total_cost', 0):.4f}"
            
            print(f"{timestamp:<20} {vehicle:<10} {input_tokens:<8} {output_tokens:<8} {total:<10} {cost:<10}")
    
    def show_cached_vs_api(self):
        """Show ratio of cached vs API calls"""
        self.print_header("⚡ CACHED VS API CALLS")
        
        if not os.path.exists(self.exec_log_file):
            print("No execution data yet.")
            return
        
        with open(self.exec_log_file, 'r') as f:
            executions = json.load(f)
        
        cached = sum(1 for e in executions if not e.get("api_called"))
        api_called = sum(1 for e in executions if e.get("api_called"))
        total = len(executions)
        
        if total == 0:
            print("No executions yet.")
            return
        
        cached_pct = (cached / total) * 100
        api_pct = (api_called / total) * 100
        
        total_cost = sum(e.get("total_cost", 0) for e in executions)
        api_cost = sum(e.get("total_cost", 0) for e in executions if e.get("api_called"))
        
        print(f"Total Executions:      {total}")
        print(f"Cached Executions:     {cached} ({cached_pct:.1f}%)")
        print(f"API Calls:             {api_called} ({api_pct:.1f}%)")
        print(f"\nTotal Cost:            ${total_cost:.4f}")
        print(f"API Cost:              ${api_cost:.4f}")
        print(f"Savings from Cache:    ${total_cost - api_cost:.4f}")
        
        if api_cost > 0:
            print(f"Cost Reduction:        {((total_cost - api_cost) / api_cost) * 100:.1f}%")

def main():
    monitor = Monitor()
    
    print("\n" + "="*80)
    print("  🔍 ORCHESTRATOR MONITORING DASHBOARD")
    print("="*80)
    
    # Show all summaries
    monitor.show_spending_summary()
    monitor.show_daily_summary()
    monitor.show_limits()
    monitor.show_cached_vs_api()
    monitor.show_execution_history(limit=15)
    monitor.show_api_calls(limit=10)
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
