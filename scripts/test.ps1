$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== ruff lint ==" -ForegroundColor Cyan
ruff check template_engine tests

Write-Host "== ruff format check ==" -ForegroundColor Cyan
ruff format --check template_engine tests

Write-Host "== mypy ==" -ForegroundColor Cyan
mypy template_engine

Write-Host "== tests + coverage ==" -ForegroundColor Cyan
coverage run -m pytest -q
coverage report --fail-under=95

Write-Host "All checks passed." -ForegroundColor Green
