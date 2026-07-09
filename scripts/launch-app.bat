@echo off
REM Open Bid Kit Launcher
REM Launches the OpenBidKit_Yibiao Electron app

set APP_DIR=C:\Users\KalsungTinzin\Documents\New Project\OpenBidKit_Yibiao\client

if not exist "%APP_DIR%" (
    echo OpenBidKit_Yibiao not found at %APP_DIR%
    echo Please clone from: https://github.com/FB208/OpenBidKit_Yibiao
    exit /b 1
)

cd /d "%APP_DIR%"

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo Starting OpenBidKit_Yibiao...
call npm run dev
