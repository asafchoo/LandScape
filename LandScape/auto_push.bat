@echo off
REM Navigate to the Git repository
cd /d "C:\Users\hamaadama\AppData\Roaming\inkscape\extensions\LandScape"

REM Stage all changes
git add .

REM Commit changes with a timestamped message
git commit -m "Auto commit on %date% %time%"

REM Push changes to the remote repository
git push origin main