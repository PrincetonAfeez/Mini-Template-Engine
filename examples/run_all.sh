#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Rendering example templates..."
python -m template_engine examples/hello.tmpl --context examples/context.json
echo
python -m template_engine examples/conditions.tmpl --context examples/context.json
echo
python -m template_engine examples/loop.tmpl --context examples/context.json
echo
python -m template_engine examples/invoice.tmpl --context examples/context.json
echo
python -m template_engine examples/showcase.tmpl --context examples/context.json -v
