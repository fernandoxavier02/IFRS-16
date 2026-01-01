# Self-Review Checklist

Before submitting any change, verify the following:

## Correctness
- [ ] Does the code solve the issue described?
- [ ] Are edge cases handled?
- [ ] No regression in existing features?

## Security
- [ ] No secrets or hardcoded tokens?
- [ ] Inputs validated (Pydantic schemas used)?
- [ ] CORS rules followed?

## Verification (Mandatory)
- [ ] Ran `cd backend && pytest -v` and all tests passed?
- [ ] (If applicable) Ran `.\testar_sistema_completo.ps1`?

## Maintainability
- [ ] Consistent naming (snake_case in Python, camelCase in JS)?
- [ ] `CHANGELOG_AI.md` updated?
- [ ] `DECISIONS.md` updated if architectural changes were made?

## Commands Used for Evidence:
- Backend: `cd backend && pytest -v`
- E2E: `.\testar_sistema_completo.ps1`
