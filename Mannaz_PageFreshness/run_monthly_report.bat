BATCH_FILE = '''@echo off
echo ========================================
echo MANNAZ PAGE FRESHNESS MONTHLY REPORT
echo ========================================
echo.
echo Starting automated report generation...
echo This may take 10-30 minutes depending on site size.
echo.

python run_monthly_report.py

echo.
echo ========================================
echo Report generation complete!
echo Press any key to close this window.
echo ========================================
pause
'''
