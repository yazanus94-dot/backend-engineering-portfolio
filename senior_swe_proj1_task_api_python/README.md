# Task Management REST API (Flask)

Personal portfolio project: a small but realistic backend REST API —
CRUD endpoints over tasks, input validation, structured error responses,
filtering, and pagination — built to demonstrate backend service design,
not just a "hello world" route.

## Why this project

Built to demonstrate the core of what a backend engineering role asks
for: designing a clean API surface, validating input defensively,
returning consistent error shapes, and backing all of it with a test
suite that actually exercises edge cases (not just the happy path).

## Design notes

- **In-memory store, by design.** No database dependency — keeps the
  project runnable with zero setup and keeps the focus on API design,
  validation, and testing rather than infrastructure. Swapping in a real
  datastore (e.g. SQLite via `sqlalchemy`) would only touch the storage
  layer, not the route/validation logic.
- **Explicit validation layer** (`ValidationError` + `@app.errorhandler`)
  rather than scattering `if` checks and ad-hoc error responses through
  each route — every validation failure returns the same consistent JSON
  shape (`{"error": ..., "message": ..., "field": ...}`).
- **22 unit tests** covering creation, validation (missing/blank/too-long
  title, invalid status/priority), retrieval, filtering, pagination
  (including out-of-range limit/offset), partial updates, and deletion —
  including negative/edge cases, not just success paths.

## Run it

```bash
pip install -r requirements.txt

# run the API
python src/app.py        # serves on http://localhost:5000

# run the tests
python -m unittest discover -s tests -v
```

## Example usage

```bash
curl -X POST localhost:5000/tasks -H "Content-Type: application/json" \
  -d '{"title": "Write tests", "priority": 2}'

curl "localhost:5000/tasks?status=todo&limit=10"

curl -X PATCH localhost:5000/tasks/1 -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

## Project structure

```
py1_task_api/
├── README.md
├── requirements.txt
├── src/
│   └── app.py           # Flask app: routes, validation, error handling
└── tests/
    └── test_app.py      # 22 unit tests (unittest, pytest-discoverable)
```
