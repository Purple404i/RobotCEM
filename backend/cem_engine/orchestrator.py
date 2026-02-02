import asyncio
import logging
from typing import Optional, Dict, Any

from backend.cem_engine.prompt_parser import PromptParser
from backend.cem_engine.code_generator import CSharpCodeGenerator
from backend.picogk_bridge.executor import PicoGKExecutor
from backend.cem_engine.physics_validator import PhysicsValidator
from backend.cem_engine.material_db import MATERIAL_DATABASE
from backend.cem_engine.design_rules import DESIGN_RULES
from backend.intelligence.material_pricing import MaterialPricingEngine
from backend.cem_engine.auto_fix import propose_fixes

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """High-level orchestrator that runs parse -> validate -> generate -> price -> auto-fix loop."""

    def __init__(
        self,
        hf_model_name: Optional[str] = None,
        csharp_project_path: Optional[str] = None,
        output_dir: Optional[str] = "backend/outputs",
        pricing_config: Optional[Dict] = None,
    ):
        self.parser = PromptParser(hf_model_name=hf_model_name)
        self.codegen = CSharpCodeGenerator(template_dir="")
        self.executor = PicoGKExecutor(csharp_project_path, output_dir) if csharp_project_path else None
        self.validator = PhysicsValidator(MATERIAL_DATABASE, DESIGN_RULES)
        self.pricing = MaterialPricingEngine(pricing_config or {})

    async def run_from_prompt(self, prompt: str, output_name: str = "generated_design") -> Dict[str, Any]:
        # Parse
        spec = self.parser.parse(prompt)

        # Iterative validate + auto-fix loop
        max_iters = 3
        validation_report = None

        for i in range(max_iters):
            validation_report = self._validate(spec)
            if validation_report.get("structural_valid") and validation_report.get("thermal_valid"):
                break
            logger.info(f"Auto-fix iteration {i+1}: proposing fixes...")
            spec = propose_fixes(spec, validation_report, MATERIAL_DATABASE)

        result: Dict[str, Any] = {
            "spec": spec,
            "validation": validation_report,
            "generation": None,
            "bom": None
        }

        # Generate C# code
        try:
            device_type = spec.get("device_type", "custom")
            csharp_code = self.codegen.generate(spec, device_type)
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            result["generation"] = {"success": False, "error": str(e)}
            return result

        # Run PicoGK if executor available
        if self.executor:
            gen = await self.executor.compile_and_run(csharp_code, output_name)
            result["generation"] = gen
            stl_analysis = gen.get("analysis", {})
        else:
            logger.info("No PicoGK executor configured — skipping compile/run step")
            stl_analysis = {}
            result["generation"] = {"success": False, "error": "No executor configured"}

        # Generate BOM and pricing
        try:
            bom = await self.pricing.generate_bom(spec, stl_analysis)
            result["bom"] = bom
        except Exception as e:
            logger.warning(f"BOM generation failed: {e}")
            result["bom"] = {"error": str(e)}

        return result

    def _validate(self, spec: Dict) -> Dict:
        structural = self.validator.validate_structural(spec)
        thermal = self.validator.validate_thermal(spec)
        manufact = self.validator.validate_manufacturing(spec)

        report = {
            "structural_valid": structural["structural_valid"],
            "structural": structural,
            "thermal_valid": thermal["thermal_valid"],
            "thermal": thermal,
            "manufacturing_valid": manufact["manufacturing_valid"],
            "manufacturing": manufact
        }

        return report
