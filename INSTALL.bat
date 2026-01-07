@echo off
setlocal EnableExtensions EnableDelayedExpansion
title FolderMonitorAdrian - Install (Startup Shortcut)

set "APP_NAME=FolderMonitorAdrian"
set "EXE=%~dp0FolderMonitorAdrian.exe"
set "TASK=%APP_NAME%"
set "USER_START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\%APP_NAME%.lnk"
set "ALL_START=%ProgramData%\Microsoft\Windows\Start Menu\Programs\StartUp\%APP_NAME%.lnk"

echo ========= %APP_NAME% Install (Startup Shortcut) =========

:: 0) Basic check
if not exist "%EXE%" (
  echo ERROR: "%EXE%" not found. Place this .bat next to %APP_NAME%.exe
  pause & exit /b 1
)

:: 1) Stop any running process
echo Stopping running process (if any)...
taskkill /IM "%APP_NAME%.exe" /F >nul 2>&1

:: 2) Clean previous auto-start hooks (task, run keys, old shortcuts)
echo Cleaning previous auto-start hooks...
schtasks /Delete /TN "%TASK%" /F >nul 2>&1
schtasks /Delete /TN "%TASK% (User)" /F >nul 2>&1
schtasks /Delete /TN "%TASK% (All Users)" /F >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "%APP_NAME%" /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "%APP_NAME%" /f >nul 2>&1
if exist "%USER_START%" del /F /Q "%USER_START%" >nul 2>&1
if exist "%ALL_START%"  del /F /Q "%ALL_START%"  >nul 2>&1

:: 3) Prepare local app data folder
echo Preparing local app data folder...
mkdir "%LOCALAPPDATA%\%APP_NAME%" >nul 2>&1

:: 4) Fix config.json formatting (remove BOM, normalize slashes)
if exist "%~dp0config.json" (
  echo Checking config.json path formatting...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$p='%~dp0config.json';" ^
    "$j=Get-Content $p -Raw;" ^
    "$j=$j -replace '\\\\','/';" ^
    "$j=$j -replace '/+','/';" ^
    "[IO.File]::WriteAllText($p,$j,[Text.UTF8Encoding]::new($false));"
)

:: 4b) Create watch/backup folders if defined
echo Creating watch/backup folders (if defined)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $c=Get-Content '%~dp0config.json' -Raw | ConvertFrom-Json; " ^
  "$paths=@($c.watch_folder,$c.backup_folder) | Where-Object { $_ -and $_.Trim() -ne '' }; " ^
  "foreach($d in $paths){ $n=[System.IO.Path]::GetFullPath($d); New-Item -ItemType Directory -Force -Path $n | Out-Null } } catch {}"

:: 5) Create per-user Startup shortcut (keeps correct Working Directory)
echo Creating Startup shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$WScript = New-Object -ComObject WScript.Shell;" ^
  "$lnk = $WScript.CreateShortcut('%USER_START%');" ^
  "$lnk.TargetPath = '%EXE%';" ^
  "$lnk.WorkingDirectory = '%~dp0';" ^
  "$lnk.IconLocation = '%EXE%,0';" ^
  "$lnk.Save();"

:: 6) Launch now for confirmation
echo Starting %APP_NAME% now...
start "" "%EXE%"

echo.
echo Install complete. The app will auto-start for this user via Startup shortcut.
pause
endlocal
