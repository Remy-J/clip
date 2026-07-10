@echo off
echo ========================================
echo     NEXUS - Demarrage Complet
echo ========================================
echo.

REM Verifier si on est dans le bon repertoire
if not exist "backend\app\main.py" (
    cd ..
    if not exist "backend\app\main.py" (
        echo Erreur: Executez ce script depuis le projet Nexus
        pause
        exit /b 1
    )
)

REM Creer l'environnement virtuel Python si necessaire
if not exist "venv" (
    echo Creation de l'environnement virtuel Python...
    python -m venv venv
)

REM Activer l'environnement Python
call venv\Scripts\activate.bat

REM Installer les dependances Python si necessaire
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances Python...
    pip install -r requirements.txt -q
)

REM Installer les dependances Node si necessaire
if not exist "frontend\node_modules" (
    echo Installation des dependances Node.js...
    cd frontend
    npm install
    cd ..
)

REM Copier .env si necessaire
if not exist ".env" (
    copy .env.example .env
    echo.
    echo [!] Fichier .env cree - Configurez vos credentials Twitch!
    echo.
)

echo ========================================
echo Demarrage des serveurs...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Appuyez sur Ctrl+C pour arreter
echo ========================================
echo.

REM Lancer le backend en arriere-plan
start "Nexus Backend" cmd /c "cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

REM Attendre un peu que le backend demarre
timeout /t 3 /nobreak >nul

REM Lancer le frontend
cd frontend
npm run dev
