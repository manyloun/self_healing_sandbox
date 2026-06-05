```markdown
# Autonomous Multi-Agent Medallion Data Pipeline Sandbox

This repository showcases a production-grade, self-healing data analytics engine designed to execute schema mapping, code generation, and automated validation routines over telemetry and transit datasets (NYC TLC Parquet streams). 

Engineered explicitly using **Claude Haiku 4.5** as a decoupled orchestration controller, the framework maps directly to enterprise data platform paradigms utilized across Databricks and Azure environments.

## 🏗 Architecture Blueprint

Instead of a monolithic single-agent loop, this project deploys a **Multi-Agent Decoupled Pipeline** to maximize token efficiency, implement active security controls, and prevent drift:

1.  **Schema Specialist Agent (`schema_specialist.py`)**: 
    *   Acts as the system's "Eyes."
    *   Uses an in-memory transport stream (`io.BytesIO`) to query and extract structural file headers and physical parquet layouts via `pyarrow` metadata blocks *without* downloading multi-gigabyte files.
    *   Outputs an isolated technical profile mapping temporal grains, foreign aggregation keys, and revenue components.
2.  **Code Generation Agent (`code_generator.py`)**:
    *   Acts as the system's "Muscle."
    *   Consumes the decoupled schema profile to construct type-safe Pandas/PySpark ingestion scripts, removing "guessing" vectors.
3.  **Safe Sandbox Environment (`sandbox.py`)**:
    *   Executes dynamic strings within a restricted execution scope.
    *   Deploys active command verification flags to block destructive Windows operations (e.g., `Invoke-Expression`, `Remove-Item`).
4.  **Orchestrator Control Loop (`orchestrator.py`)**:
    *   Manages state and cross-agent communication.
    *   Captures runtime exceptions, intercepts tracebacks, and programmatically feeds errors back to the model for self-directed compilation adjustments (Self-Healing).

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
├── mcp_server.py
└── CLAUDE.md
```

- **`.claude/settings.json`**: Enforces strict environment constraints, targeting native Windows 11 CMD profiles and loading localized Model Context Protocol handlers.
- **`.claude/hooks/pre-commit.py`**: A custom automation hook. It intercepts workspace updates and executes an automated compilation pass over our engine scripts to block invalid code syntax from entering production.
- **`.claude/skills/run-pipeline/SKILL.md`**: A native markdown skill specification utilizing YAML metadata headers to register the `/run-pipeline` sub-agent workflow.
- **`mcp_server.py`**: A custom **Model Context Protocol (MCP) Server**. It currently provides secure LLM access to Databricks Medallion schema definitions, local database analytics (`query_db`), real-time weather APIs (`get_weather`), and financial market data (`get_stock_quote`). The MCP architecture acts as an extensible tool catalog, allowing the engineering team to rapidly integrate and expose new data pipelines, enterprise APIs, and models to Claude as business requirements evolve.

### Running the Custom Workflows
When using the Claude Code tool inside this directory, invoke your custom tools using simple natural language:

```text
Run the /run-pipeline skill for green taxi month 1 to calculate trip count
```

## 🚀 Execution Profile (Development Mode)
To ensure cost governance and high-speed testing, the engine is currently optimized for the **Green Taxi Records** dataset partition. This allows for rapid iteration of the self-healing logic and schema mapping over a smaller data footprint before scaling to larger multi-terabyte datasets.

## 🧠 Polyglot AI Engineering (AI Building AI)
This project was developed using a multi-model, AI-first methodology. Rather than relying on a single assistant, I actively orchestrated a diverse ecosystem of foundation models—including **Google Gemini**, **GitHub Copilot**, **OpenAI GPT**, and **Anthropic's Claude**—to collaboratively design, debug, and write the codebase. 

This approach demonstrates a fluency in leveraging the unique strengths of various LLMs (e.g., Copilot for inline autocomplete, Gemini for deep architectural reasoning, and Claude for agentic execution) to rapidly build, debug, and iterate on complex, autonomous AI systems. It is the literal embodiment of using AI to build Agentic AI.

## ⚙️ Engineering Hygiene
*   **Decoupled Architecture**: Logic is modular, allowing for targeted unit testing of sub-agents.
*   **Memory Optimization**: Uses byte-streaming to profile large remote files without high local disk I/O or "Unrecognized Filesystem" errors.
*   **Cross-Platform Readiness**: Fully optimized for Windows 11 CMD environments without Unix bash dependencies.
```
