import os
import sys
import json
import subprocess

def test_component(component_name):
    print(f"\n[CI/CD Engine] 🔍 Validating Component: {component_name}...")

def run_pipeline_tests():
    all_passed = True

    # 1. TEST THE HOOK (Pre-Commit Automation Pass)
    test_component("Claude Code Hook Architecture")
    hook_path = os.path.join(".claude", "hooks", "pre-commit.py")
    if not os.path.exists(hook_path):
        print(f"❌ Failure: Hook script missing at path: {hook_path}")
        all_passed = False
    else:
        try:
            # Execute hook script independently to see if it passes code files syntax checking
            result = subprocess.run([sys.executable, hook_path], capture_output=True, text=True, check=True)
            print("  ✅ Pass: Hook executed successfully.")
            print(f"  [Output Log]: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failure: Hook block triggered an error response code:\n{e.stderr}")
            all_passed = False

    # 2. TEST THE SKILL (Markdown Meta Layout Verification)
    test_component("Claude Code Custom Skill Schema")
    skill_md_path = os.path.join(".claude", "skills", "run-pipeline", "SKILL.md")
    if not os.path.exists(skill_md_path):
        print(f"❌ Failure: SKILL.md missing at expected location: {skill_md_path}")
        all_passed = False
    else:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Enforce formal Anthropic frontmatter registration patterns are verified
            if not content.startswith("---") or "name: run-pipeline" not in content:
                print("  ❌ Failure: SKILL.md missing valid YAML frontmatter registration markers.")
                all_passed = False
            else:
                print("  ✅ Pass: SKILL.md metadata layout format verified.")

    # 3. TEST THE MCP SERVER (JSON Stream Protocol Simulation)
    test_component("Model Context Protocol (MCP) Stream Interface")
    mcp_script = "mcp_server.py"
    if not os.path.exists(mcp_script):
        print(f"❌ Failure: MCP Server file missing: {mcp_script}")
        all_passed = False
    else:
        try:
            # Test direct argument passing pipeline to check JSON parsing outputs
            result = subprocess.run([sys.executable, mcp_script, "green"], capture_output=True, text=True, check=True)
            parsed_json = json.loads(result.stdout.strip())
            
            if "columns" in parsed_json and "table_layer" in parsed_json:
                print("  ✅ Pass: MCP Server input/output channel responded with schema data.")
                print(f"  [Payload Sample]: {list(parsed_json.keys())}")
            else:
                print("  ❌ Failure: MCP output missing standard protocol properties.")
                all_passed = False
        except (subprocess.CalledProcessError, json.JSONDecodeError) as err:
            print(f"  ❌ Failure: MCP communication stream broken. Error: {err}")
            all_passed = False

    # FINAL STAGE VERIFICATION REPORT
    print("\n" + "="*50)
    if all_passed:
        print("🏆 [DEPLOYMENT STATUS]: READY. All parameters verified functional.")
        sys.exit(0)
    else:
        print("🛑 [DEPLOYMENT STATUS]: REJECTED. Fix component breaks before pushing.")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline_tests()
