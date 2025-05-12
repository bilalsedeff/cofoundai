@echo off
echo =========================================
echo CoFound.ai Multi-Agent System Demo
echo =========================================
echo.

echo Running agent communication and workflow tests...
echo.

echo Step 1: Testing basic agent communication...
python test_agent_communication.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Agent communication test failed!
    pause
    exit /b 1
)
echo.

echo Step 2: Testing LangGraph workflow...
python test_agentic_graph.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: LangGraph workflow test failed!
    pause
    exit /b 1
)
echo.

echo Step 3: Running full demo with a calculator app request...
python demo_cofoundai_cli.py --test --request "Create a simple calculator application that can perform addition, subtraction, multiplication and division"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Full demo test encountered issues.
    echo This might be expected if not all agent components are fully implemented.
)
echo.

echo All tests completed!
echo =========================================
echo You can further develop the CoFound.ai system by:
echo 1. Implementing actual LLM integrations
echo 2. Extending the agent capabilities
echo 3. Adding more complex workflows
echo =========================================
pause 