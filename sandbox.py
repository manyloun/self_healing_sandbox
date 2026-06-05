import sys
import io
import traceback

class SafeSandbox:
    @staticmethod
    def execute(code_string: str) -> dict:
        forbidden = ["os.system", "subprocess", "shutil", "rmdir", "del ", "environ", "Remove-Item", "iex"]
        for token in forbidden:
            if token in code_string:
                return {"success": False, "error": f"Security Exception: Blacklisted token '{token}' detected."}
        
        local_vars = {}
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = stdout_capture
            exec(code_string, {"__builtins__": __builtins__, "pd": __import__("pandas")}, local_vars)
            sys.stdout = old_stdout
            return {"success": True, "output": local_vars.get("FINAL_OUTPUT", "Error: FINAL_OUTPUT missing."), "stdout": stdout_capture.getvalue()}
        except Exception as e:
            sys.stdout = old_stdout
            return {"success": False, "error": traceback.format_exc()}
