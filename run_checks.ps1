$ErrorActionPreference = "Stop"

py -3 -m py_compile resource-monitor/app.py file-organizer/organizer.py csv-report/report.py
py -3 -m unittest discover -s file-organizer/tests -v
py -3 -m unittest discover -s csv-report/tests -v
py -3 csv-report/report.py csv-report/demo/sales.csv --output csv-report/demo-report.html

Write-Host "All checks passed." -ForegroundColor Green
