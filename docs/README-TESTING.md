# CoFound.ai Testing Framework

This document explains how to test the CoFound.ai multi-agent system without requiring an LLM connection.

## Overview

CoFound.ai includes a testing framework that allows you to verify the system's architecture, agent communication, and workflow functionality without making actual LLM API calls. This makes development and testing more efficient.

## Test Files

1. **test_agent_communication.py** - Tests basic agent communication infrastructure
2. **test_agentic_graph.py** - Tests the LangGraph workflow structure
3. **demo_test_agents.bat** - Batch file that runs all tests together

## How to Run Tests

### Option 1: Run individual tests

```bash
# Test agent communication
python test_agent_communication.py

# Test agentic graph
python test_agentic_graph.py
```

### Option 2: Run all tests with the batch file

```bash
# On Windows
.\demo_english.bat
```

## Test Mode

All agent classes now support a `test_mode` parameter in their constructor. When in test mode, the agents use predefined responses instead of calling an LLM.

Example:
```python
planner = PlannerAgent(config=config, test_mode=True)
```

## Demo CLI in Test Mode

You can run the demo CLI in test mode with:

```bash
python demo_cofoundai_cli.py --test --request "Your request here"
```

## Extending Tests

To create new tests:

1. Create test script files in the root directory
2. Use the `test_mode=True` parameter when initializing agents
3. Add appropriate assertions and error handling

## Future Enhancements

The testing framework could be enhanced with:

1. Unit tests for individual agent functionality
2. Integration tests for complex workflows
3. Automated test suite with CI/CD integration
4. Performance benchmarks for multi-agent interactions

## Notes

- Test mode is only for development and testing. For production, you need to connect to actual LLMs.
- The `fix_null_bytes.py` script helps clean up files with encoding issues.
- The `HIGHLEVEL-CHANGELOG.txt` file tracks all changes to the project, including test-related updates. 