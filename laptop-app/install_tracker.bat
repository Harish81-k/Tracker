@echo off
echo ==============================================
echo Installing SentinelTrack Laptop Background Service
echo ==============================================

echo [1/3] Compiling python script into a hidden executable...
python -m PyInstaller --noconfirm --onedir --windowed --name "SentinelTracker"  "laptop_tracker.py"

echo [2/3] Moving executable to a permanent location...
if not exist "%LOCALAPPDATA%\SentinelTrack" mkdir "%LOCALAPPDATA%\SentinelTrack"
xcopy /Y /S /I "dist\SentinelTracker" "%LOCALAPPDATA%\SentinelTrack\bin"

echo [3/3] Adding to Windows Startup (Registry)...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SentinelTracker" /t REG_SZ /d "%LOCALAPPDATA%\SentinelTrack\bin\SentinelTracker.exe" /f

echo.
echo ==============================================
echo INSTALLATION COMPLETE!
echo ==============================================
echo The tracker is now installed and will automatically start silently in the background 
echo every time you log into Windows.
echo.
echo Starting it now for the first time...
start "" "%LOCALAPPDATA%\SentinelTrack\bin\SentinelTracker.exe"
pause
