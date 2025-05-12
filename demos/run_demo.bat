@echo off
echo Running CoFound.ai CLI Demo...
set REPO_ROOT=%~dp0..
set PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%

REM Activate virtual environment
call %REPO_ROOT%\clean_venv\Scripts\activate

python %REPO_ROOT%\demos\demo_cofoundai_cli.py %*
pause 