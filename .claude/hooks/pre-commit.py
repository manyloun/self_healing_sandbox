import sys
import os

# Fix Windows 11 CMD/PowerShell encoding constraints for clean text routing
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def run_hygiene_check():
    print("[Claude Code Hook] Executing Pre-Commit Engineering Hygiene Check...")
    
    files_to_check = ["orchestrator.py", "sandbox.py", "schema_specialist.py", "code_generator.py"]
    
    for file in files_to_check:
        if not os.path.exists(file):
            print(f"[-] Skip: {file} is not present in workspace yet.")
            continue
            
        try:
            with open(file, "r", encoding="utf-8") as f:
                # compile() natively catches formatting issues like the slicing bug ([:-])
                compile(f.read(), file, "exec")
        except SyntaxError as se:
            print(f"[Hook Blocked] Syntax error detected in {file}: {se}")
            sys.exit(1)
            
    print("[Hook Passed] Code syntax is clean. Proceeding with execution workflow.")
    sys.exit(0)

if __name__ == "__main__":
    run_hygiene_check()
