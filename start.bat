@echo off
echo ========================================
echo    Payroll System - Starting Up...
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    .venv\Scripts\pip install -r requirements.txt
)

REM Start the backend server
echo Starting backend server...
start "Payroll Backend" cmd /k "cd backend && ..\\.venv\\Scripts\\python.exe app.py"

REM Wait a moment for server to start
timeout /t 3 /nobreak > nul

REM Open the frontend in default browser
echo Opening application in browser...
start "" "frontend\index.html"

echo.
echo ========================================
echo    Application is running!
echo    Close the backend window to stop.
echo ========================================
pause
