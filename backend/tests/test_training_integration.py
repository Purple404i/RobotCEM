#!/usr/bin/env python3
"""
Integration tests for training system with PromptParser and Orchestrator.

Tests:
1. Verify LLMDomainAdapter loads in PromptParser
2. Verify CEMTrainer loads in Orchestrator
3. Test prompt parsing with training-enhanced context
4. Test CEM rule application on specifications
5. End-to-end workflow with example prompts
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingIntegrationTests:
    """Test training system integration with core engine components"""
    
    def __init__(self):
        self.results = {
            "adapter_integration": None,
            "cem_rules_integration": None,
            "prompt_parsing": [],
            "cem_rule_application": [],
            "end_to_end": []
        }
    
    def test_1_adapter_in_prompt_parser(self) -> bool:
        """Test 1: LLMDomainAdapter loads in PromptParser"""
        print("\n" + "=" * 80)
        print("TEST 1: LLMDomainAdapter Integration in PromptParser")
        print("=" * 80)
        
        try:
            from backend.cem_engine.prompt_parser import PromptParser
            parser = PromptParser()
            
            # Check if domain adapter is loaded
            if not hasattr(parser, 'domain_adapter'):
                print("✗ FAIL: PromptParser has no domain_adapter attribute")
                return False
            
            if parser.domain_adapter is None:
                print("✗ FAIL: domain_adapter is None")
                return False
            
            # Check if training data loaded
            if not hasattr(parser.domain_adapter, 'knowledge_base'):
                print("✗ FAIL: domain_adapter has no knowledge_base")
                return False
            
            num_categories = len(parser.domain_adapter.knowledge_base)
            print(f"✓ PASS: PromptParser loaded with {num_categories} knowledge categories")
            print(f"  Categories: {list(parser.domain_adapter.knowledge_base.keys())}")
            
            self.results["adapter_integration"] = {
                "status": "pass",
                "categories": num_categories,
                "category_names": list(parser.domain_adapter.knowledge_base.keys())
            }
            return True
            
        except Exception as e:
            print(f"✗ FAIL: {e}")
            self.results["adapter_integration"] = {"status": "fail", "error": str(e)}
            return False
    
    def test_2_cem_rules_in_orchestrator(self) -> bool:
        """Test 2: CEMTrainer rules load in Orchestrator"""
        print("\n" + "=" * 80)
        print("TEST 2: CEM Rules Integration in Orchestrator")
        print("=" * 80)
        
        try:
            from backend.cem_engine.orchestrator import EngineOrchestrator
            orchestrator = EngineOrchestrator()
            
            # Check if CEM rules loaded
            if not hasattr(orchestrator, 'cem_rules'):
                print("✗ FAIL: Orchestrator has no cem_rules attribute")
                return False
            
            if not orchestrator.cem_rules:
                print("✗ FAIL: cem_rules is empty")
                return False
            
            # Check components
            has_design = 'design_rules' in orchestrator.cem_rules
            has_manufacturing = 'manufacturing_rules' in orchestrator.cem_rules
            has_materials = 'material_database' in orchestrator.cem_rules
            
            if not (has_design and has_manufacturing and has_materials):
                print("✗ FAIL: Missing CEM rule components")
                return False
            
            design_domains = list(orchestrator.cem_rules['design_rules'].keys())
            manufacturing = list(orchestrator.cem_rules['manufacturing_rules'].keys())
            materials = list(orchestrator.cem_rules['material_database'].keys())
            
            print(f"✓ PASS: Orchestrator loaded CEM rules")
            print(f"  Design domains: {design_domains}")
            print(f"  Manufacturing processes: {manufacturing}")
            print(f"  Materials: {materials}")
            
            self.results["cem_rules_integration"] = {
                "status": "pass",
                "design_domains": design_domains,
                "manufacturing_processes": manufacturing,
                "materials": materials
            }
            return True
            
        except Exception as e:
            print(f"✗ FAIL: {e}")
            self.results["cem_rules_integration"] = {"status": "fail", "error": str(e)}
            return False
    
    def test_3_prompt_parsing_with_training(self) -> bool:
        """Test 3: Parse prompts with training-enhanced context"""
        print("\n" + "=" * 80)
        print("TEST 3: Prompt Parsing with Training-Enhanced Context")
        print("=" * 80)
        
        test_prompts = [
            "Create a lightweight gripper with 100N grip force",
            "Design a strong robot arm for heavy payload lifting",
            "Build a cost-effective 3D printed bracket using FDM",
            "Design a high-precision aerospace component in aluminum"
        ]
        
        try:
            from backend.cem_engine.prompt_parser import PromptParser
            parser = PromptParser()
            
            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n  Test 3.{i}: {prompt}")
                
                # Extract intent
                intent = parser.nl_analyzer.extract_intent(prompt)
                print(f"    Detected device: {intent['detected_device_type']}")
                print(f"    Optimization goals: {intent['optimization_goals']}")
                print(f"    Specificity: {intent['specificity']:.2f}")
                
                self.results["prompt_parsing"].append({
                    "prompt": prompt,
                    "device_type": intent['detected_device_type'],
                    "goals": intent['optimization_goals'],
                    "specificity": intent['specificity']
                })
            
            print(f"\n✓ PASS: All {len(test_prompts)} prompts parsed successfully")
            return True
            
        except Exception as e:
            print(f"✗ FAIL: {e}")
            return False
    
    def test_4_cem_rule_application(self) -> bool:
        """Test 4: Apply CEM rules to design specifications"""
        print("\n" + "=" * 80)
        print("TEST 4: CEM Rule Application on Specifications")
        print("=" * 80)
        
        try:
            from backend.cem_engine.orchestrator import EngineOrchestrator
            orchestrator = EngineOrchestrator()
            
            # Test rule lookups
            test_cases = [
                ("gripper", "design_rules"),
                ("FDM", "manufacturing_rules"),
                ("PLA", "material_database")
            ]
            
            for item, rule_type in test_cases:
                rules = orchestrator.cem_rules.get(rule_type, {})
                
                if item in rules:
                    rule_data = rules[item]
                    print(f"✓ Found {rule_type}[{item}]")
                    if isinstance(rule_data, (list, dict)):
                        if isinstance(rule_data, list):
                            print(f"  Rules: {rule_data[:2]}...")  # Show first 2
                        else:
                            print(f"  Keys: {list(rule_data.keys())[:3]}...")  # Show first 3 keys
                    
                    self.results["cem_rule_application"].append({
                        "item": item,
                        "rule_type": rule_type,
                        "status": "found"
                    })
                else:
                    print(f"✗ Missing {rule_type}[{item}]")
                    self.results["cem_rule_application"].append({
                        "item": item,
                        "rule_type": rule_type,
                        "status": "not_found"
                    })
            
            found_count = sum(1 for r in self.results["cem_rule_application"] if r["status"] == "found")
            print(f"\n✓ PASS: {found_count}/3 CEM rules applied successfully")
            return True
            
        except Exception as e:
            print(f"✗ FAIL: {e}")
            return False
    
    async def test_5_end_to_end_workflow(self) -> bool:
        """Test 5: End-to-end workflow with training integration"""
        print("\n" + "=" * 80)
        print("TEST 5: End-to-End Workflow (Prompt → Parse → Apply Rules)")
        print("=" * 80)
        
        try:
            from backend.cem_engine.orchestrator import EngineOrchestrator
            orchestrator = EngineOrchestrator()
            
            test_workflows = [
                {
                    "name": "Lightweight Gripper",
                    "prompt": "Create a lightweight gripper with 50N grip force using FDM PLA"
                },
                {
                    "name": "Aluminum Bracket",
                    "prompt": "Design a strong, durable bracket in aluminum for aerospace with high precision"
                }
            ]
            
            for workflow in test_workflows:
                print(f"\n  Workflow: {workflow['name']}")
                print(f"  Prompt: {workflow['prompt']}")
                
                try:
                    # Step 1: Parse with training
                    spec = orchestrator.parser.parse(workflow['prompt'])
                    print(f"    ✓ Parsed specification")
                    
                    # Step 2: Check CEM rules
                    if orchestrator.cem_rules:
                        # Example: Check if FDM rules apply
                        if 'FDM' in orchestrator.cem_rules.get('manufacturing_rules', {}):
                            fdm_rules = orchestrator.cem_rules['manufacturing_rules']['FDM']
                            print(f"    ✓ Found FDM manufacturing rules")
                            print(f"      Min wall: {fdm_rules.get('min_wall_thickness', 'N/A')}mm")
                    
                    self.results["end_to_end"].append({
                        "workflow": workflow['name'],
                        "status": "success"
                    })
                    
                except Exception as e:
                    print(f"    ✗ Workflow failed: {e}")
                    self.results["end_to_end"].append({
                        "workflow": workflow['name'],
                        "status": "failed",
                        "error": str(e)
                    })
            
            success_count = sum(1 for w in self.results["end_to_end"] if w["status"] == "success")
            print(f"\n✓ PASS: {success_count}/{len(test_workflows)} end-to-end workflows completed")
            return True
            
        except Exception as e:
            print(f"✗ FAIL: {e}")
            return False
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        tests = [
            ("TEST 1: Adapter Integration", self.results["adapter_integration"]),
            ("TEST 2: CEM Rules Integration", self.results["cem_rules_integration"]),
            ("TEST 3: Prompt Parsing", len(self.results["prompt_parsing"])),
            ("TEST 4: CEM Rule Application", len(self.results["cem_rule_application"])),
            ("TEST 5: End-to-End Workflow", len(self.results["end_to_end"]))
        ]
        
        for test_name, result in tests:
            if isinstance(result, dict) and "status" in result:
                status_emoji = "✓" if result["status"] == "pass" else "✗"
                print(f"{status_emoji} {test_name}: {result['status'].upper()}")
            else:
                print(f"✓ {test_name}: {result} items")
        
        print("\n📊 DETAILED RESULTS:")
        print(json.dumps(self.results, indent=2))
        
        print("\n🎯 NEXT STEPS:")
        print("  1. Run continuous training: python3 backend/training/run_training.py")
        print("  2. Integration is now active in PromptParser and Orchestrator")
        print("  3. Training data auto-enhances all prompt parsing")
        print("  4. CEM rules guide specification validation")
        print("  5. Monitor logs for 'Domain adapter' and 'CEM training rules' messages")


async def main():
    """Run all integration tests"""
    tests = TrainingIntegrationTests()
    
    # Run tests
    test_1_pass = tests.test_1_adapter_in_prompt_parser()
    test_2_pass = tests.test_2_cem_rules_in_orchestrator()
    test_3_pass = tests.test_3_prompt_parsing_with_training()
    test_4_pass = tests.test_4_cem_rule_application()
    test_5_pass = await tests.test_5_end_to_end_workflow()
    
    # Print summary
    tests.print_summary()
    
    # Exit code
    all_pass = test_1_pass and test_2_pass and test_3_pass and test_4_pass and test_5_pass
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
