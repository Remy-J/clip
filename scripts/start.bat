@echo off
echo ========================================
echo         NEXUS - Demarrage
echo ========================================
echo.

REM Verifier si on est dans le bon repertoire
if not exist "backend\app\main.py" (
    echo Erreur: Executez ce script depuis la racine du projet Nexus
    pause
    exit /b 1
)

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur: Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

REM Verifier FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo Attention: FFmpeg n'est pas installe
    echo Telechargez-le depuis https://ffmpeg.org/download.html
)

REM Creer l'environnement virtuel si necessaire
if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Installer les dependances
echo Installation des dependances...
pip install -r requirements.txt -q

REM Copier .env si necessaire
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo Fichier .env cree. Configurez vos credentials Twitch!
    )
)

REM Lancer le serveur
echo.
echo ========================================
echo Demarrage du serveur sur http://localhost:8000
echo Documentation API: http://localhost:8000/docs
echo ========================================
echo.

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
