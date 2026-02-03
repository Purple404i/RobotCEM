import asyncio
import logging
from typing import Optional, Dict, Any

from backend.cem_engine.prompt_parser import PromptParser
from backend.cem_engine.llm_engine import get_llm_engine
from backend.cem_engine.code_generator import CSharpCodeGenerator
from backend.picogk_bridge.executor import PicoGKExecutor
from backend.cem_engine.physics_validator import PhysicsValidator
from backend.cem_engine.material_db import MATERIAL_DATABASE
from backend.cem_engine.design_rules import DESIGN_RULES
from backend.intelligence.material_pricing import MaterialPricingEngine
from backend.storage.database import ComponentSourcingEngine
from backend.cem_engine.auto_fix import propose_fixes
from backend.cem_engine.core import ShapeKernelAnalyzer
from backend.training.llm_trainer import CEMTrainer

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    High-level orchestrator following the plan:
    1. Parse natural language prompt
    2. Search for parts in database (if not found, search online market)
    3. Check pricing and sourcing
    4. Recommend base shapes and lattice structures
    5. Validate physics
    6. Generate C# code for PicoGK
    7. Auto-fix issues iteratively
    8. Generate BOM with costs
    """

    def __init__(
        self,
        hf_model_name: Optional[str] = None,
        csharp_project_path: Optional[str] = None,
        output_dir: Optional[str] = "backend/outputs",
        pricing_config: Optional[Dict] = None,
        db_session: Optional[Any] = None,
    ):
        # Use LLM engine for parsing (hf_model_name kept for backwards compatibility)
        self.parser = PromptParser(hf_model_name=None)
        self.llm_engine = get_llm_engine()
        logger.info("Orchestrator initialized with LLM engine")
        
        # Load CEM training rules (design rules, manufacturing, materials)
        try:
            self.cem_trainer = CEMTrainer()
            self.cem_trainer.load_robotics_design_rules()
            self.cem_trainer.load_manufacturing_rules()
            self.cem_trainer.load_material_database()
            self.cem_rules = self.cem_trainer.get_cem_training_data()
            logger.info("✓ CEM training rules loaded successfully")
            logger.debug(f"  Design domains: {list(self.cem_rules['design_rules'].keys())}")
            logger.debug(f"  Manufacturing processes: {list(self.cem_rules['manufacturing_rules'].keys())}")
            logger.debug(f"  Materials: {list(self.cem_rules['material_database'].keys())}")
        except Exception as e:
            logger.warning(f"Failed to load CEM training rules: {e}")
            self.cem_trainer = None
            self.cem_rules = {}
        
        self.codegen = CSharpCodeGenerator(template_dir="")
        self.executor = PicoGKExecutor(csharp_project_path, output_dir) if csharp_project_path else None
        self.validator = PhysicsValidator(MATERIAL_DATABASE, DESIGN_RULES)
        self.pricing = MaterialPricingEngine(pricing_config or {})
        self.sourcing_engine = ComponentSourcingEngine(db_session)
        self.shape_analyzer = ShapeKernelAnalyzer()

    async def run_from_prompt(self, prompt: str, output_name: str = "generated_design") -> Dict[str, Any]:
        """Execute full workflow: parse -> source components -> validate -> generate -> optimize"""
        logger.info(f"Starting CEM workflow for: {output_name}")
        
        # Step 1: Parse natural language prompt
        spec = self.parser.parse(prompt)
        logger.info(f"Parsed specification: {spec}")
        
        # Step 2: Component sourcing (search database -> online market)
        logger.info("Step 2: Sourcing components from database and marketplace...")
        spec["sourced_components"] = []
        spec["component_costs"] = {}
        
        for component in spec.get("components", []):
            sourcing_result = await self.sourcing_engine.find_component(
                component.get("name", "unknown"),
                component.get("specifications", {}),
                budget=spec.get("budget")
            )
            part, result = sourcing_result
            spec["sourced_components"].append(result)
            if part:
                spec["component_costs"][component["name"]] = part.price
        
        # Step 3: Recommend ShapeKernel BaseShape
        logger.info("Step 3: Recommending optimal BaseShape...")
        base_shape_recommendation = self.shape_analyzer.recommend_base_shape(
            spec.get("device_type", "generic"),
            spec.get("dimensions", {})
        )
        spec["base_shape"] = base_shape_recommendation
        
        # Step 4: Calculate lattice parameters for weight reduction
        if spec.get("optimization_goal") == "lightweight":
            logger.info("Step 4: Calculating lattice infill parameters...")
            lattice_params = self.shape_analyzer.calculate_lattice_parameters(
                volume_reduction_target=spec.get("volume_reduction", 0.3),
                load_case=spec.get("loads")
            )
            spec["lightweighting"] = lattice_params
        
        # Step 5: Iterative validation and auto-fix loop
        logger.info("Step 5: Validating design specifications...")
        max_iters = 3
        validation_report = None

        for i in range(max_iters):
            validation_report = self._validate(spec)
            if validation_report.get("structural_valid") and validation_report.get("thermal_valid"):
                logger.info("Design passed validation")
                break
            logger.info(f"Auto-fix iteration {i+1}: proposing fixes...")
            spec = propose_fixes(spec, validation_report, MATERIAL_DATABASE)

        result: Dict[str, Any] = {
            "spec": spec,
            "validation": validation_report,
            "generation": None,
            "bom": None,
            "sourcing_summary": {
                "components_found": len([s for s in spec.get("sourced_components", []) if s["status"] in ["found_in_database", "found_and_added"]]),
                "components_with_alternatives": len([s for s in spec.get("sourced_components", []) if s["alternatives"]]),
                "total_component_cost": sum(spec.get("component_costs", {}).values())
            }
        }

        # Step 6: Generate C# code with ShapeKernel integration
        logger.info("Step 6: Generating C# code with PicoGK/ShapeKernel...")
        try:
            device_type = spec.get("device_type", "custom")
            csharp_code = self.codegen.generate(spec, device_type)
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            result["generation"] = {"success": False, "error": str(e)}
            return result

        # Step 7: Run PicoGK with enhanced code
        logger.info("Step 7: Executing PicoGK geometry generation...")
        if self.executor:
            gen = await self.executor.compile_and_run(csharp_code, output_name, design_specs=spec)
            result["generation"] = gen
            stl_analysis = gen.get("analysis", {})
        else:
            logger.info("No PicoGK executor configured — skipping compile/run step")
            stl_analysis = {}
            result["generation"] = {"success": False, "error": "No executor configured"}

        # Step 8: Generate BOM and final pricing
        logger.info("Step 8: Generating Bill of Materials with pricing...")
        try:
            bom = await self.pricing.generate_bom(spec, stl_analysis)
            result["bom"] = bom
        except Exception as e:
            logger.warning(f"BOM generation failed: {e}")
            result["bom"] = {"error": str(e)}

        logger.info("CEM workflow completed successfully")
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
