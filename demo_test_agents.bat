@echo off
echo =========================================
echo CoFound.ai Agent Communication Tests
echo =========================================
echo.

echo Step 1: Fix null bytes in Python files (if any)
python fix_null_bytes.py
echo.

echo Step 2: Testing basic agent communication...
python test_agent_communication.py
if %ERRORLEVEL% NEQ 0 (
    echo Agent communication test failed!
    pause
    exit /b 1
)
echo.

echo Step 3: Testing agentic graph workflow...
python test_agentic_graph.py
if %ERRORLEVEL% NEQ 0 (
    echo Agentic graph test failed!
    pause
    exit /b 1
)
echo.

echo Step 4: Running CoFound.ai CLI Demo... (without LLM integration)
python demo_cofoundai_cli.py --test --request "Create a simple calculator application"
if %ERRORLEVEL% NEQ 0 (
    echo CLI demo test failed!
    pause
    exit /b 1
)
echo.

echo All tests completed successfully!
echo =========================================
echo CoFound.ai tests completed.
echo =========================================
pause 