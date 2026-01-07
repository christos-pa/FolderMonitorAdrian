@echo off
setlocal EnableExtensions EnableDelayedExpansion
title FolderMonitorAdrian - Uninstall

set "APP_NAME=FolderMonitorAdrian"
set "USER_START=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\%APP_NAME%.lnk"
set "ALL_START=%ProgramData%\Microsoft\Windows\Start Menu\Programs\StartUp\%APP_NAME%.lnk"

:: --------- flags (default: keep files, show pause) ----------
set "DO_PURGE_EXE=0"
set "DO_PURGE_CFG=0"
set "DO_SILENT=0"

for %%A in (%*) do (
  if /I "%%~A"=="/purge"      (set DO_PURGE_EXE=1 & set DO_PURGE_CFG=1)
  if /I "%%~A"=="/purge:exe"  set DO_PURGE_EXE=1
  if /I "%%~A"=="/purge:cfg"  set DO_PURGE_CFG=1
  if /I "%%~A"=="/silent"     set DO_SILENT=1
)

echo ========= %APP_NAME% Uninstall =========

:: 1) Stop any running instance
echo Stopping running process (if any)...
taskkill /IM "%APP_NAME%.exe" /F >nul 2>&1

:: 2) Remove Scheduled Tasks (all common names)
echo Removing Scheduled Tasks...
for %%T in ("%APP_NAME%" "%APP_NAME% (User)" "%APP_NAME% (All Users)") do (
  schtasks /Delete /TN "%%~T" /F >nul 2>&1
)

:: 3) Remove Startup shortcuts
echo Removing Startup shortcuts...
if exist "%USER_START%" del /F /Q "%USER_START%" >nul 2>&1
if exist "%ALL_START%"  del /F /Q "%ALL_START%"  >nul 2>&1

:: 4) Remove Run/RunOnce keys
echo Removing Run entries...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "%APP_NAME%" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "%APP_NAME%" /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "%APP_NAME%" /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "%APP_NAME%" /f >nul 2>&1

:: 5) Delete app data/state folders
echo Removing app data folders (if present)...
rmdir /S /Q "%LOCALAPPDATA%\%APP_NAME%" >nul 2>&1
rmdir /S /Q "%APPDATA%\%APP_NAME%" >nul 2>&1
rmdir /S /Q "C:\ProgramData\%APP_NAME%" >nul 2>&1

:: 6) Optional purge of EXE/config (no prompts)
if "%DO_PURGE_EXE%"=="1" del /F /Q "%~dp0%APP_NAME%.exe" >nul 2>&1
if "%DO_PURGE_CFG%"=="1" del /F /Q "%~dp0config.json"    >nul 2>&1

echo.
echo Uninstall complete. Startup hooks have been removed.
if "%DO_SILENT%"=="1" (endlocal & exit /b 0)
pause
endlocal
