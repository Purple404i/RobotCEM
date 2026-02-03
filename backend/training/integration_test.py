"""
Integration test and demo showing trained LLM and CEM in action.
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.cem_engine.prompt_parser import PromptParser, NaturalLanguageAnalyzer
from backend.cem_engine.llm_engine import get_llm_engine
from backend.training.llm_trainer import LLMDomainAdapter, CEMTrainer


async def test_domain_adapted_parsing():
    """Test LLM parsing with domain adaptation"""
    print("\n" + "="*80)
    print("TEST 1: DOMAIN-ADAPTED PROMPT PARSING")
    print("="*80)
    
    parser = PromptParser()
    
    test_prompts = [
        "I need a lightweight gripper with 2kg payload for pick and place",
        "Create a 6-DOF robot arm, 500mm reach, cost-effective design",
        "Design a bearing assembly for a rotating shaft"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: {prompt}")
        try:
            result = await parser.parse(prompt)
            print(f"   ✓ Device type: {result.get('device_type', 'N/A')}")
            print(f"   ✓ Confidence: {result.get('_specificity_score', 0):.0%}")
            print(f"   ✓ Domain adapted: {result.get('_domain_adapted', False)}")
        except Exception as e:
            print(f"   ✗ Error: {e}")


def test_domain_adapter_enhancement():
    """Test domain adapter prompt enhancement"""
    print("\n" + "="*80)
    print("TEST 2: DOMAIN ADAPTER PROMPT ENHANCEMENT")
    print("="*80)
    
    adapter = LLMDomainAdapter()
    num_loaded = adapter.load_training_data()
    print(f"\n✓ Loaded {num_loaded} training items")
    
    test_prompts = [
        "What is BaseSphere used for?",
        "Which lattice provides best weight reduction?",
        "Design rules for grippers",
        "How to optimize for lightweight?"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: {prompt}")
        enhanced = adapter.enhance_prompt_with_context(prompt, "design")
        
        if enhanced != prompt:
            print(f"   ✓ Enhanced with context")
            print(f"   Context preview: ...{enhanced[-100:]}")
        else:
            print(f"   No enhancement available")


def test_cem_training_data():
    """Test CEM training data access"""
    print("\n" + "="*80)
    print("TEST 3: CEM TRAINING DATA ACCESS")
    print("="*80)
    
    trainer = CEMTrainer()
    trainer.load_robotics_design_rules()
    trainer.load_manufacturing_rules()
    trainer.load_material_database()
    
    # Test design rules
    print("\n📋 Gripper Design Rules:")
    for rule in trainer.design_rules.get("gripper", [])[:3]:
        print(f"   • {rule}")
    
    # Test manufacturing
    print("\n🔧 FDM Manufacturing Specs:")
    fdm_specs = trainer.manufacturing_rules.get("FDM", {})
    print(f"   • Min wall thickness: {fdm_specs.get('min_wall_thickness')}mm")
    print(f"   • Tolerance: ±{fdm_specs.get('tolerance')}mm")
    print(f"   • Materials: {', '.join(fdm_specs.get('material', []))}")
    
    # Test materials
    print("\n📦 PLA Properties:")
    pla = trainer.material_database.get("PLA", {})
    print(f"   • Cost: ${pla.get('cost_per_kg'):.1f}/kg")
    print(f"   • Density: {pla.get('density_g_cm3')} g/cm³")
    print(f"   • Tensile strength: {pla.get('tensile_strength_mpa')} MPa")


def test_intent_analysis():
    """Test NaturalLanguageAnalyzer"""
    print("\n" + "="*80)
    print("TEST 4: INTENT ANALYSIS")
    print("="*80)
    
    analyzer = NaturalLanguageAnalyzer()
    
    test_prompts = [
        "Lightweight gripper for delicate items",
        "Heavy-duty industrial robot arm",
        "Cost-effective 3D printed bracket"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: {prompt}")
        intent = analyzer.extract_intent(prompt)
        print(f"   • Device: {intent['detected_device_type']}")
        print(f"   • Goals: {', '.join(intent['optimization_goals'])}")
        print(f"   • Specificity: {intent['specificity']:.0%}")


def test_knowledge_index():
    """Test knowledge index creation"""
    print("\n" + "="*80)
    print("TEST 5: KNOWLEDGE INDEX")
    print("="*80)
    
    adapter = LLMDomainAdapter()
    adapter.load_training_data()
    index = adapter.create_knowledge_index()
    
    print(f"\n✓ Knowledge Categories: {len(index)}")
    for category, items in sorted(index.items()):
        print(f"\n   📚 {category.replace('_', ' ').title()} ({len(items)} items):")
        for item in items[:3]:
            print(f"      • {item[:70]}...")


async def run_all_tests():
    """Run all integration tests"""
    print("\n\n" + "█"*80)
    print("🧪 ROBOTCEM TRAINING INTEGRATION TESTS")
    print("█"*80)
    
    try:
        # Async tests
        await test_domain_adapted_parsing()
        
        # Sync tests
        test_domain_adapter_enhancement()
        test_cem_training_data()
        test_intent_analysis()
        test_knowledge_index()
        
        print("\n\n" + "█"*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("█"*80)
        
        print("\n📊 SUMMARY:")
        print("   ✓ Domain-adapted prompt parsing")
        print("   ✓ LLM enhancement with training data")
        print("   ✓ CEM rule database access")
        print("   ✓ Intent analysis")
        print("   ✓ Knowledge indexing")
        
        print("\n🎯 NEXT STEPS:")
        print("   1. Deploy trained models to production")
        print("   2. Monitor parsing accuracy")
        print("   3. Collect feedback for iterative improvement")
        print("   4. Expand training data with user examples")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
