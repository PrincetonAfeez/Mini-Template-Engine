$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Rendering example templates..." -ForegroundColor Cyan
python -m template_engine examples/hello.tmpl --context examples/context.json
Write-Host ""
python -m template_engine examples/conditions.tmpl --context examples/context.json
Write-Host ""
python -m template_engine examples/loop.tmpl --context examples/context.json
Write-Host ""
python -m template_engine examples/invoice.tmpl --context examples/context.json
Write-Host ""
python -m template_engine examples/showcase.tmpl --context examples/context.json -v
