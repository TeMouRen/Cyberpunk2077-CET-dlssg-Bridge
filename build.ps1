[CmdletBinding()]
param(
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputDir = Join-Path $projectRoot 'input'
$distDir = Join-Path $projectRoot 'dist'
$toolsDir = Join-Path $projectRoot 'tools'

$outerInput = Join-Path $inputDir 'cet-ual-version.dll'
$innerInput = Join-Path $inputDir 'dlssg-sm86-version.dll'
$iniInput = Join-Path $inputDir 'dlssg_sm86.ini'
$outerOutput = Join-Path $distDir 'version.dll'
$innerOutput = Join-Path $distDir 'versionHooked.dll'
$iniOutput = Join-Path $distDir 'dlssg_sm86.ini'

foreach ($requiredFile in @($outerInput, $innerInput, $iniInput)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Missing input: $requiredFile"
    }
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw 'Python launcher (py.exe) was not found.'
}

$stagingDir = Join-Path ([System.IO.Path]::GetTempPath()) ("cp2077-cet-dlssg-bridge-" + [guid]::NewGuid().ToString('N'))
$stagedOuter = Join-Path $stagingDir 'version.dll'
$stagedInner = Join-Path $stagingDir 'versionHooked.dll'
$stagedIni = Join-Path $stagingDir 'dlssg_sm86.ini'

try {
    New-Item -ItemType Directory -Path $stagingDir | Out-Null
    Copy-Item -LiteralPath $innerInput -Destination $stagedInner
    Copy-Item -LiteralPath $iniInput -Destination $stagedIni

    & py -3.12 (Join-Path $toolsDir 'patch_ual_exports.py') `
        --outer $outerInput `
        --inner $stagedInner `
        --output $stagedOuter
    if ($LASTEXITCODE -ne 0) {
        throw "Export patching failed with exit code $LASTEXITCODE"
    }

    if (-not $SkipSmokeTest) {
        Write-Warning 'The smoke test loads and executes the supplied DLLs. Use trusted inputs only.'
        Copy-Item -LiteralPath (Join-Path $toolsDir 'merge-test-global.ini') -Destination (Join-Path $stagingDir 'global.ini')
        Copy-Item -LiteralPath (Join-Path $env:SystemRoot 'System32\version.dll') -Destination (Join-Path $stagingDir 'nvngx_dlssg.dll')

        & py -3.12 (Join-Path $toolsDir 'test_merge_loader.py') $stagingDir
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke test failed with exit code $LASTEXITCODE"
        }
    }

    New-Item -ItemType Directory -Path $distDir -Force | Out-Null
    Copy-Item -LiteralPath $stagedOuter -Destination $outerOutput -Force
    Copy-Item -LiteralPath $stagedInner -Destination $innerOutput -Force
    Copy-Item -LiteralPath $stagedIni -Destination $iniOutput -Force
}
finally {
    if (Test-Path -LiteralPath $stagingDir) {
        Remove-Item -LiteralPath $stagingDir -Recurse -Force
    }
}

Write-Host "Build complete: $distDir"
Get-FileHash -LiteralPath $outerOutput, $innerOutput, $iniOutput -Algorithm SHA256 |
    Select-Object Path, Hash |
    Format-Table -AutoSize
