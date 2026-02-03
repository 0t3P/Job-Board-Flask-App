@echo off
echo ================================================
echo COMMIT AND PUSH TO GITHUB (via GitHub Desktop)
echo ================================================
echo.
echo [1/2] Committing all changes...
echo.

REM Add and commit all changes
git add .
git commit -m "Update: %date% %time%"

echo.
echo [2/2] Opening GitHub Desktop to sync...
echo.

REM Open GitHub Desktop (it will show changes ready to push)
start "" "C:\Users\%USERNAME%\AppData\Local\GitHubDesktop\GitHubDesktop.exe"

timeout /t 2 /nobreak >nul

echo.
echo ================================================
echo Changes committed!
echo GitHub Desktop opened - Click "Push origin"
echo This will update your Render website automatically
echo ================================================
echo.
pause
