"""Small example demonstrating the EngineOrchestrator usage.

This script is an example and is not executed by CI. It shows how to wire a local
Hugging Face model (if available) and a PicoGK C# project to run full generation.
"""
import asyncio
from backend.cem_engine.orchestrator import EngineOrchestrator


async def main():
    prompt = (
        "Design a lightweight 3-DOF robotic arm with 300mm reach, payload 2kg, "
        "printed in PLA, prioritize low weight and use lattice infill."
    )

    orchestrator = EngineOrchestrator(
        hf_model_name="google/flan-t5-small",
        csharp_project_path="/path/to/RobotCEM/RobotCEM/",  # update to your local PicoGK project
        output_dir="backend/outputs"
    )

    result = await orchestrator.run_from_prompt(prompt, output_name="demo_arm")
    print("--- RESULT ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
