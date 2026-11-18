$ErrorActionPreference = 'Stop'
# No execution policy change or administrator privileges are needed.
python "$PSScriptRoot\setup_windows.py" @args
exit $LASTEXITCODE
