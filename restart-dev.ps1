$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "address_back"
$FrontendDir = Join-Path $Root "address_web"
$BackendPort = 8000
$FrontendPort = 5173

function Stop-PortProcess {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $connections = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $processId = $connection.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($null -ne $process) {
            Write-Host "Stopping port $Port -> $($process.ProcessName) (PID $processId)"
            Stop-Process -Id $processId -Force
        }
    }
}

function Start-ServiceWindow {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    $script = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
Set-Location '$WorkingDirectory'
$Command
Read-Host 'Process exited. Press Enter to close this window'
"@

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        $script
    )
}

Write-Host "Cleaning old frontend/backend port usage..."
Stop-PortProcess -Port $BackendPort
Stop-PortProcess -Port $FrontendPort

Write-Host "Starting backend on http://127.0.0.1:$BackendPort ..."
Start-ServiceWindow `
    -Title "address_back :$BackendPort" `
    -WorkingDirectory $BackendDir `
    -Command "uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $BackendPort"

Write-Host "Starting frontend on http://127.0.0.1:$FrontendPort ..."
Start-ServiceWindow `
    -Title "address_web :$FrontendPort" `
    -WorkingDirectory $FrontendDir `
    -Command "npm run dev -- --host 0.0.0.0 --port $FrontendPort"

Write-Host ""
Write-Host "Done."
Write-Host "Backend:  http://127.0.0.1:$BackendPort"
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
