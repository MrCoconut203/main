# Quick routing test - verify POST /predict/ is registered correctly
# This script will build and run the container briefly to test routes

Write-Host "Building Docker image..." -ForegroundColor Cyan
docker build -t ai-detection:route-test -f Dockerfile . 2>&1 | Select-Object -Last 10

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nStarting container..." -ForegroundColor Cyan
$containerId = docker run -d -e PORT=8000 -p 8765:8000 ai-detection:route-test

Start-Sleep -Seconds 5  # Wait for startup

Write-Host "`nTesting routes..." -ForegroundColor Cyan

Write-Host "`n1. GET /health"
curl.exe -s http://localhost:8765/health

Write-Host "`n`n2. OPTIONS /predict/ (CORS preflight)"
curl.exe -s -X OPTIONS http://localhost:8765/predict/ -i | Select-String "HTTP|Allow"

Write-Host "`n3. GET /predict/ (should return helpful message)"
curl.exe -s http://localhost:8765/predict/

Write-Host "`n`n4. POST /predict/ without file (should be 422, NOT 405!)"
$response = curl.exe -s -X POST http://localhost:8765/predict/ -i
if ($response -match "405") {
    Write-Host "❌ FAILED: Got 405 Method Not Allowed - routing broken!" -ForegroundColor Red
} elseif ($response -match "422") {
    Write-Host "✅ PASSED: Got 422 Unprocessable Entity (missing file) - routing correct!" -ForegroundColor Green
} else {
    Write-Host "Status line: $($response | Select-String 'HTTP')" -ForegroundColor Yellow
}

Write-Host "`n5. POST /predict/ with dummy file (should NOT be 405)"
$tempFile = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllBytes($tempFile, @(0xFF, 0xD8, 0xFF, 0xD9))  # minimal JPEG
$response = curl.exe -s -X POST http://localhost:8765/predict/ -F "file=@$tempFile" -i
Remove-Item $tempFile -Force
if ($response -match "405") {
    Write-Host "❌ FAILED: Got 405 - POST handler not working!" -ForegroundColor Red
} else {
    $status = $response | Select-String 'HTTP/\d\.\d (\d+)' | ForEach-Object { $_.Matches.Groups[1].Value }
    Write-Host "✅ PASSED: Got status $status (not 405) - routing works!" -ForegroundColor Green
}

Write-Host "`nCleaning up..."
docker stop $containerId | Out-Null
docker rm $containerId | Out-Null

Write-Host "`nDone! If all tests passed, you can deploy safely." -ForegroundColor Cyan
