$ErrorActionPreference = 'Stop'

Write-Host 'Checking Node.js and npm...' -ForegroundColor Cyan
$nodeVersion = node -v
$npmVersion = npm -v
Write-Host "Node: $nodeVersion"
Write-Host "npm : $npmVersion"

Write-Host 'Installing dependencies...' -ForegroundColor Cyan
npm install

Write-Host 'Adding Android platform (first time only)...' -ForegroundColor Cyan
npx cap add android

Write-Host 'Syncing Capacitor...' -ForegroundColor Cyan
npx cap sync android

Write-Host 'Opening Android Studio project...' -ForegroundColor Cyan
npx cap open android

Write-Host 'Done. Build signed AAB from Android Studio for Play Store.' -ForegroundColor Green
