@echo off
echo =========================================
echo CoFound.ai Agent Communication Tests
echo =========================================
echo.

set REPO_ROOT=%~dp0..
set PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%

REM Activate virtual environment
call %REPO_ROOT%\clean_venv\Scripts\activate

echo Step 1: Fix null bytes in Python files (if any)
python %REPO_ROOT%\scripts\fix_null_bytes.py
echo.

echo Step 2: Testing basic agent communication...
python %REPO_ROOT%\cofoundai\tests\integration\test_agent_communication.py
if %ERRORLEVEL% NEQ 0 (
    echo Agent communication test failed!
    pause
    exit /b 1
)
echo.

echo Step 3: Testing agentic graph workflow...
python %REPO_ROOT%\cofoundai\tests\unit\test_agentic_graph.py
if %ERRORLEVEL% NEQ 0 (
    echo Agentic graph test failed!
    pause
    exit /b 1
)
echo.

echo Step 4: Running CoFound.ai CLI Demo... (without LLM integration)
python %REPO_ROOT%\demos\demo_cofoundai_cli.py --test --request "Create a simple calculator application"
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