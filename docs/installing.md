# Installing GearLoan

## Requirements

- Python 3.11+
- PostgreSQL 14+ (SQLite works for local dev)
- Docker and docker-compose (optional)

## Quick start with Docker

```bash
git clone https://github.com/YOUR-NAME/gearloan.git
cd gearloan
cp .env.example .env          # edit SECRET_KEY and email settings
docker compose up --build
```

Open http://localhost:8000. The first `docker compose up` runs migrations automatically.

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

## Quick start without Docker

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # edit as needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://localhost:8000.

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (must be set) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL | SQLite |
| `EMAIL_BACKEND` | Django email backend | console |
| `DEFAULT_FROM_EMAIL` | Sender address | `gearloan@example.com` |

## Production checklist

- Set `DEBUG=False` and `SECRET_KEY` to a long random string.
- Set `DATABASE_URL` to your PostgreSQL connection string.
- Configure a real email backend (`smtp`, SendGrid, etc.).
- Run `python manage.py collectstatic` and serve `staticfiles/` with nginx.
- Set `ALLOWED_HOSTS` to your domain.
