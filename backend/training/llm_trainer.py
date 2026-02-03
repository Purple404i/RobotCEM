"""
LLM Fine-tuning and Domain Adaptation Module.
Trains the LLM engine on domain-specific knowledge about robotics, CEM, and LEAP 71 libraries.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example for the LLM"""
    prompt: str
    response: str
    category: str
    intent: str
    tags: List[str]
    domain: str = "robotics"
    confidence: float = 0.95
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LLMDomainAdapter:
    """
    Adapts and fine-tunes the LLM engine with domain-specific knowledge.
    Since we can't directly fine-tune without access to model weights,
    we create a knowledge base that enhances prompt responses through:
    1. Context injection
    2. Response refinement
    3. Example-based learning
    """
    
    def __init__(self):
        self.training_examples: List[TrainingExample] = []
        self.knowledge_base: Dict[str, List[Dict]] = {}
        self.prompt_templates: Dict[str, str] = {}
        self.cache: Dict[str, str] = {}
        self.training_data_path = Path("backend/training/training_data.json")
        
    def load_training_data(self, data_path: Optional[str] = None) -> int:
        """Load training data from JSON file"""
        path = Path(data_path or self.training_data_path)
        
        if not path.exists():
            logger.warning(f"Training data not found at {path}")
            return 0
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        for item in data:
            self._process_training_item(item)
        
        logger.info(f"Loaded {len(data)} training items")
        return len(data)

    def load_books_folder(self, folder_path: str | Path = "books") -> int:
        """Load plain-text files from a folder (e.g., `books/`) into the knowledge base.

        Each text file becomes a knowledge item with category `books` and will be
        converted into training examples by the existing pipeline.
        """
        p = Path(folder_path)
        if not p.exists() or not p.is_dir():
            return 0

        count = 0
        for txt in sorted(p.glob("*.txt")):
            try:
                with open(txt, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                # skip unreadable files
                continue

            item = {
                "category": "books",
                "title": txt.name,
                "content": content,
                "tags": ["book", "corpus", txt.stem],
                "metadata": {"source": str(txt)}
            }

            # Reuse existing processing pipeline
            self._process_training_item(item)
            count += 1

        return count
    
    def _process_training_item(self, item: Dict) -> None:
        """Process a training item and add to knowledge base"""
        category = item.get("category", "general")
        
        if category not in self.knowledge_base:
            self.knowledge_base[category] = []
        
        self.knowledge_base[category].append(item)
        
        # Create training examples for LLM
        if "content" in item:
            example = self._create_training_example(item)
            self.training_examples.append(example)
    
    def _create_training_example(self, item: Dict) -> TrainingExample:
        """Convert knowledge item to training example"""
        category = item.get("category", "general")
        title = item.get("title", "")
        content = item.get("content", "")
        metadata = item.get("metadata", {})
        
        # Create prompt-response pair
        if category == "base_shape":
            shape = metadata.get("shape", "")
            prompt = f"What is {shape}? How is it used in robotics design?"
            response = content
        elif category == "lattice_library":
            lattice_type = metadata.get("type", "")
            prompt = f"Explain {lattice_type} and its applications"
            response = content
        elif category == "robotics":
            domain = item.get("domain", "")
            prompt = f"What are the design rules for {domain}?"
            response = content
        else:
            prompt = title
            response = content
        
        return TrainingExample(
            prompt=prompt,
            response=response,
            category=category,
            intent=item.get("intent", "general"),
            tags=item.get("tags", []),
            domain=item.get("domain", "robotics")
        )
    
    def create_system_prompt(self, intent: str = "design") -> str:
        """Create enhanced system prompt with domain knowledge"""
        base_prompt = """You are an expert robotics design engineer with deep knowledge of:
- LEAP 71 ShapeKernel library and its 6 base shapes (Box, Sphere, Cylinder, Pipe, Lens, Ring)
- LEAP 71 LatticeLibrary for weight optimization (BodyCentric, Octahedron lattices)
- PicoGK geometry kernel for computational design
- Robotics component selection and optimization
- Manufacturing processes (FDM, SLA, SLS, CNC)
- Computational Engineering Models (CEM) for design optimization

Your responses are precise, technically accurate, and grounded in engineering best practices."""

        if intent == "design":
            return base_prompt + "\nFocus on: geometry design, shape selection, and optimization strategies."
        elif intent == "optimization":
            return base_prompt + "\nFocus on: weight reduction, cost optimization, and performance tuning."
        elif intent == "manufacturing":
            return base_prompt + "\nFocus on: manufacturing constraints, tolerances, and material selection."
        else:
            return base_prompt
    
    def enhance_prompt_with_context(self, user_prompt: str, intent: str = "design") -> str:
        """Enhance user prompt with relevant domain context"""
        # Extract intent keywords
        keywords = self._extract_keywords(user_prompt)
        
        # Find relevant knowledge items
        relevant_knowledge = self._find_relevant_knowledge(keywords)
        
        if not relevant_knowledge:
            return user_prompt
        
        # Build context
        context_parts = [user_prompt, "\n--- RELEVANT KNOWLEDGE ---"]
        for item in relevant_knowledge[:3]:  # Top 3 most relevant
            title = item.get("title", "")
            content = item.get("content", "")
            context_parts.append(f"• {title}: {content[:200]}...")
        
        return "\n".join(context_parts)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Common robotics/CEM keywords
        keywords_list = [
            "gripper", "arm", "actuator", "bearing", "motor", "servo", "stepper",
            "lattice", "weight", "optimization", "lightweight", "cost", "durable",
            "3d print", "cnc", "fdm", "sla", "sls",
            "basebox", "basesphere", "basecylinder", "basepipe", "baselens", "basering",
            "picogk", "shapekernel", "leap71"
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keywords_list:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _find_relevant_knowledge(self, keywords: List[str]) -> List[Dict]:
        """Find knowledge items matching keywords"""
        relevant = []
        
        for category, items in self.knowledge_base.items():
            for item in items:
                item_tags = item.get("tags", [])
                matches = sum(1 for kw in keywords for tag in item_tags if kw.lower() in tag.lower())
                
                if matches > 0:
                    relevant.append((item, matches))
        
        # Sort by match count descending
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in relevant]
    
    def generate_training_prompts(self) -> List[Tuple[str, str]]:
        """Generate prompt-response pairs from knowledge base for training"""
        prompts = []
        
        # Base shape prompts
        for category in ["base_shape"]:
            if category in self.knowledge_base:
                for item in self.knowledge_base[category]:
                    metadata = item.get("metadata", {})
                    shape = metadata.get("shape", "")
                    use_cases = metadata.get("use_cases", [])
                    
                    # Multiple prompt variations for same knowledge
                    prompts.append((
                        f"What is {shape} used for?",
                        f"{shape} is used for: {', '.join(use_cases)}. {item.get('content', '')}"
                    ))
                    
                    params = metadata.get("parameters", [])
                    if params:
                        prompts.append((
                            f"What parameters does {shape} take?",
                            f"{shape} requires parameters: {', '.join(params)}"
                        ))
        
        # Lattice prompts
        for category in ["lattice_library"]:
            if category in self.knowledge_base:
                for item in self.knowledge_base[category]:
                    if item.get("type") == "lattice_type":
                        metadata = item.get("metadata", {})
                        lattice = metadata.get("type", "")
                        weight_red = metadata.get("weight_reduction", "")
                        
                        prompts.append((
                            f"What weight reduction does {lattice} provide?",
                            f"{lattice} provides {weight_red} weight reduction. {item.get('content', '')}"
                        ))
        
        # Optimization goal prompts
        for category in ["cem"]:
            if category in self.knowledge_base:
                for item in self.knowledge_base[category]:
                    if item.get("type") == "optimization_strategy":
                        goal = item.get("goal", "")
                        metadata = item.get("metadata", {})
                        improvement = metadata.get("estimated_improvement", "")
                        
                        prompts.append((
                            f"How do I optimize for {goal}?",
                            f"{item.get('content', '')} Estimated improvement: {improvement}"
                        ))
        
        return prompts
    
    def save_training_examples(self, output_path: str = "backend/training/llm_training_examples.json") -> int:
        """Save training examples to file, deduplicating by prompt+response pair"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Deduplicate examples by (prompt, response) pair to avoid duplicates on repeated runs
        seen = set()
        unique_examples = []
        for ex in self.training_examples:
            key = (ex.prompt, ex.response)
            if key not in seen:
                seen.add(key)
                unique_examples.append(ex)
        
        examples_data = [ex.to_dict() for ex in unique_examples]
        
        with open(output_path, 'w') as f:
            json.dump(examples_data, f, indent=2)
        
        logger.info(f"Saved {len(examples_data)} training examples (deduplicated) to {output_path}")
        return len(examples_data)
    
    def create_retrieval_augmented_response(
        self, 
        user_prompt: str,
        llm_response: str
    ) -> str:
        """Enhance LLM response with retrieval-augmented generation (RAG)"""
        keywords = self._extract_keywords(user_prompt)
        relevant_knowledge = self._find_relevant_knowledge(keywords)
        
        if not relevant_knowledge:
            return llm_response
        
        # Add knowledge to response
        response_parts = [llm_response, "\n\n📚 **Supporting Knowledge:**"]
        
        for item in relevant_knowledge[:2]:
            title = item.get("title", "")
            category = item.get("category", "")
            response_parts.append(f"\n• **{title}** ({category})")
        
        return "\n".join(response_parts)
    
    def create_knowledge_index(self) -> Dict[str, List[str]]:
        """Create searchable index of all knowledge"""
        index = {}
        
        for category, items in self.knowledge_base.items():
            index[category] = []
            for item in items:
                title = item.get("title", "")
                tags = item.get("tags", [])
                index[category].append(f"{title} [{', '.join(tags)}]")
        
        return index


class CEMTrainer:
    """
    Trains the CEM engine with design rules and manufacturing constraints.
    """
    
    def __init__(self):
        self.design_rules: Dict[str, List[str]] = {}
        self.manufacturing_rules: Dict[str, Dict] = {}
        self.material_database: Dict[str, Dict] = {}
        self.component_specs: Dict[str, Dict] = {}
    
    def load_robotics_design_rules(self) -> None:
        """Load and structure robotics design rules"""
        self.design_rules = {
            "gripper": [
                "Apply 2x minimum safety factor on payload",
                "Jaw width range: 20-150mm",
                "Parallel jaw stroke: 10-100mm",
                "Material: Al6061 frames, stainless jaws",
                "Grip force range: 50-500N"
            ],
            "arm": [
                "Reach: 500-2500mm typical",
                "Payload inversely proportional to reach",
                "6-DOF standard configuration",
                "Carbon fiber for links, aluminum for joints",
                "3x safety factor for load capacity"
            ],
            "bearing": [
                "Dynamic load rating 2x minimum",
                "Ball bearing for low friction",
                "Roller bearing for heavy loads",
                "Bore range: 5-50mm for robotics",
                "Stainless steel for corrosive environments"
            ]
        }
    
    def load_manufacturing_rules(self) -> None:
        """Load manufacturing constraints and tolerances"""
        self.manufacturing_rules = {
            "FDM": {
                "min_wall_thickness": 0.8,
                "min_feature": 1.0,
                "tolerance": 0.3,
                "material": ["PLA", "ABS", "PETG", "Nylon"],
                "cost_per_kg": 5.0,
                "print_speed": "50-150 mm/s",
                "support_angle": 45.0
            },
            "SLA": {
                "min_wall_thickness": 0.4,
                "min_feature": 0.5,
                "tolerance": 0.1,
                "material": ["Standard", "Tough", "Flexible"],
                "cost_per_ml": 0.05,
                "print_speed": "25 mm/h",
                "escape_holes": True
            },
            "SLS": {
                "min_wall_thickness": 0.7,
                "min_feature": 0.5,
                "tolerance": 0.15,
                "material": ["Nylon 12", "Nylon Glass", "TPU"],
                "cost_per_kg": 20.0,
                "print_speed": "10 mm/h",
                "support_angle": 90.0
            },
            "CNC": {
                "min_wall_thickness": 0.5,
                "min_feature": 0.1,
                "tolerance": 0.05,
                "material": ["Al6061", "Steel", "Brass", "Titanium"],
                "cost_per_hour": 50.0,
                "coolant": "Required",
                "tool_changes": "Multiple"
            }
        }
    
    def load_material_database(self) -> None:
        """Load material properties and costs"""
        self.material_database = {
            "PLA": {
                "category": "thermoplastic",
                "process": "FDM",
                "cost_per_kg": 5.0,
                "density_g_cm3": 1.24,
                "tensile_strength_mpa": 50,
                "print_temp": 200,
                "environmental": "Biodegradable"
            },
            "ABS": {
                "category": "thermoplastic",
                "process": "FDM",
                "cost_per_kg": 8.0,
                "density_g_cm3": 1.05,
                "tensile_strength_mpa": 40,
                "print_temp": 240,
                "environmental": "Impact resistant"
            },
            "PETG": {
                "category": "thermoplastic",
                "process": "FDM",
                "cost_per_kg": 10.0,
                "density_g_cm3": 1.27,
                "tensile_strength_mpa": 55,
                "print_temp": 235,
                "environmental": "Balanced properties"
            },
            "Al6061": {
                "category": "aluminum",
                "process": "CNC",
                "cost_per_kg": 3.0,
                "density_g_cm3": 2.70,
                "tensile_strength_mpa": 310,
                "machinability": "Good",
                "environmental": "Recyclable"
            },
            "Steel": {
                "category": "metal",
                "process": "CNC",
                "cost_per_kg": 2.0,
                "density_g_cm3": 7.85,
                "tensile_strength_mpa": 400,
                "machinability": "Moderate",
                "environmental": "Recyclable"
            }
        }
    
    def get_cem_training_data(self) -> Dict[str, Any]:
        """Return all CEM training data"""
        return {
            "design_rules": self.design_rules,
            "manufacturing_rules": self.manufacturing_rules,
            "material_database": self.material_database
        }
    
    def save_cem_training(self, output_path: str = "backend/training/cem_rules.json") -> None:
        """Save CEM training data to file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        data = self.get_cem_training_data()
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved CEM training data to {output_path}")


async def train_systems(
    data_path: Optional[str] = None,
    output_dir: str = "backend/training"
) -> Dict[str, Any]:
    """
    Complete training pipeline for LLM and CEM engines.
    """
    logger.info("=" * 70)
    logger.info("STARTING UNIFIED TRAINING PIPELINE")
    logger.info("=" * 70)
    
    results = {
        "llm_training": {},
        "cem_training": {},
        "timestamps": {}
    }
    
    # LLM Training
    logger.info("\n1️⃣  Initializing LLM Domain Adapter...")
    llm_adapter = LLMDomainAdapter()
    
    logger.info("2️⃣  Loading training data...")
    num_items = llm_adapter.load_training_data(data_path)
    results["llm_training"]["knowledge_items_loaded"] = num_items
    
    logger.info("3️⃣  Generating training examples...")
    examples = llm_adapter.generate_training_prompts()
    num_examples = llm_adapter.save_training_examples(
        f"{output_dir}/llm_training_examples.json"
    )
    results["llm_training"]["training_examples"] = num_examples
    
    logger.info("4️⃣  Creating knowledge index...")
    index = llm_adapter.create_knowledge_index()
    logger.info(f"   Knowledge categories: {list(index.keys())}")
    results["llm_training"]["knowledge_categories"] = list(index.keys())
    
    # CEM Training
    logger.info("\n5️⃣  Initializing CEM Trainer...")
    cem_trainer = CEMTrainer()
    
    logger.info("6️⃣  Loading CEM rules...")
    cem_trainer.load_robotics_design_rules()
    cem_trainer.load_manufacturing_rules()
    cem_trainer.load_material_database()
    
    logger.info("7️⃣  Saving CEM training data...")
    cem_trainer.save_cem_training(f"{output_dir}/cem_rules.json")
    
    cem_data = cem_trainer.get_cem_training_data()
    results["cem_training"]["design_rule_categories"] = list(cem_data["design_rules"].keys())
    results["cem_training"]["manufacturing_processes"] = list(cem_data["manufacturing_rules"].keys())
    results["cem_training"]["materials"] = list(cem_data["material_database"].keys())
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ TRAINING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\n📊 LLM Training Results:")
    logger.info(f"   • Knowledge items loaded: {results['llm_training']['knowledge_items_loaded']}")
    logger.info(f"   • Training examples: {results['llm_training']['training_examples']}")
    logger.info(f"   • Knowledge categories: {', '.join(results['llm_training']['knowledge_categories'])}")
    
    logger.info(f"\n📊 CEM Training Results:")
    logger.info(f"   • Design domains: {', '.join(results['cem_training']['design_rule_categories'])}")
    logger.info(f"   • Manufacturing processes: {', '.join(results['cem_training']['manufacturing_processes'])}")
    logger.info(f"   • Materials in database: {', '.join(results['cem_training']['materials'])}")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run training pipeline
    results = asyncio.run(train_systems())
    
    print("\n" + "=" * 70)
    print("TRAINING PIPELINE SUMMARY")
    print("=" * 70)
    print(json.dumps(results, indent=2))
