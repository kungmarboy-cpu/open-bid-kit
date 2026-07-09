# Open Bid Kit Launcher (PowerShell)
# Launches the OpenBidKit_Yibiao Electron app

$AppDir = "C:\Users\KalsungTinzin\Documents\New Project\OpenBidKit_Yibiao\client"

if (-not (Test-Path $AppDir)) {
    Write-Error "OpenBidKit_Yibiao not found at $AppDir"
    Write-Host "Please clone from: https://github.com/FB208/OpenBidKit_Yibiao"
    exit 1
}

Push-Location $AppDir

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..."
    npm install
}

Write-Host "Starting OpenBidKit_Yibiao..."
npm run dev

Pop-Location
