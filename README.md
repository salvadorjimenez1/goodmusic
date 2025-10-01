# goodmusic
A Goodreads-style app for music.  
Frontend: Next.js + Tailwind  
Backend: FastAPI + Postgres  

## Structure
- `apps/web` → Next.js frontend
- `apps/api` → FastAPI backend
- `db` → migrations + schema
- `infra` → Docker, infra configs
- `packages/shared` → shared utils/types

## Setup
1. Clone repo
2. `docker-compose up --build`
3. `cd apps/web && npm run dev`
4. `cd apps/api && uvicorn api.main:app --reload`

## Testing
1. Always run through your interpreter: `python -m pytest -v`

## Alembic
### Every time you change models.py, just:
1. Run `alembic revision --autogenerate -m "change description"`.
2. Run `alembic upgrade head`.