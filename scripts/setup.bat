@echo off
echo ========================================
echo      NEXUS - Installation Complete
echo ========================================
echo.

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe
    echo Telechargez Python 3.11+ depuis https://python.org
    pause
    exit /b 1
) else (
    echo [OK] Python installe
)

REM Verifier FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [MANQUANT] FFmpeg
    echo.
    echo Pour installer FFmpeg:
    echo 1. Telechargez depuis https://www.gyan.dev/ffmpeg/builds/
    echo 2. Extrayez dans C:\ffmpeg
    echo 3. Ajoutez C:\ffmpeg\bin au PATH systeme
    echo.
) else (
    echo [OK] FFmpeg installe
)

REM Verifier yt-dlp
yt-dlp --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] yt-dlp sera installe avec pip
) else (
    echo [OK] yt-dlp installe
)

REM Creer l'environnement virtuel
echo.
echo Creation de l'environnement virtuel...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat

REM Installer les dependances
echo.
echo Installation des dependances Python...
pip install -r requirements.txt

REM Creer le fichier .env
if not exist ".env" (
    copy .env.example .env
    echo.
    echo [ACTION REQUISE] Fichier .env cree
    echo Editez .env pour ajouter vos credentials Twitch
)

REM Verifier Ollama
echo.
echo Verification d'Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [MANQUANT] Ollama
    echo.
    echo Pour installer Ollama:
    echo 1. Telechargez depuis https://ollama.ai/download
    echo 2. Installez et lancez l'application
    echo 3. Executez: ollama pull llama3.1:8b
    echo.
) else (
    echo [OK] Ollama installe
    echo.
    echo Telechargement du modele Llama 3.1...
    ollama pull llama3.1:8b
)

echo.
echo ========================================
echo          Installation terminee!
echo ========================================
echo.
echo Prochaines etapes:
echo 1. Configurez vos credentials Twitch dans .env
echo 2. Lancez: scripts\start.bat
echo 3. Ouvrez http://localhost:8000/docs
echo.
pause
