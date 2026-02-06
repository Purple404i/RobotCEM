import asyncio
import logging
import tempfile
import os
from typing import Optional, Dict, Any

import time
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
from backend.intelligence.market_search import search_part, find_best_offer
from backend.utils.blender_sim import BlenderSimulator

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
        self.blender_sim = BlenderSimulator()
        self.last_interaction = time.time()
        self.current_design = None
        self.output_dir = output_dir or "backend/outputs"

        # Start inactivity monitor if loop is running
        try:
            loop = asyncio.get_running_loop()
            self._inactivity_task = loop.create_task(self._monitor_inactivity())
        except RuntimeError:
            logger.warning("No running event loop, inactivity monitor not started.")
            self._inactivity_task = None

    async def _monitor_inactivity(self):
        """Background task to monitor inactivity."""
        while True:
            await asyncio.sleep(60) # Check every minute
            try:
                await self.check_inactivity_and_analyze()
            except Exception as e:
                logger.error(f"Error in inactivity monitor: {e}")

    async def run_from_prompt(self, prompt: str, output_name: str = "generated_design", max_iters: int = 3) -> Dict[str, Any]:
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

            # If not found in database, search online market
            if not part or result["status"] == "not_found":
                logger.info(f"Component {component.get('name')} not found in DB. Searching market...")
                market_results = search_part(component.get("name", "unknown"))
                best_offer = find_best_offer(market_results)
                if best_offer:
                    result = {
                        "status": "found_in_market",
                        "part": best_offer,
                        "price": best_offer.get("price_usd"),
                        "url": best_offer.get("url")
                    }
                    spec["component_costs"][component["name"]] = best_offer.get("price_usd")

            spec["sourced_components"].append(result)
            if part and result["status"] != "found_in_market":
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

        # Step 6: Get C# code from Aurora LLM
        logger.info("Step 6: Getting C# code from Aurora LLM...")
        csharp_code = spec.get("picogk_code")
        if not csharp_code:
            try:
                device_type = spec.get("device_type", "custom")
                csharp_code = self.codegen.generate(spec, device_type)
            except Exception as e:
                logger.error(f"Fallback code generation failed: {e}")
                result["generation"] = {"success": False, "error": str(e)}
                return result

        # Step 7: Run PicoGK with generated code
        logger.info("Step 7: Executing PicoGK geometry generation...")
        if self.executor:
            gen = await self.executor.compile_and_run(csharp_code, output_name, design_specs=spec)
            result["generation"] = gen
            stl_analysis = gen.get("analysis", {})

            # Step 7.1: Run Blender Simulation
            if gen.get("success") and gen.get("stl_path"):
                logger.info("Step 7.1: Running Blender physics simulation...")

                # Use custom blender script from Aurora if available
                blender_script = spec.get("blender_script")
                if blender_script:
                    # Save custom script to temp file and run
                    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                        f.write(blender_script)
                        temp_script_path = f.name

                    try:
                        sim_result = await self.blender_sim.run_simulation(gen["stl_path"], custom_script_path=temp_script_path)
                    finally:
                        if os.path.exists(temp_script_path):
                            os.unlink(temp_script_path)
                else:
                    sim_result = await self.blender_sim.run_simulation(gen["stl_path"])

                result["simulation"] = sim_result

                # Step 7.2: LLM analysis of results
                logger.info("Step 7.2: LLM analysis of simulation results...")
                llm_analysis = await self.llm_engine.analyze_simulation(stl_analysis, sim_result)
                result["scientific_analysis"] = llm_analysis

                # Auto-fix based on LLM analysis if it failed stability
                if (sim_result.get("fell_over") or llm_analysis.get("suggested_fixes")) and max_iters > 0:
                    logger.info("Design unstable or failed analysis. Applying LLM suggested fixes...")
                    suggested_fixes = llm_analysis.get("suggested_fixes", [])
                    if suggested_fixes:
                        # Apply fixes to spec
                        for fix in suggested_fixes:
                            logger.info(f"Applying fix: {fix}")
                            # Simple logic to update spec based on LLM string suggestions
                            # In a real system, the LLM would provide a JSON patch
                            if "increase" in fix.lower() and "dimension" in fix.lower():
                                spec["dimensions"] = {k: v * 1.2 for k, v in spec.get("dimensions", {}).items() if isinstance(v, (int, float))}
                            if "material" in fix.lower():
                                spec["materials"] = ["Aluminum_6061"] # Upgrade to metal as safe default

                        # Re-run generation with updated spec (recursive call with reduced max_iters)
                        return await self.run_from_prompt(f"Apply fixes to {output_name}: {', '.join(suggested_fixes)}", output_name, max_iters=max_iters-1)
        else:
            logger.info("No PicoGK executor configured — skipping compile/run step")
            stl_analysis = {}
            result["generation"] = {"success": False, "error": "No executor configured"}

        self.current_design = result
        self.last_interaction = time.time()

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

    async def check_inactivity_and_analyze(self) -> Optional[Dict[str, Any]]:
        """
        Check if 5 minutes have passed since last interaction.
        If so, trigger a re-analysis and simulation.
        """
        if self.current_design and (time.time() - self.last_interaction) > 300:
            logger.info("5 minutes of inactivity detected. Triggering automatic re-analysis.")
            # Reset timer so we don't loop
            self.last_interaction = time.time()

            # Re-run simulation and analysis
            if self.current_design.get("generation", {}).get("stl_path"):
                stl_path = self.current_design["generation"]["stl_path"]
                stl_analysis = self.current_design["generation"].get("analysis", {})

                sim_result = await self.blender_sim.run_simulation(stl_path)
                llm_analysis = await self.llm_engine.analyze_simulation(stl_analysis, sim_result)

                self.current_design["simulation"] = sim_result
                self.current_design["scientific_analysis"] = llm_analysis

                return self.current_design
        return None

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
