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
*   **Bronze (Ingest Validation)**: The `SchemaSpecialist` acts as an automated ingestion check, catching schema drift in raw telematics data before costly compute resources are allocated.
*   **Silver (Self-Healing Transformation)**: The `Orchestrator` automates the path from raw ingestion to cleaned datasets. If a transformation fails, the system isolates the logic error and self-corrects the code in real-time.
*   **Gold (Business Logic)**: The engine produces verified, human-readable reports on core metrics like trip counts and financial averages, ready for stakeholder decision-making.

## 🛠 Claude Code Native Skill Architecture

This repository is built explicitly to hook into Anthropic's **Claude Code** agentic CLI tool using the official native directory structure. Rather than static JSON schemas, custom skills are packaged as isolated directories containing structured Markdown with YAML frontmatter.

### Workspace Blueprint
```text
.claude/
├── settings.json
└── skills/
    └── run-pipeline/
        └── SKILL.md
```

- **`.claude/settings.json`**: Restricts the system execution boundary to native Windows 11 CMD/PowerShell environments, enforcing engineering hygiene.
- **`.claude/skills/run-pipeline/SKILL.md`**: Provides a standard markdown system integration file leveraging YAML metadata hooks to register the `/run-pipeline` sub-agent execution flow.

### Triggering the Automation Workflow
When utilizing the Claude Code CLI inside this workspace directory, you do not need rigid parameter flags. Invoke the pipeline natively via the registered slash command using natural language:

```text
Run the /run-pipeline skill for green taxi month 1 to calculate trip count
```

## 🚀 Execution Profile (Development Mode)
To ensure cost governance and high-speed testing, the engine is currently optimized for the **Green Taxi Records** dataset partition. This allows for rapid iteration of the self-healing logic and schema mapping over a smaller data footprint before scaling to larger multi-terabyte datasets.

## ⚙️ Engineering Hygiene
*   **Decoupled Architecture**: Logic is modular, allowing for targeted unit testing of sub-agents.
*   **Memory Optimization**: Uses byte-streaming to profile large remote files without high local disk I/O or "Unrecognized Filesystem" errors.
*   **Cross-Platform Readiness**: Fully optimized for Windows 11 CMD environments without Unix bash dependencies.
