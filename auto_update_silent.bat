@echo off
REM Silent version for Task Scheduler - no pause or prompts

echo %date% %time% - Starting auto-update >> update_log.txt

cd /d "%~dp0"

echo Running scrapers... >> update_log.txt
python run_all_spiders.py >> update_log.txt 2>&1

echo Committing changes... >> update_log.txt
git add scraped_jobs.json
git commit -m "Auto-update jobs - %date% %time%" >> update_log.txt 2>&1

echo Pushing to GitHub... >> update_log.txt
git push origin main >> update_log.txt 2>&1

echo %date% %time% - Update complete >> update_log.txt
echo. >> update_log.txt
