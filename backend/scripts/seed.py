#!/usr/bin/env python3
"""
Seed script — run once after migrations to bootstrap the platform.
Creates:
  - Super admin account (YOU)
  - Demo tenant: Salon Nour
  - Sample services
  - Business hours
  - Sample WhatsApp config (placeholder)

Usage:
  cd backend
  python scripts/seed.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.security import hash_password
from app.models.tenant import Tenant, BusinessType, SubscriptionPlan
from app.models.user import User, UserRole
from app.models.service import Service
from app.models.business_hours import BusinessHours
from app.models.whatsapp_config import WhatsAppConfig
from app.models.customer import Customer
from app.models.booking import Booking, BookingStatus, BookingSource
from datetime import time, datetime, timedelta
import pytz
import uuid

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with SessionLocal() as db:
        print("🌱 Starting database seed...")

        # ── 1. Super Admin ────────────────────────────────────────────────────
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == settings.SUPER_ADMIN_EMAIL))
        if existing.scalar_one_or_none():
            print("⚠️  Super admin already exists, skipping.")
        else:
            super_admin = User(
                email=settings.SUPER_ADMIN_EMAIL,
                full_name="Mohammed – AINTORA",
                hashed_password=hash_password(settings.SUPER_ADMIN_PASSWORD),
                role=UserRole.super_admin,
                is_active=True,
                is_email_verified=True,
                tenant_id=None,
            )
            db.add(super_admin)
            await db.flush()
            print(f"✅ Super admin created: {settings.SUPER_ADMIN_EMAIL}")

        # ── 2. Demo Tenant: Salon Nour ────────────────────────────────────────
        existing_tenant = await db.execute(select(Tenant).where(Tenant.slug == "salon-nour"))
        tenant = existing_tenant.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                name="Salon Nour",
                slug="salon-nour",
                email="nour@salon-nour.ma",
                phone="+212600000001",
                business_type=BusinessType.salon,
                plan=SubscriptionPlan.free,
                city="Casablanca",
                country="MA",
                timezone="Africa/Casablanca",
                language="fr",
                is_active=True,
                is_verified=True,
                primary_color="#c9a96e",
            )
            db.add(tenant)
            await db.flush()
            print(f"✅ Demo tenant created: {tenant.name} (slug: {tenant.slug})")

            # ── Owner user ────────────────────────────────────────────────────
            owner = User(
                tenant_id=tenant.id,
                email="owner@salon-nour.ma",
                full_name="Nour El Houda",
                hashed_password=hash_password("SalonNour2024!"),
                role=UserRole.owner,
                is_active=True,
                is_email_verified=True,
            )
            db.add(owner)
            print(f"✅ Owner user: owner@salon-nour.ma / SalonNour2024!")

            # ── Services ──────────────────────────────────────────────────────
            services_data = [
                {
                    "name": "Coupe Femme",
                    "duration_minutes": 60,
                    "price": 150,
                    "category": "hair",
                    "name_translations": {"ar": "قص شعر نسائي", "en": "Women's Haircut", "darija": "Coupe dial lbniya"},
                    "nlp_aliases": ["coupe", "haircut", "قص", "couper", "قصة", "coiffe", "coiffure", "kupe", "wlida"],
                },
                {
                    "name": "Coupe Homme",
                    "duration_minutes": 30,
                    "price": 80,
                    "category": "hair",
                    "name_translations": {"ar": "قص شعر رجالي", "en": "Men's Haircut", "darija": "Coupe dial rajel"},
                    "nlp_aliases": ["coupe homme", "men haircut", "رجالي", "rajel", "masculin", "gars"],
                },
                {
                    "name": "Coloration",
                    "duration_minutes": 120,
                    "price": 350,
                    "category": "hair",
                    "name_translations": {"ar": "صباغة", "en": "Hair Coloring", "darija": "Sbagha"},
                    "nlp_aliases": ["couleur", "coloration", "color", "تلوين", "صباغة", "sbagha", "teinture", "balayage"],
                },
                {
                    "name": "Soin Kératine",
                    "duration_minutes": 180,
                    "price": 600,
                    "category": "treatment",
                    "name_translations": {"ar": "علاج الكيراتين", "en": "Keratin Treatment", "darija": "Kératine"},
                    "nlp_aliases": ["keratin", "كيراتين", "lissage", "liss", "soin"],
                },
                {
                    "name": "Manucure",
                    "duration_minutes": 45,
                    "price": 120,
                    "category": "nails",
                    "name_translations": {"ar": "عناية بالأظافر", "en": "Manicure", "darija": "Manucure"},
                    "nlp_aliases": ["manicure", "ongles", "أظافر", "dfer", "vernis", "gel nails"],
                },
            ]

            created_services = []
            for svc_data in services_data:
                svc = Service(tenant_id=tenant.id, **svc_data, is_active=True)
                db.add(svc)
                created_services.append(svc)
            await db.flush()
            print(f"✅ {len(services_data)} services created")

            # ── Business Hours (Mon–Sat 9:00–19:00, Sun closed) ────────────────
            for day in range(6):
                db.add(BusinessHours(
                    tenant_id=tenant.id,
                    day_of_week=day,
                    is_open=True,
                    opens_at=time(9, 0),
                    closes_at=time(19, 0),
                    break_starts_at=time(13, 0) if day < 5 else None,
                    break_ends_at=time(14, 0) if day < 5 else None,
                ))
            db.add(BusinessHours(tenant_id=tenant.id, day_of_week=6, is_open=False))
            print("✅ Business hours seeded")

            # ── WhatsApp Config (placeholder) ─────────────────────────────────
            import secrets
            wa_config = WhatsAppConfig(
                tenant_id=tenant.id,
                phone_number_id="REPLACE_WITH_YOUR_PHONE_NUMBER_ID",
                access_token="REPLACE_WITH_YOUR_META_ACCESS_TOKEN",
                owner_whatsapp="212600000001",
                waba_id="REPLACE_WITH_WABA_ID",
                verify_token=secrets.token_urlsafe(16),
                is_active=True,
                welcome_message="Bienvenue chez Salon Nour! 💄",
            )
            db.add(wa_config)
            await db.flush()
            print(f"✅ WhatsApp config created (verify_token: {wa_config.verify_token})")

            # ── Sample Customer ────────────────────────────────────────────────
            tz = pytz.timezone("Africa/Casablanca")
            customer = Customer(
                tenant_id=tenant.id,
                whatsapp_number="212601234567",
                name="Fatima Zahra",
                preferred_language="fr",
                total_bookings=2,
            )
            db.add(customer)
            await db.flush()

            # ── Sample Bookings ────────────────────────────────────────────────
            await db.flush()
            b1 = Booking(
                tenant_id=tenant.id,
                customer_id=customer.id,
                service_id=created_services[0].id,
                booking_ref="BK-2024-000001",
                status="confirmed",
                source="whatsapp",
                scheduled_at=tz.localize(datetime.now() + timedelta(days=1, hours=2)),
                duration_minutes="60",
                raw_message="Je veux une coupe demain à 11h",
            )
            b2 = Booking(
                tenant_id=tenant.id,
                customer_id=customer.id,
                service_id=created_services[2].id,
                booking_ref="BK-2024-000002",
                status="pending",
                source="whatsapp",
                scheduled_at=tz.localize(datetime.now() + timedelta(days=2, hours=3)),
                duration_minutes="120",
                raw_message="Coloration samedi à 14h stp",
            )
            db.add(b1)
            db.add(b2)
            print("✅ Sample bookings created")

        await db.commit()
        print("\n🎉 Seed complete!")
        print("=" * 50)
        print(f"  Super Admin: {settings.SUPER_ADMIN_EMAIL}")
        print(f"  Password:    {settings.SUPER_ADMIN_PASSWORD}")
        print(f"  Demo owner:  owner@salon-nour.ma / SalonNour2024!")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
