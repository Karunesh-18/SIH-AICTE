# Windows equivalent of `make dev` (no make/docker needed). Run from repo root.
$py = "$PSScriptRoot\..\backend\.venv\Scripts\python.exe"
Push-Location "$PSScriptRoot\..\backend"
& $py -m alembic upgrade head
& $py -m app.seed.run
Start-Process $py -ArgumentList "-m uvicorn app.main:app --reload --port 8000"
Pop-Location
Push-Location "$PSScriptRoot\..\frontend"; npm run dev; Pop-Location
