# PowerShell script to start both bots on Windows
# Usage: .\start_all.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 🗞️  FAP News - Starting All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if config exists
if (-not (Test-Path "config.json")) {
    Write-Host "❌ config.json not found!" -ForegroundColor Red
    Write-Host "   Please run: python setup.py" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Green
    & ".venv\Scripts\Activate.ps1"
}

Write-Host ""
Write-Host "🚀 Starting Main Bot..." -ForegroundColor Green
$botJob = Start-Job -ScriptBlock { python bot.py }

Start-Sleep -Seconds 2

Write-Host "🚀 Starting Admin Bot..." -ForegroundColor Green
$adminJob = Start-Job -ScriptBlock { python admin_bot.py }

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host "📊 Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        # Show output from both jobs
        Receive-Job -Job $botJob
        Receive-Job -Job $adminJob
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host ""
    Write-Host "⚠️  Shutting down all services..." -ForegroundColor Yellow
    Stop-Job -Job $botJob
    Stop-Job -Job $adminJob
    Remove-Job -Job $botJob
    Remove-Job -Job $adminJob
    Write-Host "✅ All services stopped" -ForegroundColor Green
}