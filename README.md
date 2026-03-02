# Tier1 Smart Todo - Services and Tech Documentation

## Overview

Tier1 Smart Todo is a FastAPI-based backend for user-authenticated todo management, with a minimal HTML frontend and PostgreSQL persistence.

## Services Offered by the App

### 1) Authentication Service (`/auth`)

Handles account creation and login.

- `POST /auth/register`
  - Input: `email`, `password`
  - Behavior: creates a user with Argon2-hashed password
- `POST /auth/login`
  - Input: `email`, `password`
  - Behavior: validates credentials and returns JWT access token
  - Output: `{ "access_token": "..." }`

### 2) Todo Management Service (`/todos`)

Provides CRUD operations for authenticated users' todos.

All routes require `Authorization: Bearer <token>`.

- `POST /todos/`
  - Creates a todo for current user
  - Fields: `title`, optional `description`, optional `deadline`
- `GET /todos/`
  - Lists all todos belonging to current user
- `PUT /todos/{todo_id}`
  - Updates selected fields (`title`, `description`, `completed`) on user's todo
- `DELETE /todos/{todo_id}`
  - Deletes a user's todo

### 3) Frontend Service (Static HTML UI)

A simple browser UI is present at `frontend/index.html` for:

- registration
- login (stores JWT in localStorage)
- creating todos
- listing todos

Note: this frontend is static and calls API directly at `http://127.0.0.1:8000`.

### 4) Database Service (PostgreSQL via Docker Compose)

`docker-compose.yml` defines a `db` service:

- Image: `postgres:18`
- DB name: `todoapp`
- Port: `5432`

The app connects using `DATABASE_URL` from `.env`.

## Data Model

### `users`

- `id` (UUID, PK)
- `email` (unique)
- `hashed_password`

### `todos`

- `id` (UUID, PK)
- `title`
- `description` (nullable)
- `completed` (default `false`)
- `deadline` (nullable datetime)
- `created_at` (datetime)
- `user_id` (FK -> `users.id`)

## Technology Stack

### Backend

- Python (project metadata requires `>=3.13`; Dockerfile currently uses Python `3.11-slim`)
- FastAPI
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- Pydantic (request schemas/validation)

### Authentication & Security

- OAuth2 Bearer token flow (FastAPI security dependency)
- JWT tokens via `python-jose`
- Password hashing with `passlib[argon2]`

### Database & Migrations

- PostgreSQL
- Alembic for schema migrations
- `psycopg2-binary` driver

### Configuration & Environment

- `.env` loading via `python-dotenv`
- Config variables:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`

### Containerization

- Dockerfile for app image
- Docker Compose for app + database orchestration

### Development/Testing Tools

- `pytest`
- `httpx`

## Runtime Architecture (High-Level)

1. Client calls FastAPI endpoints.
2. Auth routes issue JWT tokens after credential verification.
3. Protected todo routes decode JWT and resolve current user.
4. Service layer performs DB operations through SQLAlchemy session.
5. PostgreSQL stores persistent user and todo records.

## Important Implementation Notes

- CORS is currently fully open (`allow_origins=["*"]`, all methods/headers).
- Tables are created at startup via `Base.metadata.create_all(bind=engine)` in `app/main.py`.
- Alembic is also configured for migrations (mixed strategy currently).
- Existing `README.md` is empty; this file serves as the active documentation requested.
