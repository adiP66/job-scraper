# Windows PowerShell Execution Script for Application Tracker
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$pythonExe = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonExe = ".\.venv\Scripts\python.exe"
}

if ($args.Count -eq 0) {
    & $pythonExe track_applications.py --list
} else {
    & $pythonExe track_applications.py $args
}
