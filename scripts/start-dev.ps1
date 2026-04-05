param(
    [switch]$WithFrontend
)

Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "uvicorn" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $repoRoot ".run"

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

function Start-ServiceProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $stdout = Join-Path $runDir "$Name.out.log"
    $stderr = Join-Path $runDir "$Name.err.log"
    $pidFile = Join-Path $runDir "$Name.pid"

    if (Test-Path $pidFile) {
        $existingPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($existingPid) {
            $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            if ($existingProcess) {
                Write-Host "$Name is already running (PID $existingPid)."
                return
            }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    Set-Content -Path $pidFile -Value $process.Id
    Write-Host "Started $Name (PID $($process.Id))."
}

function Wait-ForUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    for ($attempt = 1; $attempt -le 20; $attempt++) {
        try {
            Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 3 | Out-Null
            Write-Host "$Name is reachable at $Url"
            return
        }
        catch {
            Start-Sleep -Milliseconds 750
        }
    }

    Write-Warning "$Name did not become ready. Check .run logs."
}

Start-ServiceProcess `
    -Name "cad-engine" `
    -FilePath "conda" `
    -ArgumentList @("run", "-n", "base", "python", "cad-engine/python_cad_engine.py") `
    -WorkingDirectory $repoRoot

Start-ServiceProcess `
    -Name "llm-service" `
    -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "7000") `
    -WorkingDirectory (Join-Path $repoRoot "llm-service")

Start-ServiceProcess `
    -Name "backend-mcp" `
    -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000") `
    -WorkingDirectory (Join-Path $repoRoot "backend-mcp")

if ($WithFrontend) {
    $nodeModules = Join-Path $repoRoot "frontend\\node_modules"
    if (Test-Path $nodeModules) {
        Start-ServiceProcess `
            -Name "frontend" `
            -FilePath "npm.cmd" `
            -ArgumentList @("run", "dev", "--", "--host", "0.0.0.0", "--port", "3000") `
            -WorkingDirectory (Join-Path $repoRoot "frontend")
    }
    else {
        Write-Warning "Frontend dependencies are missing. Run 'npm install' in frontend first."
    }
}

Wait-ForUrl -Name "CAD engine" -Url "http://127.0.0.1:5000/health"
Wait-ForUrl -Name "LLM service" -Url "http://127.0.0.1:7000/health"
Wait-ForUrl -Name "MCP server" -Url "http://127.0.0.1:8000/health"

if ($WithFrontend -and (Test-Path (Join-Path $runDir "frontend.pid"))) {
    Write-Host "Frontend should be available at http://127.0.0.1:3000"
}

Write-Host ""
Write-Host "Logs: $runDir"
