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
2. `docker-compose up` (coming soon)
3. `cd apps/web && npm run dev`
4. `cd apps/api && uvicorn api.main:app --reload`


Test commit