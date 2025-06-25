@echo off
echo TouchPortal TikTok Plugin Troubleshooting
echo ========================================
echo.

REM Vérifier si TouchPortal est fermé
echo Checking if TouchPortal is running...
tasklist /FI "IMAGENAME eq TouchPortal.exe" 2>NUL | find /I /N "TouchPortal.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo WARNING: TouchPortal is running. Please close it before continuing.
    echo Press any key to continue anyway, or Ctrl+C to exit.
    pause >nul
)

REM Définir les chemins
set "PLUGIN_DIR=%APPDATA%\TouchPortal\plugins\TikTokLivePlugin"
set "BUILD_DIR=build\TikTokLivePlugin"

echo.
echo Plugin directory: %PLUGIN_DIR%
echo Build directory: %BUILD_DIR%
echo.

REM Vérifier si le dossier de build existe
if not exist "%BUILD_DIR%" (
    echo ERROR: Build directory not found. Please run build.bat first.
    pause
    exit /b 1
)

REM Créer le dossier plugin s'il n'existe pas
if not exist "%PLUGIN_DIR%" (
    echo Creating plugin directory...
    mkdir "%PLUGIN_DIR%"
)

REM Supprimer l'ancien plugin
echo Removing old plugin files...
if exist "%PLUGIN_DIR%\*" del /Q "%PLUGIN_DIR%\*"

REM Copier les nouveaux fichiers
echo Copying plugin files...
copy "%BUILD_DIR%\tiktok_plugin.exe" "%PLUGIN_DIR%\" >nul
copy "%BUILD_DIR%\entry.tp" "%PLUGIN_DIR%\" >nul

REM Créer plugin.json (copie de entry.tp pour compatibilité)
echo Creating plugin.json...
copy "%BUILD_DIR%\entry.tp" "%PLUGIN_DIR%\plugin.json" >nul

REM Créer une icône simple
echo Creating icon...
if not exist "%PLUGIN_DIR%\tiktok.png" (
    echo. > "%PLUGIN_DIR%\tiktok.png"
)

REM Vérifier les fichiers
echo.
echo Verifying installation...
if exist "%PLUGIN_DIR%\tiktok_plugin.exe" (
    echo [OK] tiktok_plugin.exe found
) else (
    echo [ERROR] tiktok_plugin.exe missing
)

if exist "%PLUGIN_DIR%\entry.tp" (
    echo [OK] entry.tp found
) else (
    echo [ERROR] entry.tp missing
)

if exist "%PLUGIN_DIR%\plugin.json" (
    echo [OK] plugin.json found
) else (
    echo [ERROR] plugin.json missing
)

REM Tester l'exécutable
echo.
echo Testing executable...
"%PLUGIN_DIR%\tiktok_plugin.exe" --version 2>nul
if %ERRORLEVEL% == 0 (
    echo [OK] Executable runs successfully
) else (
    echo [WARNING] Executable test failed - this may be normal
)

echo.
echo Installation completed!
echo.
echo Next steps:
echo 1. Start TouchPortal
echo 2. The plugin should appear in the plugins list
echo 3. If you still see errors, check TouchPortal logs
echo.
echo TouchPortal logs location:
echo %APPDATA%\TouchPortal\logs\
echo.
echo Common issues:
echo - Make sure TouchPortal is completely closed before installation
echo - Check that Python dependencies are installed
echo - Verify that Windows allows the executable to run
echo.
pause