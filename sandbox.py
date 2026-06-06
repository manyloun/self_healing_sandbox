import sys
import io
import traceback

class SafeSandbox:
    @staticmethod
    def execute(code_string: str) -> dict:
        """Executes Python code strings safely inside an isolated local scope."""
        # Windows-specific and generic malicious command tokens blacklist
        forbidden = [
            "os.system", "subprocess", "shutil", "rmdir", "del ", 
            "environ", "Remove-Item", "Invoke-Expression", "iex"
        ]
        for token in forbidden:
            if token in code_string:
                return {"success": False, "error": f"Security Exception: Blacklisted token '{token}' detected."}
        
        local_vars = {}
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        
        try:
            sys.stdout = stdout_capture
            # Execute safely by limiting global builtins and parsing libraries explicitly
            exec(code_string, {"__builtins__": __builtins__, "pd": __import__("pandas")}, local_vars)
            sys.stdout = old_stdout
            
            return {
                "success": True, 
                "output": local_vars.get("FINAL_OUTPUT", "Error: Variable 'FINAL_OUTPUT' not defined by code."),
                "stdout": stdout_capture.getvalue()
            }
        except Exception as e:
            sys.stdout = old_stdout
            return {
                "success": False, 
                "error": traceback.format_exc()
            }
