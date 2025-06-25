@echo off
echo Building TikTok Live Plugin for TouchPortal...

REM Créer le dossier de build
if not exist "build" mkdir build
if not exist "build\TikTokLivePlugin" mkdir build\TikTokLivePlugin

REM Installer les dépendances
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Créer l'exécutable
echo Creating executable...
pyinstaller --onefile --noconsole --name tiktok_plugin tiktok_plugin.py

REM Copier les fichiers dans le dossier de build
echo Copying files...
copy dist\tiktok_plugin.exe build\TikTokLivePlugin\
copy entry.tp build\TikTokLivePlugin\

REM Créer une icône par défaut (optionnel)
echo Creating default icon...
echo. > build\TikTokLivePlugin\tiktok.png

REM Créer le fichier plugin.json nécessaire
echo Creating plugin.json...
copy entry.tp build\TikTokLivePlugin\plugin.json

echo Build complete! 
echo.
echo To install:
echo 1. Copy the 'build\TikTokLivePlugin' folder to your TouchPortal plugins directory
echo 2. The plugin will appear in TouchPortal after restart
echo.
echo TouchPortal plugins directory is usually located at:
echo %APPDATA%\TouchPortal\plugins\
echo.
pause