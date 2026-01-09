# Stop server on port 8000
Write-Host "Stopping server on port 8000..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connections) {
    $processes = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $processes) {
        Write-Host "Stopping process ID: $procId" -ForegroundColor Red
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "`n✅ Server stopped. You can now run: python main.py`n" -ForegroundColor Green
} else {
    Write-Host "No process found on port 8000.`n" -ForegroundColor Green
}
