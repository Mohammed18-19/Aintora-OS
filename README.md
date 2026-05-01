# 🤖 AINTORA SYSTEMS — WhatsApp Booking SaaS

> Multi-tenant WhatsApp-first booking automation platform for salons, clinics, spas and service businesses.
> Built by Mohammed — AINTORA SYSTEMS 🇲🇦

---

## 🏗️ Architecture Overview

```
aintora-saas/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints
│   │   │   └── endpoints/
│   │   │       ├── auth.py           # Login, register, JWT
│   │   │       ├── bookings.py       # Booking CRUD + actions
│   │   │       ├── whatsapp.py       # Meta webhook (GET verify + POST messages)
│   │   │       ├── admin.py          # Super admin routes
│   │   │       └── settings.py       # Services, staff, hours, WhatsApp config
│   │   ├── core/
│   │   │   ├── config.py             # All env variables via pydantic-settings
│   │   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   │   ├── security.py           # JWT + bcrypt
│   │   │   └── dependencies.py       # FastAPI Depends() injectors
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── tenant.py             # Core multi-tenancy model
│   │   │   ├── user.py               # Users with role system
│   │   │   ├── customer.py           # WhatsApp customers + conversation state
│   │   │   ├── booking.py            # Bookings with full status machine
│   │   │   ├── service.py            # Bookable services with NLP aliases
│   │   │   ├── staff.py              # Staff members
│   │   │   ├── business_hours.py     # Per-day opening hours
│   │   │   ├── whatsapp_config.py    # Per-tenant Meta credentials
│   │   │   └── notification_log.py   # Every message sent/received
│   │   ├── services/
│   │   │   ├── booking_service.py    # Business logic: create, confirm, cancel...
│   │   │   └── availability_service.py # Slot availability checking
│   │   ├── whatsapp/
│   │   │   ├── client.py             # Meta Cloud API HTTP client
│   │   │   ├── intent_parser.py      # Rules-based NLP (no paid AI needed)
│   │   │   └── webhook_handler.py    # Conversation state machine
│   │   └── i18n/                     # Translations
│   │       ├── en.json               # English
│   │       ├── fr.json               # French
│   │       ├── ar.json               # Arabic
│   │       └── darija.json           # Moroccan Darija + Arabizi
│   ├── alembic/                      # Database migrations
│   ├── scripts/
│   │   └── seed.py                   # Bootstrap super admin + demo tenant
│   ├── main.py                       # FastAPI app entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React + TypeScript dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardHome.tsx     # Stats, charts, recent bookings
│   │   │   ├── BookingsPage.tsx      # Full booking table + confirm/reject
│   │   │   ├── BookingDetailPage.tsx # Single booking with all actions
│   │   │   ├── ServicesPage.tsx      # Service CRUD with NLP aliases
│   │   │   ├── SettingsPage.tsx      # WhatsApp config + business hours
│   │   │   └── AdminPage.tsx         # Super admin tenant management
│   │   ├── components/layout/
│   │   │   └── DashboardLayout.tsx   # Sidebar + main layout
│   │   ├── services/api.ts           # Axios client + all API calls
│   │   └── store/authStore.ts        # Zustand auth state
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml        # Full production stack
├── docker-compose.dev.yml    # Development overrides
└── .env.example              # All environment variables documented
```

---

## ⚡ Quick Start (5 minutes)

### Prerequisites
- Docker Desktop installed
- Git

### Step 1: Clone & Configure

```bash
git clone https://github.com/Mohammed18-19/aintora-saas.git
cd aintora-saas

# Copy and edit your environment file
cp .env.example .env
nano .env   # or: code .env
```

**Minimum required changes in `.env`:**
```bash
SECRET_KEY=generate_a_random_64_char_string_here
SUPER_ADMIN_EMAIL=your@email.com
SUPER_ADMIN_PASSWORD=a_strong_password
```

### Step 2: Launch Everything

```bash
docker compose up --build
```

This will:
1. Start PostgreSQL
2. Run Alembic migrations automatically
3. Seed the database (super admin + Salon Nour demo)
4. Start the FastAPI backend on :8000
5. Build and serve the React frontend on :3000

### Step 3: Open the Dashboard

```
Frontend:  http://localhost:3000
API Docs:  http://localhost:8000/docs  (DEBUG mode only)
```

**Login credentials after seed:**
```
Super Admin:  admin@aintora.com  /  change_me_immediately_admin_2024!
Demo Owner:   owner@salon-nour.ma  /  SalonNour2024!
```

> ⚠️ **Change all default passwords immediately after first login!**

---

## 📱 WhatsApp Setup (Per Business)

After a business registers, they must configure their Meta credentials:

### Step 1: Create a Meta App

1. Go to https://developers.facebook.com
2. Create a new app → Business type
3. Add WhatsApp product
4. Copy your **Phone Number ID** and **Access Token**

### Step 2: Configure in Dashboard

1. Log in as business owner
2. Go to **Settings → WhatsApp**
3. Enter your Phone Number ID and Access Token
4. Click **Save Configuration**
5. You'll get a **Webhook URL** and **Verify Token**

### Step 3: Register the Webhook in Meta

1. In Meta Developer Console → WhatsApp → Configuration → Webhooks
2. Set Callback URL to: `https://your-domain.com/api/v1/webhook/your-slug`
3. Set Verify Token to the one shown in dashboard
4. Subscribe to `messages` field

### Step 4: Test!

Send a WhatsApp message to your test number:
```
"Je veux réserver une coupe demain à 10h"
```

The bot should respond automatically!

---

## 🌍 Supported Languages

The bot auto-detects language from message content:

| Language | Code | Detection |
|----------|------|-----------|
| French | `fr` | Keywords: bonjour, réserver, demain... |
| Arabic | `ar` | Arabic Unicode script (ء-ي) |
| Darija | `darija` | Dialect keywords: mrhba, bghi, ghda... |
| English | `en` | Keywords: hello, book, tomorrow... |

To change default language per business, update `tenant.language` in the DB.

---

## 🗣️ NLP Intent System

The bot understands these intents (no paid AI needed):

| Intent | Example messages |
|--------|-----------------|
| `book` | "Je veux réserver", "I want to book", "بغيت نحجز" |
| `cancel` | "annuler", "cancel", "الغاء", "lgha" |
| `reschedule` | "reprogrammer", "changer", "t3awd" |
| `status` | "statut", "status", "حالة" |
| `confirm` | "oui", "yes", "iya", "نعم" |
| `deny` | "non", "no", "la", "لا" |
| `help` | "bonjour", "hello", "salam", "مرحبا" |

**Adding service aliases:**
When creating services, add NLP aliases to help matching:
```json
nlp_aliases: ["coupe", "haircut", "قص", "coiffe", "kupe", "wlida"]
```

---

## 🏗️ Multi-Tenancy Design

Each business is a **Tenant** with:
- Isolated data via `tenant_id` foreign key on all tables
- Separate WhatsApp credentials (phone number ID + token)
- Separate services, staff, business hours
- Unique webhook URL: `/api/v1/webhook/{slug}`
- Own language preference

Database isolation: Row-Level via `tenant_id` filter. All queries are scoped.

---

## 🔐 User Roles

| Role | Access |
|------|--------|
| `super_admin` | Full platform access, all tenants |
| `owner` | Own tenant only: all features |
| `staff` | Own tenant: view bookings |
| `viewer` | Own tenant: read-only |

---

## 📊 API Reference

### Auth
```
POST /api/v1/auth/login          Login → JWT token
POST /api/v1/auth/register       Register new business
GET  /api/v1/auth/me             Current user info
```

### Bookings
```
GET    /api/v1/bookings/           List bookings (filterable)
GET    /api/v1/bookings/stats      Booking counts by status
GET    /api/v1/bookings/{id}       Booking details
POST   /api/v1/bookings/{id}/confirm
POST   /api/v1/bookings/{id}/reject
POST   /api/v1/bookings/{id}/cancel
POST   /api/v1/bookings/{id}/reschedule
```

### Settings
```
GET/POST  /api/v1/services/        Service CRUD
GET/POST  /api/v1/staff/           Staff CRUD
GET/PUT   /api/v1/business-hours/  Business hours
GET/POST  /api/v1/whatsapp-config/ WhatsApp credentials
```

### WhatsApp Webhook
```
GET  /api/v1/webhook/{slug}    Meta verification
POST /api/v1/webhook/{slug}    Incoming messages
```

### Super Admin
```
GET   /api/v1/admin/tenants              All businesses
GET   /api/v1/admin/tenants/{id}         Tenant details
POST  /api/v1/admin/tenants/{id}/activate
POST  /api/v1/admin/tenants/{id}/deactivate
GET   /api/v1/admin/stats/platform       Platform KPIs
```

---

## 🚀 Production Deployment

### Railway (Recommended — same as your chatbot-saas)

```bash
# Backend
railway up --service backend

# Add env vars in Railway dashboard
# Set DATABASE_URL to Railway PostgreSQL URL

# Frontend: deploy to Vercel or Netlify
```

### Manual VPS

```bash
# 1. Point domain to your server
# 2. Install Docker
# 3. Clone repo, fill .env
# 4. docker compose up -d
# 5. Set up HTTPS with Certbot + Nginx reverse proxy
```

---

## 💸 Future Monetization (Architecture Ready)

The codebase already has:
- `tenant.plan` field (free / starter / professional / enterprise)
- `tenant.stripe_customer_id` and `tenant.stripe_subscription_id`
- Subscription plan enum

To add Stripe:
1. Add `stripe` to requirements.txt
2. Create `/api/v1/billing/` endpoints
3. Add webhook for `customer.subscription.updated`
4. Gate features by `tenant.plan`

---

## 🔧 Development Without Docker

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL locally or via Docker:
docker run -d -p 5432:5432 -e POSTGRES_DB=aintora_db -e POSTGRES_USER=aintora -e POSTGRES_PASSWORD=aintora_pass postgres:16

# Copy and fill env
cp ../.env.example .env

# Migrations
alembic upgrade head

# Seed
python scripts/seed.py

# Run
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens on http://localhost:3000
```

---

## 🛠️ Useful Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Reset database (DANGER: deletes all data)
docker compose down -v
docker compose up --build

# Run only backend + postgres
docker compose up postgres backend

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "add_field"

# Run migrations manually
docker compose exec backend alembic upgrade head

# Open psql
docker compose exec postgres psql -U aintora -d aintora_db
```

---

## 📞 Support

Built and maintained by **Mohammed — AINTORA SYSTEMS**
- GitHub: https://github.com/Mohammed18-19
- Email: aintomar.mohamed19@gmail.com

---

*🤖 Powered by AINTORA SYSTEMS — WhatsApp booking automation for Morocco and the Arab world*
