$ErrorActionPreference = "Stop"

python -m py_compile resource-monitor/app.py file-organizer/organizer.py csv-report/report.py
python -m unittest discover -s file-organizer/tests -v
python -m unittest discover -s csv-report/tests -v
python csv-report/report.py csv-report/demo/sales.csv --output csv-report/demo-report.html

Write-Host "All checks passed." -ForegroundColor Green

