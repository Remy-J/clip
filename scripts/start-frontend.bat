@echo off
echo ========================================
echo     NEXUS - Frontend React
echo ========================================
echo.

cd /d "%~dp0..\frontend"

REM Installer les dependances si necessaire
if not exist "node_modules" (
    echo Installation des dependances...
    npm install
)

echo.
echo Demarrage sur http://localhost:5173
echo.

npm run dev
