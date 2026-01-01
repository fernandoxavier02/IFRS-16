# Quality and Verification

Standard commands for verification in this repo:

## Backend
- **Test all**: `cd backend && pytest -v`
- **Specific test**: `cd backend && pytest tests/test_filename.py -v`
- **Run migration**: `cd backend && alembic upgrade head`

## Frontend & Integration
- **E2E tests**: `.\testar_sistema_completo.ps1` (PowerShell)
- **Deploy Preview**: `firebase deploy --only hosting --project ifrs16-app`

## Code Style
- Follow existing patterns in `backend/app/` for Python.
- Follow existing patterns in `assets/js/` for Javascript.
