# Training System Fine-Tuning Guide

## Overview

This guide covers Steps 3 & 4 from the integration requirements:
- **Step 3**: Test with example prompts (via test_training_integration.py)
- **Step 4**: Fine-tune based on results

## Step 3: Test with Example Prompts

### Running Integration Tests

```bash
# From project root
cd /home/devlord/RobotCEM

# Activate virtualenv (if not already active)
source backend/dw_env/bin/activate

# Run integration tests
python3 backend/tests/test_training_integration.py
```

### What Tests Check

**TEST 1: Adapter Integration**
- ✓ LLMDomainAdapter loaded in PromptParser
- ✓ Knowledge base contains training categories
- ✓ Training data ready to enhance prompts

**TEST 2: CEM Rules Integration**
- ✓ CEMTrainer loaded in Orchestrator
- ✓ Design rules loaded (gripper, arm, bearing)
- ✓ Manufacturing rules loaded (FDM, SLA, SLS, CNC)
- ✓ Material database loaded (PLA, ABS, PETG, Al6061, Steel)

**TEST 3: Prompt Parsing**
- ✓ Extracts device type from natural language
- ✓ Identifies optimization goals
- ✓ Calculates specificity score
- Tests 4 diverse prompts covering different domains

**TEST 4: CEM Rule Application**
- ✓ Design rules accessible for gripper
- ✓ Manufacturing rules accessible for FDM
- ✓ Material properties accessible for PLA

**TEST 5: End-to-End Workflow**
- ✓ Parse prompt with training context
- ✓ Apply CEM rules to specification
- ✓ Validate manufacturing constraints
- Tests 2 complete workflows (gripper + bracket)

### Expected Output

```
TEST 1: LLMDomainAdapter Integration in PromptParser
✓ PASS: PromptParser loaded with 9 knowledge categories
  Categories: ['BaseShapes', 'LatticeTypes', ...]

TEST 2: CEM Rules Integration in Orchestrator
✓ PASS: Orchestrator loaded CEM rules
  Design domains: ['gripper', 'arm', 'bearing']
  Manufacturing processes: ['FDM', 'SLA', 'SLS', 'CNC']
  Materials: ['PLA', 'ABS', 'PETG', 'Al6061', 'Steel']

TEST 3: Prompt Parsing with Training-Enhanced Context
  Test 3.1: Create a lightweight gripper with 100N grip force
    Detected device: gripper
    Optimization goals: ['lightweight', 'strong']
    Specificity: 0.85
  ✓ PASS: All 4 prompts parsed successfully

TEST 4: CEM Rule Application on Specifications
✓ Found design_rules[gripper]
✓ Found manufacturing_rules[FDM]
✓ Found material_database[PLA]
✓ PASS: 3/3 CEM rules applied successfully

TEST 5: End-to-End Workflow
  Workflow: Lightweight Gripper
    ✓ Parsed specification
    ✓ Found FDM manufacturing rules
      Min wall: 0.8mm
  ✓ PASS: 2/2 end-to-end workflows completed
```

## Step 4: Fine-Tuning Based on Results

### Monitoring & Validation

#### 1. Check Training Data Quality

```bash
# Verify deduplication working
ls -lah backend/training/llm_training_examples.json

# Inspect unique examples
python3 -c "
import json
with open('backend/training/llm_training_examples.json') as f:
    examples = json.load(f)
    print(f'Total examples: {len(examples)}')
    print(f'First example: {examples[0]}')
"
```

#### 2. Monitor Run Training Loop

```bash
# Terminal 1: Watch training logs
tail -f backend/logs/training.log | grep -E "Book|Pass|Saved"

# Terminal 2: Start training loop
python3 backend/training/run_training.py
```

Expected log pattern (every 1 second):
```
2024-01-15 10:23:45 - INFO - Processing book: books/mechanics.txt
2024-01-15 10:23:45 - INFO - Training examples processed
2024-01-15 10:23:45 - INFO - Saved 15 deduplicated examples to llm_training_examples.json
2024-01-15 10:23:46 - INFO - Processing book: books/maths.txt
2024-01-15 10:23:46 - INFO - Training examples processed
```

#### 3. Validate Parser Enhancement

```bash
# Create test script
cat > /tmp/test_parser.py << 'EOF'
import sys
sys.path.insert(0, '/home/devlord/RobotCEM')

from backend.cem_engine.prompt_parser import PromptParser

parser = PromptParser()
prompt = "Create a lightweight gripper with FDM material"

# Parse with training enhancement
spec = parser.parse(prompt)

# Check if training context was applied
if hasattr(parser, 'domain_adapter') and parser.domain_adapter:
    print("✓ Domain adapter active")
    print(f"  Knowledge categories: {len(parser.domain_adapter.knowledge_base)}")
    print(f"  Specification intent: {spec.intent if hasattr(spec, 'intent') else 'N/A'}")
else:
    print("✗ Domain adapter not active")
EOF

python3 /tmp/test_parser.py
```

### Fine-Tuning Actions

#### Scenario 1: Tests Pass ✓

**Status**: Integration fully working
- ✓ LLMDomainAdapter enhancing all prompts
- ✓ CEMTrainer rules loaded and accessible
- ✓ Deduplication preventing file bloat
- ✓ Training loop running continuously

**Actions**:
1. **Enable Production Mode**
   ```bash
   # Set environment for slower pass interval (less CPU)
   export TRAIN_PASS_INTERVAL=5  # 5 seconds instead of 1
   python3 backend/training/run_training.py
   ```

2. **Add More Training Data**
   ```bash
   # Add specialized books to training folder
   cp /path/to/robotics_guide.txt books/
   cp /path/to/manufacturing_specs.txt books/
   # Training will auto-process new files
   ```

3. **Monitor Performance**
   ```bash
   # Check training throughput
   grep "Saved" backend/logs/training.log | wc -l
   # Should show steady growth of unique examples
   ```

4. **Document Success**
   ```bash
   # Create success checkpoint
   echo "Integration test passed - $(date)" >> DEPLOYMENT_READY.md
   ```

#### Scenario 2: Tests Partial Pass ⚠️

**If TEST 1-2 pass but TEST 3-5 fail**:

1. **Check Imports**
   ```python
   # In Python REPL
   from backend.training.llm_trainer import LLMDomainAdapter, CEMTrainer
   from backend.cem_engine.prompt_parser import PromptParser
   
   # Should not raise ImportError
   ```

2. **Verify File Paths**
   ```bash
   ls -la backend/training/llm_training_examples.json
   ls -la backend/cem_engine/design_rules.json
   ```

3. **Check NL Analyzer**
   ```bash
   # PromptParser depends on NL analyzer being loaded
   grep "nl_analyzer" backend/cem_engine/prompt_parser.py
   ```

4. **Debug Parse Method**
   ```python
   # Interactive debug
   from backend.cem_engine.prompt_parser import PromptParser
   
   parser = PromptParser()
   # Check if parse method exists and works
   try:
       result = parser.parse("test prompt")
       print(f"Parse works: {type(result)}")
   except Exception as e:
       print(f"Parse error: {e}")
   ```

**Solution**: 
- Add missing methods to PromptParser if needed
- Ensure nl_analyzer is properly initialized
- Check design rules JSON format

#### Scenario 3: Tests Fail ✗

**If multiple tests fail**:

1. **Rebuild Training System**
   ```bash
   cd /home/devlord/RobotCEM
   
   # Verify training files exist
   ls -la backend/training/{llm_trainer.py,run_training.py}
   
   # Check Python syntax
   python3 -m py_compile backend/training/llm_trainer.py
   python3 -m py_compile backend/cem_engine/orchestrator.py
   ```

2. **Manually Load Components**
   ```python
   # Test minimal case
   import sys
   sys.path.insert(0, '/home/devlord/RobotCEM')
   
   # Step 1
   from backend.training.llm_trainer import LLMDomainAdapter
   adapter = LLMDomainAdapter()
   print(f"Adapter loaded: {len(adapter.knowledge_base)} categories")
   
   # Step 2
   from backend.training.llm_trainer import CEMTrainer
   trainer = CEMTrainer()
   trainer.load_robotics_design_rules()
   rules = trainer.get_cem_training_data()
   print(f"Rules loaded: {list(rules.keys())}")
   ```

3. **Check Orchestrator Initialization**
   ```python
   from backend.cem_engine.orchestrator import EngineOrchestrator
   try:
       orch = EngineOrchestrator()
       print(f"Orchestrator initialized")
       print(f"Has CEM rules: {hasattr(orch, 'cem_rules')}")
   except Exception as e:
       print(f"Orchestrator error: {e}")
       import traceback
       traceback.print_exc()
   ```

### Performance Tuning

#### Training Loop Interval

Default: **1 second** (aggressive learning)

```bash
# Slower interval for production (5 seconds)
export TRAIN_PASS_INTERVAL=5

# Very slow for minimal CPU impact (30 seconds)
export TRAIN_PASS_INTERVAL=30

# Apply in run command
TRAIN_PASS_INTERVAL=5 python3 backend/training/run_training.py
```

#### Deduplication Strategy

Current: Tracks `(prompt, response)` tuples

Check dedup effectiveness:
```python
import json

with open('backend/training/llm_training_examples.json') as f:
    examples = json.load(f)

# Count unique prompts
prompts = set(e.get('prompt', '') for e in examples)
print(f"Total examples: {len(examples)}")
print(f"Unique prompts: {len(prompts)}")
print(f"Dedup ratio: {len(examples) / len(prompts):.2f}x")
# Should be close to 1.0 (near-zero duplicates)
```

#### CEM Rule Priority

Current order in orchestrator initialization:
1. Load robotics design rules (gripper, arm, bearing)
2. Load manufacturing rules (FDM, SLA, SLS, CNC)
3. Load material database (PLA, ABS, PETG, Al6061, Steel)

To adjust priority:
```python
# In orchestrator.py __init__:
# Reorder load sequence if some rules should take precedence
self.cem_trainer.load_material_database()  # Do materials first
self.cem_trainer.load_manufacturing_rules()  # Then manufacturing
self.cem_trainer.load_robotics_design_rules()  # Design rules last
```

### Metrics to Track

Create [METRICS.md](METRICS.md) to track:

```markdown
# Training System Metrics

## Training Data Quality
- **Unique Examples**: COUNT from llm_training_examples.json
- **Dedup Ratio**: Should be ~1.0 (minimal duplicates)
- **Books Processed**: COUNT of files from books/ folder

## Integration Status
- **Adapter Loaded**: ✓ (in PromptParser)
- **CEM Rules Loaded**: ✓ (in Orchestrator)
- **Parse Enhancement**: ✓ (active on all prompts)

## Performance
- **Training Loop Interval**: 1s (configurable)
- **File Update Frequency**: Every ~1s pass
- **Memory Usage**: [Monitor with 'top' while running]

## Test Results
- **TEST 1**: ✓ PASS
- **TEST 2**: ✓ PASS
- **TEST 3**: ✓ PASS (4/4 prompts)
- **TEST 4**: ✓ PASS (3/3 rules)
- **TEST 5**: ✓ PASS (2/2 workflows)
```

## Validation Checklist

- [ ] `backend/tests/test_training_integration.py` created
- [ ] All 5 tests running without errors
- [ ] `llm_training_examples.json` being updated
- [ ] LLMDomainAdapter active in PromptParser
- [ ] CEMTrainer active in Orchestrator
- [ ] `run_training.py` running in background
- [ ] No duplicate examples accumulating
- [ ] CEM rules accessible in orchestration
- [ ] Prompts enhanced with training context

## Next Phase: Advanced Fine-Tuning

Once basic integration verified:

1. **Domain-Specific Prompts**: Add manufacturing-focused test cases
2. **Multi-Step Workflows**: Test complex design sequences
3. **Rule Conflict Resolution**: Handle cases where rules conflict
4. **Custom Material Support**: Extend material database
5. **Geometry Validation**: Verify PicoGK bridge compliance
6. **Performance Profiling**: Track enhancement overhead

## Support

If issues arise:

1. Check logs: `tail -f backend/logs/training.log`
2. Run syntax checks: `python3 -m py_compile backend/**/*.py`
3. Test imports: `python3 -c "from backend.training.llm_trainer import CEMTrainer"`
4. Review integration test output for specific failures
