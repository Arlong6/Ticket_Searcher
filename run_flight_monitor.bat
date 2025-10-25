@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd "C:\Project\Python_Environment\LTC\Scripts"
call activate

cd /d "C:\Project\Ticket_Searcher"
echo ========================================= >> logs\scheduler.log
echo 執行時間: %date% %time% >> logs\scheduler.log
echo ========================================= >> logs\scheduler.log

python main.py >> logs\scheduler.log 2>&1

echo 執行完成: %date% %time% >> logs\scheduler.log
echo. >> logs\scheduler.log