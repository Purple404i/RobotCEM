#!/usr/bin/env python3
"""
Complete training runner that:
1. Collects training data from LEAP 71 documentation
2. Trains LLM with domain knowledge
3. Trains CEM with robotics rules
4. Integrates trained models into the engine
"""

import asyncio
import json
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.training.training_data_collector import TrainingDataCollector
from backend.training.llm_trainer import LLMDomainAdapter, CEMTrainer, train_systems
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_complete_training():
    """Run complete training pipeline"""
    
    print("\n" + "=" * 80)
    print("🚀 ROBOTCEM UNIFIED TRAINING PIPELINE")
    print("=" * 80)
    
    # Step 1: Collect training data
    print("\n📚 STEP 1: Collecting Training Data from LEAP 71 Documentation")
    print("-" * 80)
    
    collector = TrainingDataCollector()
    print("  • Collecting ShapeKernel knowledge...")
    print("  • Collecting LatticeLibrary knowledge...")
    print("  • Collecting robotics domain knowledge...")
    print("  • Collecting CEM optimization rules...")
    
    all_knowledge = collector.collect_all_knowledge()
    training_data_path = collector.save_training_data(all_knowledge)
    
    print(f"\n✅ Collected {len(all_knowledge)} training items")
    
    # Breakdown
    categories = {}
    for item in all_knowledge:
        cat = item.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n   Knowledge Breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"   • {cat.replace('_', ' ').title()}: {count} items")
    
    # Step 2: Train LLM
    print("\n\n🧠 STEP 2: Training LLM with Domain Knowledge")
    print("-" * 80)
    
    print("  • Initializing LLM Domain Adapter...")
    llm_adapter = LLMDomainAdapter()

    print("  • Entering LLM training loop (press Ctrl+C to stop)...")
    examples = []
    index = {}

    # Configurable pass interval (seconds); override with TRAIN_PASS_INTERVAL env var
    pass_interval = int(os.environ.get("TRAIN_PASS_INTERVAL", "1"))

    try:
        # Load initial training data (non-book knowledge)
        num_loaded = llm_adapter.load_training_data(str(training_data_path))
        print(f"   ✓ Items loaded: {num_loaded}")

        # Create system prompts once
        system_prompt_design = llm_adapter.create_system_prompt("design")
        system_prompt_opt = llm_adapter.create_system_prompt("optimization")
        system_prompt_mfg = llm_adapter.create_system_prompt("manufacturing")

        # Repeatedly process all books each pass so the LLM rereads them
        books_dir = Path("books")
        while True:
            any_books = False
            if books_dir.exists() and books_dir.is_dir():
                for book in sorted(books_dir.glob("*.txt")):
                    any_books = True
                    name = book.name
                    print(f"  • Processing book: {name}")
                    try:
                        with open(book, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"   ✗ Failed to read {name}: {e}")
                        continue

                    item = {
                        "category": "books",
                        "title": name,
                        "content": content,
                        "tags": ["book", "corpus", book.stem],
                        "metadata": {"source": str(book)}
                    }

                    # Add to adapter and create training example for this book
                    llm_adapter._process_training_item(item)
                    # Save after processing this book
                    num_examples = llm_adapter.save_training_examples()

                    print(f"   ✓ Finished training on book: {name} (examples saved: {num_examples})")

            if not any_books:
                print("  • No books found in books/. Sleeping 10s (Ctrl+C to stop)...")
                time.sleep(10)
            else:
                print(f"  • Completed a full books pass. Sleeping {pass_interval}s (Ctrl+C to stop)...")
                time.sleep(pass_interval)
    except KeyboardInterrupt:
        print("\n  ✋ LLM training loop interrupted by user (Ctrl+C). Proceeding...")

    # Final index and summary
    index = llm_adapter.create_knowledge_index()
    examples = llm_adapter.generate_training_prompts()
    print(f"\n✅ LLM Training Complete")
    print(f"   • Items loaded: {num_loaded}")
    print(f"   • Training examples generated: {len(examples)}")
    print(f"   • Knowledge categories indexed: {len(index)}")
    print(f"   • System prompts created: 3 (design, optimization, manufacturing)")
    
    # Step 3: Train CEM (single run)
    print("\n\n🔧 STEP 3: Training CEM with Robotics Rules")
    print("-" * 80)

    cem_trainer = CEMTrainer()
    print("  • Initializing CEM Trainer...")

    print("  • Loading design rules...")
    cem_trainer.load_robotics_design_rules()
    design_domains = list(cem_trainer.design_rules.keys())

    print("  • Loading manufacturing rules...")
    cem_trainer.load_manufacturing_rules()
    processes = list(cem_trainer.manufacturing_rules.keys())

    print("  • Loading material database...")
    cem_trainer.load_material_database()
    materials = list(cem_trainer.material_database.keys())

    print("  • Saving CEM training data...")
    cem_trainer.save_cem_training()

    print(f"\n✅ CEM Training Complete")
    print(f"   • Design domains: {', '.join(design_domains)}")
    print(f"   • Manufacturing processes: {', '.join(processes)}")
    print(f"   • Materials in database: {len(materials)}")
    print(f"   • Total manufacturing rules: {sum(len(v) for v in cem_trainer.manufacturing_rules.values())}")
    
    # Step 4: Integration verification
    print("\n\n🔗 STEP 4: Integration Verification")
    print("-" * 80)
    
    print("  • Verifying training data files...")
    training_dir = Path("backend/training")
    files_expected = [
        "training_data.json",
        "llm_training_examples.json",
        "cem_rules.json"
    ]
    
    for file_name in files_expected:
        file_path = training_dir / file_name
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"   ✓ {file_name} ({size_kb:.1f} KB)")
        else:
            print(f"   ✗ {file_name} (NOT FOUND)")
    
    # Step 5: Usage examples
    print("\n\n💡 STEP 5: Integration Examples")
    print("-" * 80)
    
    print("\n  Example 1: Using enhanced prompts in PromptParser")
    print("""
    from backend.training.llm_trainer import LLMDomainAdapter
    
    adapter = LLMDomainAdapter()
    adapter.load_training_data()
    
    # Enhance prompt with context
    user_prompt = "Create a lightweight gripper"
    enhanced = adapter.enhance_prompt_with_context(user_prompt, "design")
    
    # Use in LLM engine
    result = llm_engine.process_prompt(session_id, enhanced, parser)
    """)
    
    print("\n  Example 2: Using CEM training data in orchestrator")
    print("""
    from backend.training.llm_trainer import CEMTrainer
    import json
    
    trainer = CEMTrainer()
    trainer.load_robotics_design_rules()
    trainer.load_manufacturing_rules()
    trainer.load_material_database()
    
    # Access rules in CEM operations
    gripper_rules = trainer.design_rules["gripper"]
    fdm_specs = trainer.manufacturing_rules["FDM"]
    pla_props = trainer.material_database["PLA"]
    """)
    
    print("\n  Example 3: Using retrieval-augmented responses")
    print("""
    adapter = LLMDomainAdapter()
    adapter.load_training_data()
    
    user_prompt = "What lattice should I use?"
    llm_response = await llm_engine.process_prompt(...)
    
    # Enhance with supporting knowledge
    enhanced_response = adapter.create_retrieval_augmented_response(
        user_prompt, llm_response
    )
    """)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print("✅ TRAINING PIPELINE COMPLETE")
    print("=" * 80)
    
    print("\n📊 FINAL STATISTICS:")
    print(f"   • Total training items: {len(all_knowledge)}")
    print(f"   • LLM training examples: {len(examples)}")
    print(f"   • CEM design domains: {len(design_domains)}")
    print(f"   • Manufacturing processes trained: {len(processes)}")
    print(f"   • Materials in CEM database: {len(materials)}")
    
    print("\n📁 OUTPUT FILES:")
    print(f"   • {training_data_path}")
    print(f"   • backend/training/llm_training_examples.json (deduplicated, grows with new books)")
    print(f"   • backend/training/cem_rules.json")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Integrate adapter into PromptParser")
    print("   2. Load CEM rules in Orchestrator")
    print("   3. Test with example prompts")
    print("   4. Fine-tune based on results")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    try:
        # If a project-local virtualenv exists at backend/dw_env, re-exec under it
        venv_python = Path(__file__).parent.parent / "dw_env/bin/python"
        try:
            venv_path = str(venv_python.resolve())
        except Exception:
            venv_path = None

        if venv_path and Path(venv_path).exists():
            current = os.path.realpath(sys.executable)
            if os.path.realpath(venv_path) != current:
                print(f"Activating project virtualenv: {venv_path}")
                os.execv(venv_path, [venv_path, *sys.argv])

        run_complete_training()
    except KeyboardInterrupt:
        print("\nTraining interrupted by user (Ctrl+C). Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)