# Stockchallangeapp

A small FastAPI-based project to track user stock transactions and current prices.

## Migrations & Demo

This project uses Alembic for database migrations. The Alembic configuration is in `alembic/` and the default DB URL is set to `sqlite:///./portfolio.db` in `alembic.ini`.

How to run migrations locally (in your configured conda env):

1. Ensure dependencies are installed (in your configured environment):

```bash
pip install -r requirements.txt
pip install alembic
```

2. Generate an autogenerate migration (optional if you already have a migration):

```bash
# make sure project root is on PYTHONPATH
PYTHONPATH="$(pwd)" alembic revision --autogenerate -m "create initial"
```

3. Apply migrations:

```bash
PYTHONPATH="$(pwd)" alembic upgrade head
```

Demo: create users & transactions and see price updates

1. Run the test helper which drops and recreates the DB and inserts test users and transactions:

```bash
PYTHONPATH="$(pwd)" python app/utils/test_create_transaction.py
```

This script will also upsert tracked tickers into the `stock_prices` table.

2. Start the app (this will also start the background price updater on startup):

```bash
PYTHONPATH="$(pwd)" uvicorn app.main:app --reload
```

3. To quickly observe the background price updater in action (dev/demo):

```bash
# start a short-run updater demonstration (uses 5s interval inside the script)
PYTHONPATH="$(pwd)" python - <<'PY'
from time import sleep
from app.database import SessionLocal
from app.models import StockPrice
from app.services.price_updater import start_price_updater


def print_prices(label):
    db = SessionLocal()
    rows = db.query(StockPrice).all()
    print('\n' + label)
    for r in rows:
        print(f'  {r.symbol}: price={r.current_price} last_updated={r.last_updated}')
    db.close()

print_prices('Before updater')
thread, stop_event = start_price_updater(interval_seconds=5)
sleep(10)
print_prices('After updater')
stop_event.set()
thread.join(timeout=2)
PY
```

Notes
- The test script drops the DB and recreates it — only use in development.
- In production use Alembic migrations instead of dropping the DB.
- If you want migrations to run in CI or other dev machines, ensure `alembic` is installed and available in the environment.

---

If you want I can also add a Makefile or npm-style scripts for these commands to make them easier to run.
