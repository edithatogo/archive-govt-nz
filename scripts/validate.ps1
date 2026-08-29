$ErrorActionPreference = 'Stop'
uv run --locked python tools/check.py `
  --pytest-workers auto `
  --pytest-distribution loadscope
exit $LASTEXITCODE
