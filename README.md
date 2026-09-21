# Spend Tracker API

A small expense-tracking service: a FastAPI backend backed by SQLite, and a
minimal HTML/JS frontend for adding expenses and viewing a summary.

## How to run

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# API key the backend expects (defaults to "dev-secret-key" if unset)
export API_KEY=dev-secret-key

uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/ for the UI (enter the same API key in the
"API Key" field), or http://127.0.0.1:8000/docs for interactive API docs.

Run the tests:

```bash
pytest
```

The app uses `expenses.db` (SQLite) in the working directory by default;
override with the `DATABASE_URL` env var. The tests use their own SQLite
file (`test_expenses.db`) and drop/recreate tables between tests, so they
never touch your dev database.

## API

All endpoints (except the static UI) require an `X-API-Key` header matching
the `API_KEY` env var.

- `POST /expenses` — body: `{amount, category, note?, date}`. `amount` must
  be > 0, `category` non-blank, `date` an ISO date (`YYYY-MM-DD`) not in the
  future. Returns 422 on validation failure, 201 + the created row on
  success.
- `GET /expenses?category=&start_date=&end_date=&skip=&limit=` — list
  expenses, all filters optional. Returns 400 if `start_date > end_date`.
- `GET /summary?month=YYYY-MM` — defaults to the current month. Returns
  total spend, spend by category, the previous month's total, percentage
  change vs. the previous month (overall and per category), and a list of
  human-readable insight strings for any category whose spend rose more
  than 20% month-over-month.

## Design decisions

- **FastAPI + SQLAlchemy + Pydantic.** FastAPI gives request validation,
  OpenAPI docs, and typed responses for free, which covers most of the
  "sensible error responses" requirement without extra code.
- **SQLite via SQLAlchemy Core/ORM**, not a raw connection or an in-memory
  list, so the schema, indexing (`category`, `date`), and query filtering
  are explicit and swapping to Postgres later is a one-line `DATABASE_URL`
  change.
- **API key auth** via a required `X-API-Key` header, checked with a FastAPI
  dependency. Chosen over JWT because there's only one "user" concept here
  (a single API consumer) — JWT's session/identity machinery wouldn't add
  anything for this scope.
- **Summary math lives in `app/crud.py`**, separate from the route
  handlers in `app/main.py`, so it's directly unit-testable and the HTTP
  layer stays thin.
- **Month-over-month** compares calendar months (`YYYY-MM`), not a rolling
  30-day window — simpler to reason about and matches how the task phrases
  it ("month-over-month change").
- **Insight threshold** is a >20% increase in a category's total vs. the
  previous month, only when the previous month had nonzero spend (a brand
  new category isn't a "20% increase", it's new spend — flagging it would
  be noise for every new category logged).
- **Frontend is deliberately minimal** — one static HTML file with vanilla
  JS `fetch` calls, served by FastAPI's `StaticFiles`. No build step, no
  framework; it exists to prove the API works end-to-end, not to be a
  product UI.

## What I'd do differently with more time

- Pagination metadata (total count) on `GET /expenses`, not just
  `skip`/`limit`.
- Soft-delete/update endpoints (`PATCH`/`DELETE /expenses/{id}`) — out of
  scope per the spec but an obvious next step for a real tracker.
- Move the API key into a proper secrets flow (currently an env var checked
  in-process) and consider per-client keys if there's ever more than one
  consumer.
- Alembic migrations instead of `create_all()`, once the schema needs to
  evolve after data exists.
- A Dockerfile + deploy to Render/Fly.io (bonus item) — skipped here since
  it requires an external account; the app is deploy-ready as-is (reads
  `DATABASE_URL`/`API_KEY` from the environment, binds via `$PORT` with a
  standard `uvicorn app.main:app --host 0.0.0.0 --port $PORT` start
  command).

## AI usage note

Built with Claude Code end-to-end (backend, tests, frontend, this README)
from the task spec. I reviewed the schema, auth approach, and the
month-over-month/insight calculation logic line by line, and ran the full
test suite plus manual `curl` smoke tests against a live server to confirm
behavior before submitting. No unreviewed code was submitted.
