import pytest
import asyncio
from cem_engine.core import CEMEngine, DesignSpecification

@pytest.fixture
def cem_engine():
    config = {
        'anthropic_api_key': 'test-key',
        'csharp_project_path': '../csharp_runtime/RobotCEM',
        'output_dir': './test_outputs'
    }
    return CEMEngine('test-key', config)

@pytest.mark.asyncio
async def test_prompt_parsing(cem_engine):
    prompt = "Build a robot arm with 200mm reach, using MG996R servos"
    spec = await cem_engine.parse_prompt(prompt)
    
    assert spec.device_type == 'robot_arm'
    assert spec.dimensions.get('reach_mm') == 200
    assert any('MG996R' in str(c) for c in spec.components)

def test_structural_validation(cem_engine):
    spec = DesignSpecification(
        device_type='robot_arm',
        dimensions={'length': 300, 'reach': 300},
        loads={'payload_kg': 2.0},
        motion_constraints={},
        material_preferences=['PLA'],
        manufacturing_method='FDM',
        components=[],
        environmental_conditions={},
        safety_factor=2.0,
        tolerance=0.1,
        finish_requirements='as_printed'
    )
    
    validation = cem_engine.validate_design(spec)
    assert isinstance(validation.errors, list)
    assert isinstance(validation.warnings, list)

def test_material_selection(cem_engine):
    spec = DesignSpecification(
        device_type='robot_arm',
        dimensions={'length': 200},
        loads={'payload_kg': 1.0},
        motion_constraints={},
        material_preferences=[],
        manufacturing_method='FDM',
        components=[],
        environmental_conditions={'temp_max': 80},
        safety_factor=2.0,
        tolerance=0.1,
        finish_requirements='as_printed'
    )
    
    material = cem_engine._select_optimal_material(spec)
    assert material is not None
    assert material in cem_engine.material_database

# Run tests:
# pytest backend/tests/ -v
