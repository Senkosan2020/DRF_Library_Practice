# DRF Library API

A Django REST Framework project for managing books, borrowings, and payments with JWT auth, filtering, throttling, optional pagination, and OpenAPI docs.

## Quick start

### Requirements
- Python 3.14
- pip
- (optional) Node is **not** required

### Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Useful URLs**
- API root: `http://localhost:8000/api/`
- Swagger UI: `http://localhost:8000/docs/`
- OpenAPI Schema: `http://localhost:8000/schema/`
- Admin: `http://localhost:8000/admin/`
- Health: `/healthz/` and `/health/`

## Authentication (JWT)

- `POST /users/token/` — obtain access & refresh tokens (email + password)
- `POST /users/token/refresh/` — refresh access token
- `POST /users/register/` — user registration
- `GET /users/me/` — current user profile

Include header for protected endpoints:
```
Authorization: Bearer <ACCESS_TOKEN>
```

## Endpoints

### Books
- `GET /api/books/` — public list
  - Filters: `?author=`, `?title=`, `?cover=HARD|SOFT`
  - Search: `?search=`
  - Ordering: `?ordering=title|author|daily_fee|inventory|-...`
- `GET /api/books/{id}/` — retrieve
- `POST /api/books/` — **admin only**
  - Validations: `inventory > 0`, `daily_fee > 0`

### Borrowings
- `GET /api/borrowings/` — list
  - Regular users: only own items
  - Admin: all items
  - Filters:
    - `?is_active=true|false`
    - `?overdue=true|false`
    - `?user_id=<id>` (admin only)
  - Ordering: `?ordering=borrow_date|expected_return_date|actual_return_date|id|-...`
  - **Pagination:** off by default; enable with `?limit=<N>[&offset=<M>]`
- `GET /api/borrowings/{id}/` — retrieve
- `POST /api/borrowings/` — create (authenticated)
- `POST /api/borrowings/{id}/return/` — return (owner or admin)

### Payments
- `GET /api/payments/` — list
  - Regular users: only own (by borrowing owner)
  - Admin: all
  - Filters: `?borrowing=`, `?status=`, `?type=`
  - Ordering: `?ordering=created_at|-created_at|amount|paid_at|id`
- `GET /api/payments/{id}/` — retrieve
- `GET /api/payments/preview/?borrowing=<id>` — preview late fee for a borrowing (owner or admin)
- `POST /api/payments/` — create a payment (owner or admin); duplicate open payments prevented

**Examples**
```bash
# Preview late fee
curl -H "Authorization: Bearer <ACCESS>"   "http://localhost:8000/api/payments/preview/?borrowing=1"

# Create payment
curl -X POST -H "Authorization: Bearer <ACCESS>"   -H "Content-Type: application/json"   -d '{"borrowing": 1}'   http://localhost:8000/api/payments/
```

## Throttling

Per-user throttling is applied to sensitive actions:
- Borrowings: `create`, `return`
- Payments: `preview`, `create`

## Testing

Run the full test suite:
```bash
pytest -q
```

## Code style & hooks

We use `black` and `flake8` via pre-commit hooks:
```bash
pip install pre-commit black flake8
pre-commit install
pre-commit run --all-files
```

## CI

GitHub Actions runs tests on every push/PR (Python 3.14).

## Project layout (short)

```
config/
  settings.py
  urls.py
  pagination.py
books/
  models.py
  serializers.py
  views.py
  urls.py
borrowings/
  models.py
  serializers.py
  views.py
  urls.py
payments/
  models.py
  serializers.py
  views.py
  urls.py
users/
  ...
tests/
  ...
```
