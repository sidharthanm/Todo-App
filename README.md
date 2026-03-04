# Tier1 Smart Todo

FastAPI + PostgreSQL todo application with JWT auth, hierarchical tasks (parent/subtasks), and a static HTML frontend.

## Current Features

- User registration and login
- JWT-protected todo APIs
- Nested todos using `parent_id`
- Soft-finish flow (task is marked `completed=true` instead of hard delete)
- Finished parent-task cleanup endpoint
- Browser frontend at `frontend/index.html`

## Tech Stack

- Python (`pyproject.toml` requires `>=3.13`)
- FastAPI
- SQLAlchemy
- Pydantic v2
- PostgreSQL + `psycopg2-binary`
- Alembic
- `python-jose` (JWT)
- `passlib[argon2]` (password hashing)
- Uvicorn

Note: Docker currently uses `python:3.11-slim`, which does not match the `>=3.13` project requirement.

## Project Structure

- `app/main.py` - FastAPI app setup, CORS, router registration
- `app/api/auth.py` - auth endpoints
- `app/api/todos.py` - todo endpoints
- `app/services/` - business logic
- `app/models/` - SQLAlchemy models
- `app/schemas/` - request/response schemas
- `frontend/index.html` - static UI
- `alembic/` - migrations
- `docker-compose.yml` - app + database services

## Environment Variables

Set these in `.env`:

- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default `30` if omitted)

Example `DATABASE_URL`:

```env
DATABASE_URL=Your_postgres_URL_here
```

## Run Locally (uv)

1. Install dependencies:
```bash
uv sync
```
2. Start PostgreSQL (for example with Docker):
```bash
docker compose up -d db
```
3. Apply migrations:
```bash
uv run alembic upgrade head
```
4. Start API:
```bash
uv run uvicorn app.main:app --reload
```
5. Open UI:
  - Open `frontend/index.html` in browser
  - API base URL used by UI: `http://127.0.0.1:8000`

## Run with Docker Compose

```bash
docker compose up --build
```

Services:

- API: `http://127.0.0.1:8000`
- PostgreSQL: `localhost:5432` (`postgres` / `toor`, DB: `todoapp`)

## API Reference

All `/todos` routes require:

```http
Authorization: Bearer <token>
```

### Auth

- `POST /auth/register`
  - Body: `{ "email": "...", "password": "..." }`
  - Creates a user with hashed password
- `POST /auth/login`
  - Body: `{ "email": "...", "password": "..." }`
  - Returns: `{ "access_token": "..." }`

### Todos

- `POST /todos/`
  - Create todo
  - Body:
    - `title` (required)
    - `description` (optional)
    - `deadline` (optional datetime)
    - `parent_id` (optional UUID of existing user-owned parent task)
- `GET /todos/`
  - Returns user todos as a nested tree using `subtasks`
- `PUT /todos/{todo_id}`
  - Partial update fields:
    - `title`
    - `description`
    - `completed`
- `DELETE /todos/{todo_id}`
  - Soft-finish behavior: marks todo as completed and returns:
  - `{ "finished": true, "id": "<todo_id>", "completed": true }`
- `DELETE /todos/finished/clear-parents`
  - Hard-deletes completed root tasks (`parent_id IS NULL`)
  - Returns `{ "cleared": <count> }`

## Data Model

### `users`

- `id` (UUID, PK)
- `email` (unique, indexed)
- `hashed_password`

### `todos`

- `id` (UUID, PK)
- `title`
- `description` (nullable)
- `completed` (boolean, default `false`)
- `deadline` (nullable datetime)
- `created_at` (datetime)
- `user_id` (FK -> `users.id`)
- `parent_id` (nullable self-reference FK -> `todos.id`, `ondelete="CASCADE"`)

## Frontend Notes

`frontend/index.html` supports:

- register/login/logout
- create root todos and subtasks
- edit todo title/description/completed
- mark task finished
- view finished tasks
- clear finished parent tasks

Token is stored in browser `localStorage`.

## Important Notes

- CORS is fully open (`allow_origins=["*"]`, all methods and headers).
- `Base.metadata.create_all(...)` is currently disabled in `app/main.py`; schema should be managed through Alembic.
- Some migrations are placeholders (`pass`), so verify migration history for fresh environments.
