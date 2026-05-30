$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== ruff ==" -ForegroundColor Cyan
ruff check template_engine tests

Write-Host "== mypy ==" -ForegroundColor Cyan
mypy template_engine

Write-Host "== tests + coverage ==" -ForegroundColor Cyan
coverage run -m pytest -q
coverage report --fail-under=95

Write-Host "All checks passed." -ForegroundColor Green
