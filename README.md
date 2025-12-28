# DRF Library API

A Django REST Framework project for managing books and borrowings with JWT auth, filtering, throttling, and OpenAPI docs.

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
