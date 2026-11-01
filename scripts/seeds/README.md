# Test seeds (manual testing and E2E)

The scripts in this folder insert **dummy data for testing only**. They are NOT needed in production and must never be run against a shared or production database.

| | `pipenv run seeders` | `scripts/seeds/*` |
|---|---|---|
| Location | `app/database/seeders.py` | `scripts/seeds/` |
| Purpose | Data the app needs to work (roles, car model catalog, associates, owner user) | Demo data to test features by hand or in E2E |
| Runs in prod | Yes | **No** |

## Order

1. `alembic upgrade head`
2. `pipenv run seeders` (the car seeds need associate 1 from here)
3. Any seed below

Run them from the repository root.

## Cars (`cars.py`)

```bash
python -m scripts.seeds.cars clean
python -m scripts.seeds.cars history
python -m scripts.seeds.cars contract
```

| Scenario | Creates | Use it to test |
|---|---|---|
| `clean` | `DEMO-CLEAN-01`, `DEMO-CLEAN-02` without history | update, status, archive, unarchive, **hard delete** |
| `history` | `DEMO-HIST-01` with 3 transactions | **soft delete** (history is preserved) |
| `contract` | `DEMO-CONTR-01` with an active contract and a demo driver | archive blocked (400) |

Running a scenario again re-arms existing cars (clears `archived_at` / `deleted_at`, status back to `ACTIVE`) so tests can be repeated.

## Transactions (`transactions.py`)

```bash
python -m scripts.seeds.transactions income    # more income than expenses
python -m scripts.seeds.transactions expense   # more expenses than income
```

Inserts random transactions from the last 30 days.

## Adding a new seed

Keep it idempotent when possible, use clearly fake ids (`DEMO-*`), print what it created, and document it here.
