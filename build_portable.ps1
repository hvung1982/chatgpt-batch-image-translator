$ErrorActionPreference = "Stop"

$AppName = "ChatGPT Batch Translator"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistApp = Join-Path $Root "dist\$AppName"

Set-Location $Root

$PythonExe = $null
$PythonPrefix = @()

function Test-PythonExe {
    param([string]$Path)

    if (-not $Path) {
        return $false
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    & $Path -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" *> $null
    return ($LASTEXITCODE -eq 0)
}

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($PythonCommand) {
    $PythonExe = $PythonCommand.Source
} else {
    $PyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($PyCommand) {
        $PythonExe = $PyCommand.Source
        $PythonPrefix = @("-3")
    }
}

if (-not $PythonExe) {
    $registryRoots = @(
        "Registry::HKEY_CURRENT_USER\Software\Python\PythonCore",
        "Registry::HKEY_LOCAL_MACHINE\Software\Python\PythonCore",
        "Registry::HKEY_LOCAL_MACHINE\Software\WOW6432Node\Python\PythonCore"
    )

    foreach ($registryRoot in $registryRoots) {
        if ($PythonExe) {
            break
        }
        if (-not (Test-Path $registryRoot)) {
            continue
        }

        $versions = Get-ChildItem $registryRoot -ErrorAction SilentlyContinue |
            Sort-Object PSChildName -Descending

        foreach ($version in $versions) {
            $installPathKey = Join-Path $version.PSPath "InstallPath"
            try {
                $installPath = (Get-ItemProperty -Path $installPathKey -ErrorAction Stop)."(default)"
                $candidate = Join-Path $installPath "python.exe"
                if (Test-PythonExe $candidate) {
                    $PythonExe = $candidate
                    break
                }
            } catch {
                continue
            }
        }
    }
}

if (-not $PythonExe) {
    $candidateRoots = @(
        "$env:LOCALAPPDATA\Programs\Python",
        "$env:ProgramFiles\Python*",
        "${env:ProgramFiles(x86)}\Python*"
    )

    foreach ($candidateRoot in $candidateRoots) {
        if ($PythonExe) {
            break
        }

        Get-ChildItem -Path $candidateRoot -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            ForEach-Object {
                if (-not $PythonExe -and (Test-PythonExe $_.FullName)) {
                    $script:PythonExe = $_.FullName
                }
            }
    }
}

if (-not $PythonExe) {
    throw "Python 3.9+ was not found. If Python is installed, enable 'Add python.exe to PATH' or install the official Python from python.org."
}

function Invoke-Python {
    & $PythonExe @PythonPrefix @args
}

Write-Host "==> Using Python:"
Write-Host $PythonExe

$PythonRoot = Split-Path -Parent $PythonExe
$TclLibrary = Join-Path $PythonRoot "tcl\tcl8.6"
$TkLibrary = Join-Path $PythonRoot "tcl\tk8.6"
if ((Test-Path $TclLibrary) -and (Test-Path $TkLibrary)) {
    $env:TCL_LIBRARY = $TclLibrary
    $env:TK_LIBRARY = $TkLibrary
}

Write-Host "==> Checking Tkinter support..."
Invoke-Python -c "import tkinter; tkinter.Tcl().eval('info patchlevel')"
if ($LASTEXITCODE -ne 0) {
    throw "This Python installation does not include Tkinter. Install the official Python from python.org and enable Tcl/Tk, then run this script again."
}

Write-Host "==> Installing Python dependencies..."
Invoke-Python -m pip install --upgrade pip
Invoke-Python -m pip install -r requirements.txt

Write-Host "==> Cleaning old build output..."
if (Test-Path (Join-Path $Root "build")) {
    Remove-Item -LiteralPath (Join-Path $Root "build") -Recurse -Force
}
if (Test-Path $DistApp) {
    Remove-Item -LiteralPath $DistApp -Recurse -Force
}

Write-Host "==> Building portable app..."
Invoke-Python -m PyInstaller `
    --noconfirm `
    --onedir `
    --windowed `
    --name "$AppName" `
    --collect-all playwright `
    --hidden-import run_chatgpt_batch `
    --hidden-import pygetwindow `
    --hidden-import win32process `
    app.pyw

Write-Host "==> Installing Playwright Chromium into portable folder..."
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $DistApp "ms-playwright"
Invoke-Python -m playwright install chromium

Write-Host "==> Creating default user folders..."
New-Item -ItemType Directory -Force -Path (Join-Path $DistApp "images") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DistApp "images_vn") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DistApp "chatgpt_auto_profile") | Out-Null

Write-Host ""
Write-Host "DONE."
Write-Host "Portable app folder:"
Write-Host $DistApp
Write-Host ""
Write-Host "Send this whole folder to users. They should run:"
Write-Host "$AppName.exe"
