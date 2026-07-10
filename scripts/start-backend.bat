@echo off
echo ========================================
echo     NEXUS - Backend FastAPI
echo ========================================
echo.

cd /d "%~dp0.."

REM Activer l'environnement virtuel
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

echo.
echo Demarrage sur http://localhost:8000
echo Documentation: http://localhost:8000/docs
echo.

cd backend
python -m uvicorn app.main:app --reload --port 8000
