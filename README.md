# Topic Verifier

Backend service for topic verification, archive matching, student submissions, admin review, and import/export workflows.

## Prerequisites

- Python 3.13+
- PostgreSQL with pgvector enabled
- A virtual environment for the project

## Local setup

1. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
2. Install backend dependencies:
   - `pip install -r backend/requirements.txt`
3. Create a `.env` file in the project root and configure your database and app settings.
4. Run the API:
   - `uvicorn app.main:app --reload`
   - from the `backend` directory

## Environment variables

Key settings include:

- `DATABASE_URL` for PostgreSQL
- `JWT_SECRET` for admin authentication
- `SIMILARITY_THRESHOLD` for archive matching sensitivity
- `EMAIL_BACKEND` for email delivery mode
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` for SMTP delivery

## Email configuration

The application supports two delivery modes:

- `EMAIL_BACKEND=console` (default in development): emails are logged instead of being sent.
- `EMAIL_BACKEND=smtp`: emails are sent through the configured SMTP server.

For local development, the default console mode is recommended. To send real emails, set:

```env
EMAIL_BACKEND=smtp
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USER=your-user
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@example.com
```

Email delivery is non-blocking and runs in the background after submission or review actions.

## Testing

Run the backend test suite with:

```bash
.venv\Scripts\python.exe -m pytest backend/tests -q
```

> Blockchain layer added: see START_HERE.md for run steps and the viva demo.
