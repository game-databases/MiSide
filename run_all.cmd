@echo off
rem MiSide pack - single-entrypoint pipeline driver (native Windows entry).
rem PowerShell invokes this .cmd directly; Git Bash / `ssh ne8k` use ./run_all.
rem Spec: docs\specs\pipeline-run_all.mdx
setlocal
set "PACKROOT=%~dp0"
python "%PACKROOT%pipeline\run_all.py" %*
endlocal & exit /b %ERRORLEVEL%
