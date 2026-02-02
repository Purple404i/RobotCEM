## Backend CEM Engine

This folder contains the Computational Engineering Model (CEM) backend pieces:

- `cem_engine` : prompt parsing, code generation, validation, orchestration.
- `picogk_bridge` : tooling to compile and run the C# PicoGK generator.
- `intelligence` : pricing and market search helpers.

Quick start (example, not executed here):

1. Install dependencies from `backend/requirements.txt`.
2. Configure local Hugging Face model or remote provider and set `hf_model_name`.
3. Provide the `csharp_project_path` pointing at the PicoGK C# project.
4. Run `python -m backend.examples.run_demo` to exercise the orchestrator (after installing deps).
