# --- CONFIG ---
$FlakeLibrary    = "X:\Brandon\02_Areas\materials-exfoliation"
$FlakeScript     = "X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py"
$FlakeSyncScript = "X:\Brandon\02_Areas\fabrication\tools\flake_sync.py"

# --- Helper: get latest batch folder ---
function Get-LatestBatch {
    Get-ChildItem -Path $FlakeLibrary -Directory |
        Sort-Object Name -Descending |
        Select-Object -First 1 -ExpandProperty Name
}

# --- Tab completion (shared between both commands) ---
$FlakeBatchCompleter = {
    param($commandName, $parameterName, $wordToComplete)
    Get-ChildItem -Path $FlakeLibrary -Directory |
        Where-Object { $_.Name -like "$wordToComplete*" } |
        ForEach-Object {
            [System.Management.Automation.CompletionResult]::new(
                $_.Name, $_.Name, 'ParameterValue', $_.Name
            )
        }
}

# --- Commands ---
function flake-index {
    param([string]$BatchFolder)
    if (-not $BatchFolder) {
        $BatchFolder = Get-LatestBatch
        Write-Host "No batch specified. Using latest: $BatchFolder"
    }
    $fullPath = Join-Path $FlakeLibrary $BatchFolder
    if (-not (Test-Path $fullPath)) {
        Write-Error "Batch folder not found: $fullPath"
        return
    }
    python "$FlakeScript" "$fullPath"
}

function flake-sync {
    param([string]$BatchFolder)
    if (-not $BatchFolder) {
        $BatchFolder = Get-LatestBatch
        Write-Host "No batch specified. Using latest: $BatchFolder"
    }
    $fullPath = Join-Path $FlakeLibrary $BatchFolder
    if (-not (Test-Path $fullPath)) {
        Write-Error "Batch folder not found: $fullPath"
        return
    }
    python "$FlakeSyncScript" "$fullPath"
}

Register-ArgumentCompleter -CommandName flake-index -ParameterName BatchFolder -ScriptBlock $FlakeBatchCompleter
Register-ArgumentCompleter -CommandName flake-sync  -ParameterName BatchFolder -ScriptBlock $FlakeBatchCompleter