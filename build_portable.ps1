$ErrorActionPreference = "Stop"

$AppName = "ChatGPT Batch Translator"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistApp = Join-Path $Root "dist\$AppName"

Set-Location $Root

$PythonExe = $null
$PythonPrefix = @()

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
    throw "Python was not found. Install Python 3 first, then run this script again."
}

function Invoke-Python {
    & $PythonExe @PythonPrefix @args
}

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
