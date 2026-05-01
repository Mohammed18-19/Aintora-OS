.PHONY: up down build logs shell-backend shell-db migrate seed reset test

# ─── Docker ──────────────────────────────────────────────────────────────────
up:
	docker compose up -d

up-build:
	docker compose up --build

down:
	docker compose down

down-volumes:
	docker compose down -v

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

build:
	docker compose build

# ─── Database ─────────────────────────────────────────────────────────────────
migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	docker compose exec backend alembic revision --autogenerate -m "$$msg"

seed:
	docker compose exec backend python scripts/seed.py

reset-db:
	docker compose down -v
	docker compose up -d postgres
	sleep 3
	docker compose exec backend alembic upgrade head
	docker compose exec backend python scripts/seed.py

# ─── Shells ────────────────────────────────────────────────────────────────────
shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U aintora -d aintora_db

# ─── Dev (without Docker) ────────────────────────────────────────────────────
dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ─── Install ───────────────────────────────────────────────────────────────────
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

# ─── Setup (first time) ───────────────────────────────────────────────────────
setup:
	cp -n .env.example .env || true
	@echo ""
	@echo "════════════════════════════════════════════"
	@echo "  ✅ AINTORA SYSTEMS — Setup Complete"
	@echo "  📝 Edit .env with your credentials"
	@echo "  🚀 Then run: make up-build"
	@echo "════════════════════════════════════════════"
