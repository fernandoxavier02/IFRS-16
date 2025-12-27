# 20-quality.md — Quality Standards

## Code Style

- Match existing indentation and naming conventions
- Imports at top of file only
- No orphan imports in middle of file
- Preserve existing comments unless asked to change

## Testing

- Run `pytest -v` before completing backend tasks
- Tests use SQLite in-memory (see `conftest.py`)
- Markers: `@pytest.mark.asyncio`, `@pytest.mark.slow`, `@pytest.mark.integration`

## Database

- Use Alembic for schema changes in production
- `init_db()` only for development
- SSL required for PostgreSQL connections

## Security

- Never commit secrets (`.env` is gitignored)
- Validate critical settings at startup in production
- CORS: explicit origins only, no wildcards with credentials

## API Conventions

- User auth: `Authorization: Bearer <JWT>`
- Admin auth: `X-Admin-Token` header or Admin JWT
- All async endpoints use `AsyncSession`

## Invariants

1. License validation: always check `is_valid` property
2. Stripe webhooks: verify signature before processing
3. JWT: validate expiry and claims
4. Passwords: use bcrypt via passlib

## Error Handling

- Global exception handler in `main.py`
- Debug info only in non-production
- Log errors with traceback
