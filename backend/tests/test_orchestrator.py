import asyncio
import pytest

from backend.cem_engine.orchestrator import EngineOrchestrator


class DummyParser:
    def __init__(self, *_a, **_k):
        pass

    def parse(self, prompt):
        # Return a minimal spec for testing
        return {
            "device_type": "robot_arm",
            "dimensions": {"length": 200.0, "diameter": 40.0, "reach_mm": 200.0},
            "loads": {"payload_kg": 1.0},
            "materials": ["PLA"],
            "requirements": {"safety_factor": 2.0}
        }


class DummyExecutor:
    def __init__(self, *_a, **_k):
        pass

    async def compile_and_run(self, code, output_name):
        return {
            "success": True,
            "stl_path": f"/tmp/{output_name}.stl",
            "analysis": {"volume_cm3": 10.0, "is_watertight": True},
        }


@pytest.mark.asyncio
async def test_orchestrator_end_to_end(monkeypatch):
    # Replace parser and executor with dummies to avoid external deps
    monkeypatch.setattr("backend.cem_engine.orchestrator.PromptParser", DummyParser)
    monkeypatch.setattr("backend.cem_engine.orchestrator.PicoGKExecutor", DummyExecutor)

    orchestrator = EngineOrchestrator(hf_model_name="google/flan-t5-small", csharp_project_path="/tmp")
    result = await orchestrator.run_from_prompt("Make a small arm", output_name="testarm")

    assert "spec" in result
    assert result["generation"]["success"] is True
    assert result["bom"] is not None
