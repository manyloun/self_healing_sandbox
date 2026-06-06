---
name: run-pipeline
description: Automates the multi-agent self-healing data pipeline for NYC TLC/Green taxi telemetry verification checks. Use this when the user requests an autonomous data validation run or pipeline analysis.
---

# Reusable Data Pipeline Execution Workflow

When the user triggers this skill via `/run-pipeline` or asks to run the autonomous pipeline, execute the following step-by-step procedures:

## Step 1: Input Parameter Mapping
Analyze the user's intent to extract three critical variables:
- `vehicle_type`: Must be strictly one of `green`, `yellow`, `fhv`, or `hvfhv` (Default to `green` if unstated).
- `month`: An integer representing the target calendar month index.
- `goal`: The core analytical or data-science target summary requested.

## Step 2: Local Script Dispatched Execution
Utilize your terminal tool execution capabilities to invoke the Windows 11 Python environment. You must pass the variables directly to our state controller orchestrator using native argument hooks.

Run the script exactly via this template format:
```bash
python orchestrator.py
```

*Note: Since the orchestrator's code is already optimized for local Green Taxi development, execute the script directly and intercept the console output parameters to deliver the final report text back to the session window.*
