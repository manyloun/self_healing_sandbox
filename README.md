# Autonomous Multi-Agent Medallion Data Pipeline Sandbox

This repository showcases a production-grade, self-healing data analytics engine designed to execute schema mapping, code generation, and automated validation routines over telemetry and transit datasets (NYC TLC Parquet streams). 

Engineered explicitly using **Claude Haiku 4.5** as a decoupled orchestration controller, the framework maps directly to enterprise data platform paradigms utilized across Databricks and Azure environments.

## 🆕 Latest Features (v2.2)

### 🖥️ Web UI Dashboard & Cache Management
- **Interactive Web Dashboard**: Built-in HTML UI with a clean, glassmorphism design for running analytics pipelines locally or remotely.
- **⭐ Favorites System**: Renaming an auto-generated script permanently saves it to a protected Favorites tab. 
- **Quick-Run Workflows**: You can reuse any Favorite script on a *new* data month or vehicle type directly from the main dashboard dropdown. The backend safely executes Regex swaps on the dataset URLs and aggressively updates the hardcoded HTML title strings so the resulting charts are perfectly labeled for the new target data!
- **Cache Transparency**: Reports generated from cache are dynamically badged with a floating `⚡ Cached Run` overlay.
- **🔍 Details Viewer**: A custom Prism.js-powered modal allows you to inspect the syntax-highlighted Python code of any cached script, alongside the exact Original User Prompt that generated it.
- **Fail-Safe Deletions**: The `🗑️ Clear Entire Cache` button features a strict `DELETE` typing requirement to prevent accidental wipes of the sandbox.

### 🧠 Intelligent Data Context Injection
- **No-Join Semantic Mapping**: The backend orchestrator automatically injects the official NYC TLC Data Dictionaries (e.g., `VendorID: 1=CMT, 2=VeriFone` and `payment_type: 1=Credit Card, 2=Cash`) directly into the LLM's system prompt context window. 
- Claude natively maps the physical integers into human-readable labels when generating charts and data tables, eliminating the need for relational database JOIN operations!

### 🤖 Unconstrained MCP Testing
- **General Intelligence Bypass**: A dedicated "Run MCP Test" workflow allows users to bypass the strict Data Analyst prompt guidelines and query the agent for general-purpose logic tests and system status evaluations.

### 🛡️ Robust Code Extraction
- **Regex-based Code Parsing**: The Orchestrator automatically intercepts and extracts clean Python code using Regex, preventing failures when the LLM attempts to wrap code in markdown formatting or conversational filler text.
- **Strict Visualization Prompts**: Enforces strict `Chart.js v4` rendering and syntax to ensure dashboards render natively in the browser without relying on arbitrary local setups.

### Smart Schema & Code Caching
- **AVRO Schema Versioning**: Automatically extracts parquet schemas and stores them as `.avsc` files with SHA256 hashes in the `schema/` folder
- **Hash-Based Code Caching**: Generated code is cached in `code_cache/` using schema hash as the key
- **Prompt Memory**: Original user prompts are persisted inside the cached Python scripts as docstrings for complete auditability.
- **Intelligent Reuse**: Subsequent runs with identical schemas skip Claude API calls entirely, using cached code instead ⚡

### API Usage Tracking & Monitoring
- **Silent Execution Logging**: Orchestrator silently logs every run to `execution_log.json` with:
  - Unique execution ID
  - Timestamp and vehicle/month/task details
  - API called flag (YES/NO)
  - Input/output tokens and cost
  - Code hash and cached code path
  - Success/failure status

- **Comprehensive Dashboard**: Run `python monitor.py` to view:
  - 💰 **Spending Summary** - Total tokens, cost, and session metrics
  - 📅 **Today's Spending** - Current day costs vs daily/hourly limits
  - ⚡ **Cached vs API** - Efficiency ratio and cost savings (e.g., 75% cached = 75% savings)
  - 📋 **Execution History** - Last N runs with 😊 CACHED or 💰 USED indicators
  - 🔌 **API Calls Detail** - Token breakdown per Claude API call

### Spending Limits & Kill Switch
- **Daily Limit**: Default $10.00/day (configurable in `usage_tracker.py`)
- **Hourly Limit**: Default $1.00/hour (configurable in `usage_tracker.py`)
- **Automatic Kill Switch**: Blocks Claude API calls when limits are exceeded, preventing runaway costs
- **Zero-Cost Tracking**: Usage data comes free from API response metadata; no extra API calls needed

## 🏗 Architecture Blueprint

Instead of a monolithic single-agent loop, this project deploys a **Multi-Agent Decoupled Pipeline** to maximize token efficiency, implement active security controls, and prevent drift:

1.  **Schema Specialist Agent (`schema_specialist.py`)**: 
    *   Acts as the system's "Eyes."
    *   Uses an in-memory transport stream (`io.BytesIO`) to query and extract structural file headers and physical parquet layouts via `pyarrow` metadata blocks *without* downloading multi-gigabyte files.
    *   **NEW**: Stores schemas as AVRO format with content hash for change detection and versioning.
    
2.  **Code Generation Agent (`code_generator.py`)**:
    *   Acts as the system's "Muscle."
    *   Consumes the decoupled schema profile to construct type-safe Pandas/PySpark ingestion scripts, removing "guessing" vectors.
    *   **NEW**: Returns usage stats (tokens, cost) alongside generated code for tracking.
    
3.  **Safe Sandbox Environment (`sandbox.py`)**:
    *   Executes dynamic strings within a restricted execution scope.
    *   Deploys active command verification flags to block destructive Windows operations (e.g., `Invoke-Expression`, `Remove-Item`).
    
4.  **Orchestrator Control Loop (`orchestrator.py`)**:
    *   Manages state and cross-agent communication.
    *   Captures runtime exceptions, intercepts tracebacks, and programmatically feeds errors back to the model for self-directed compilation adjustments (Self-Healing).
    *   **NEW**: Implements schema hash checking, code caching, and spending limit enforcement.
    
5.  **Usage Tracker (`usage_tracker.py`)** - NEW:
    *   Tracks API tokens, costs, and execution details
    *   Enforces daily/hourly spending limits with automatic kill switch
    *   Generates execution logs for auditing and monitoring

6.  **Monitoring Dashboard (`monitor.py`)** - NEW:
    *   Beautiful console dashboard showing spending, execution history, and caching efficiency
    *   Zero dependencies (no database required)

## 🧱 Medallion Data Lifecycle Alignment

The architecture is designed to automate logic verification within a **Medallion Data Architecture** (Bronze → Silver → Gold):
*   **Bronze (Ingest Validation)**: The `SchemaSpecialist` acts as an automated ingestion check, catching schema drift in raw telematics data before compute resources are allocated.
*   **Silver (Self-Healing Transformation)**: The `Orchestrator` automates the path from raw ingestion to cleaned datasets. If a transformation fails, the system isolates the logic error and self-corrects the code in real-time.
*   **Gold (Business Logic)**: The engine produces verified, human-readable reports on core metrics like trip counts and financial averages, ready for stakeholder decision-making.

## 🛠 Claude Code Native Extension Integration

This repository is built explicitly to hook into Anthropic's **Claude Code** agentic CLI tool infrastructure using its official, native directory layout format:

### Workspace Directory Layout
```text
D:\self_healing_sandbox\
├── .claude\
│   ├── settings.json
│   ├── hooks\
│   │   └── pre-commit.py
│   └── skills\
│       └── run-pipeline\
│           └── SKILL.md
├── orchestrator.py
├── schema_specialist.py
├── code_generator.py
├── sandbox.py
├── providers.py
├── usage_tracker.py
├── monitor.py
├── mcp_server.py
├── schema/
│   └── *.avsc (auto-generated schema files)
├── code_cache/
│   └── *.py (auto-generated cached code)
├── execution_log.json (auto-generated)
├── api_usage.json (auto-generated)
└── CLAUDE.md
```

## 🚀 Quick Start

### 1. Set Your API Key
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

### 2. Run the Pipeline
```powershell
python orchestrator.py
```

Output will show:
- ✅ **USING CACHED CODE** (if schema unchanged) - Free & fast ⚡
- 🧠 **CALLING CLAUDE** (if new schema) - Calls API once, then caches

### 3. Monitor Your Spending
```powershell
python monitor.py
```

Dashboard shows:
- 😊 CACHED executions (saved money)
- 💰 USED executions (cost money)
- Total tokens, cost, and efficiency metrics

### 4. Adjust Spending Limits (Optional)
Edit `usage_tracker.py`:
```python
DAILY_LIMIT = 10.00    # Change to your daily budget
HOURLY_LIMIT = 1.00    # Change to your hourly budget
```

## 💡 How Caching Works

**First Run (Month 1, Green Taxi):**
1. Downloads parquet schema → Hash: `e0a2cb4f9c6e`
2. No cached code found → **Calls Claude API** (costs tokens)
3. Claude generates code → **Saves to** `code_cache/green_e0a2cb4f9c6e.py`
4. Code executes successfully → **Cached for future use**

**Second Run (Month 2, Green Taxi, Same Schema):**
1. Downloads parquet schema → Hash: `e0a2cb4f9c6e` (same!)
2. Cached code found → **Skips Claude API** (costs $0) ⚡
3. Uses cached code → Instant execution

**Third Run (Month 2, Green Taxi, Schema Changed):**
1. Downloads parquet schema → Hash: `xyz789uvw123` (different!)
2. No cached code for new hash → **Calls Claude API** (new code needed)
3. Saves new code to `code_cache/green_xyz789uvw123.py`

## 📊 Example Dashboard Output

```
================================================================================
  🔍 ORCHESTRATOR MONITORING DASHBOARD
================================================================================

💰 SPENDING SUMMARY
Total Tokens:     1,325
Total Cost:       $0.0028
Total Sessions:   6
Average Cost:     $0.0005/session

⚡ CACHED VS API CALLS
Total Executions:     4
Cached Executions:    3 (75%)  😊 Saved Money!
API Calls:            1 (25%)  💰 Used Credits

📋 EXECUTION HISTORY
ID       Time     Vehicle    API Called   Cost       Status
6ef6632b 2.99s    GREEN-03   😊 CACHED     $0.0000    ✅     
48439e42 9.83s    GREEN-03   😊 CACHED     $0.0000    ✅     
35ae7721 4.84s    YELLOW-01  💰 USED       $0.0017    ✅     
```

## 🚀 Execution Profile (Development Mode)
To ensure cost governance and high-speed testing, the engine is currently optimized for the **Green Taxi Records** dataset partition. This allows for rapid iteration of the self-healing logic and schema mapping over a smaller data footprint before scaling to larger multi-terabyte datasets.

## 🧠 Polyglot AI Engineering (AI Building AI)
This project was developed using a multi-model, AI-first methodology. Rather than relying on a single assistant, I actively orchestrated a diverse ecosystem of foundation models—including **Google Gemini**, **GitHub Copilot**, **OpenAI GPT**, and **Anthropic's Claude**—to collaboratively design, debug, and write the codebase. 

This approach demonstrates a fluency in leveraging the unique strengths of various LLMs (e.g., Copilot for inline autocomplete, Gemini for deep architectural reasoning, and Claude for agentic execution) to rapidly build, debug, and iterate on complex, autonomous AI systems. It is the literal embodiment of using AI to build Agentic AI.

## ⚙️ Engineering Hygiene
*   **Decoupled Architecture**: Logic is modular, allowing for targeted unit testing of sub-agents.
*   **Memory Optimization**: Uses byte-streaming to profile large remote files without high local disk I/O or "Unrecognized Filesystem" errors.
*   **Smart Caching**: Automatic schema versioning and code caching to minimize API calls and costs
*   **Cost Governance**: Spending limits with kill switch prevent budget overruns
*   **Transparent Logging**: All executions logged for auditing and cost analysis
*   **Cross-Platform Readiness**: Fully optimized for Windows 11 CMD environments without Unix bash dependencies.

## 🐳 Production Deployment

This repository includes production-ready deployment files for Jenkins + Docker on Ubuntu:

- **`Dockerfile`** - Multi-stage Python 3.13 image optimized for FastAPI
- **`docker-compose.yml`** - Service definition with persistent volumes (port 8100)
- **`Jenkinsfile`** - Declarative CI/CD pipeline with Jenkins credential store integration
- **`api_server.py`** - REST API microservice (FastAPI on port 8100)
- **`DEPLOYMENT.md`** - Complete deployment guide for Ubuntu + Jenkins

### Quick Deployment
```bash
# 1. Configure Jenkins credentials (Manage Credentials)
# 2. Create pipeline job pointing to this repo
# 3. Jenkins triggers automatically on git push
# 4. API available at http://192.168.6.51:8100
```

**See [DEPLOYMENT.md](DEPLOYMENT.md) for full setup instructions.**

