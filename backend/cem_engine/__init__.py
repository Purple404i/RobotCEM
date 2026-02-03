"""
CEM Engine Module - Core design generation and optimization

Includes:
- CEMEngine: Core design generation engine
- DesignSpecification: Design specification models
- LLM Engine: Large language model integration
- Code Generator: C# code generation
- Material Database: Material properties and pricing
- Design Rules: Manufacturability rules
- Physics Validator: Physics simulation validation
"""

# Import core modules to make them available at package level
try:
    from .core import CEMEngine, DesignSpecification
    from .llm_engine import get_llm_engine
    from .code_generator import CSharpCodeGenerator
    from .material_db import MaterialDatabase
    from .design_rules import DesignRules
    from .physics_validator import PhysicsValidator
    from .orchestrator import DesignOrchestrator
except ImportError as e:
    # Allow partial imports during module discovery
    import warnings
    warnings.warn(f"Could not import all CEM engine modules: {e}", ImportWarning)

__all__ = [
    "CEMEngine",
    "DesignSpecification",
    "get_llm_engine",
    "CSharpCodeGenerator",
    "MaterialDatabase",
    "DesignRules",
    "PhysicsValidator",
    "DesignOrchestrator",
]
