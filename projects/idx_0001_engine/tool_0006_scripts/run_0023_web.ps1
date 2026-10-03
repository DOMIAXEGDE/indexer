param([int]$var_1801_port = 8765, [string]$var_1802_database = '')
$var_1803_root = Split-Path -Parent $PSScriptRoot
$var_1804_python = & py -3.12 -c 'import sys; print(sys.executable)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required. Set up Python before launching.' }
$env:INDEXER_PYTHON = $var_1804_python.Trim()
if ($var_1802_database) { $env:INDEXER_DATABASE = $var_1802_database }
Write-Host "Indexer: http://127.0.0.1:$var_1801_port/x3.php (Ctrl+C stops the local server)"
& php -S "127.0.0.1:$var_1801_port" -t $var_1803_root (Join-Path $var_1803_root 'x3.php')
