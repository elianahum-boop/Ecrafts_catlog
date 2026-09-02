@echo off
cd /d "%~dp0"

echo.
echo ==========================================
echo       Uploading Ecrafts catalog updates
echo ==========================================
echo.

where git > nul 2> nul
if errorlevel 1 (
    echo Git was not found on this computer.
    echo Make sure Git is installed and available, then run this file again.
    echo.
    pause
    exit /b 1
)

git rev-parse --is-inside-work-tree > nul 2> nul
if errorlevel 1 (
    echo This folder is not recognized as a Git repository.
    echo Make sure this file is inside the correct catalog folder.
    echo.
    pause
    exit /b 1
)

echo Step 1: adding only site and data files...
git add -- index.html products-data.js S1.png S2.png S3.png logo.jpg favicon.png ".gitignore"
if errorlevel 1 goto error

echo Step 2: checking for changes...
git diff --cached --quiet
if not errorlevel 1 (
    echo No new changes to upload.
    echo.
    pause
    exit /b 0
)

echo Step 3: saving changes...
git commit -m "Update catalog"
if errorlevel 1 goto error

echo Step 4: uploading to GitHub...
git push origin main
if errorlevel 1 goto error

echo.
echo ==========================================
echo       GitHub Pages update completed
echo ==========================================
echo.
echo The live site usually updates within a minute or two.
echo.
pause
exit /b 0

:error
echo.
echo ==========================================
echo       Upload failed
echo ==========================================
echo.
echo Check the error message above.
echo If GitHub asks you to sign in, sign in and run this file again.
echo.
pause
exit /b 1
