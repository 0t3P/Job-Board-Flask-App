@echo off
echo ================================================
echo AUTOMATIC JOB UPDATE SCRIPT
echo ================================================
echo.
echo [1/3] Running all scrapers...
echo.

REM Run the scrapers
python run_all_spiders.py

echo.
echo [2/3] Committing changes to Git...
echo.

REM Add and commit the updated jobs file
git add scraped_jobs.json
git commit -m "Auto-update jobs - %date% %time%"

echo.
echo [3/3] Pushing to GitHub...
echo.

REM Push to GitHub
git push origin main

echo.
echo ================================================
echo SUCCESS! Jobs updated and pushed to GitHub
echo Render will auto-deploy in 1-2 minutes
echo ================================================
echo.
pause
