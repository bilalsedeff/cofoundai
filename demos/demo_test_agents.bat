@echo off
echo =========================================
echo CoFound.ai Agent Communication Tests
echo =========================================
echo.

REM Get the absolute path of the repository root
set REPO_ROOT=%~dp0..
echo Repository root: %REPO_ROOT%

REM Set up Python path
set PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%
echo PYTHONPATH set to: %PYTHONPATH%

REM Check if virtual environment exists
if not exist "%REPO_ROOT%\clean_venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found at %REPO_ROOT%\clean_venv
    echo Please ensure the clean_venv directory exists and contains proper activation scripts.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "%REPO_ROOT%\clean_venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)
echo Virtual environment activated successfully.

REM Step 1: Fix null bytes in Python files
echo Step 1: Fix null bytes in Python files (if any)
if not exist "%REPO_ROOT%\scripts\fix_null_bytes.py" (
    echo Warning: fix_null_bytes.py script not found at %REPO_ROOT%\scripts\fix_null_bytes.py
    echo Skipping this step...
) else (
    python "%REPO_ROOT%\scripts\fix_null_bytes.py"
)
echo.

REM Step 2: Testing basic agent communication
echo Step 2: Testing basic agent communication...
if not exist "%REPO_ROOT%\cofoundai\tests\integration\test_agent_communication.py" (
    echo Error: test_agent_communication.py not found at %REPO_ROOT%\cofoundai\tests\integration\test_agent_communication.py
    pause
    exit /b 1
)
python "%REPO_ROOT%\cofoundai\tests\integration\test_agent_communication.py"
if %ERRORLEVEL% NEQ 0 (
    echo Agent communication test failed!
    pause
    exit /b 1
)
echo Agent communication test completed successfully.
echo.

REM Step 3: Testing agentic graph workflow
echo Step 3: Testing agentic graph workflow...
if not exist "%REPO_ROOT%\cofoundai\tests\unit\test_agentic_graph.py" (
    echo Error: test_agentic_graph.py not found at %REPO_ROOT%\cofoundai\tests\unit\test_agentic_graph.py
    pause
    exit /b 1
)
python "%REPO_ROOT%\cofoundai\tests\unit\test_agentic_graph.py"
if %ERRORLEVEL% NEQ 0 (
    echo Agentic graph test failed!
    pause
    exit /b 1
)
echo Agentic graph test completed successfully.
echo.

REM Step 4: Running CoFound.ai CLI Demo
echo Step 4: Running CoFound.ai CLI Demo... (without LLM integration)
if not exist "%REPO_ROOT%\demos\demo_cofoundai_cli.py" (
    echo Error: demo_cofoundai_cli.py not found at %REPO_ROOT%\demos\demo_cofoundai_cli.py
    pause
    exit /b 1
)
python "%REPO_ROOT%\demos\demo_cofoundai_cli.py" --test --request "Create a simple calculator application"
if %ERRORLEVEL% NEQ 0 (
    echo CLI demo test failed!
    pause
    exit /b 1
)
echo CLI demo completed successfully.
echo.

echo All tests completed successfully!
echo =========================================
echo CoFound.ai tests completed.
echo =========================================
pause 