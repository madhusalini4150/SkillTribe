@echo off
echo Starting SkillTribe...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo SkillTribe is running at http://localhost:5000
echo Demo login: demo@demo.com / demo1234
echo.
python app.py
pause
