$py = "$PSScriptRoot\..\backend\.venv\Scripts\python.exe"
Push-Location "$PSScriptRoot\..\backend"; & $py -m pytest -q; Pop-Location
Push-Location "$PSScriptRoot\..\frontend"; npm test; Pop-Location
