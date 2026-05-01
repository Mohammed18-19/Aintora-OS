"""
WhatsApp Webhook Handler
Processes incoming messages and drives the conversation state machine.
"""
import structlog
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.customer import Customer
from app.models.booking import Booking, BookingStatus
from app.models.whatsapp_config import WhatsAppConfig
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.intent_parser import parse_intent, match_service
from app.services.booking_service import BookingService
from app.services.availability_service import AvailabilityService
from app.i18n import t, detect_language
import pytz

logger = structlog.get_logger()


class ConversationState:
    IDLE = "idle"
    AWAITING_SERVICE = "awaiting_service"
    AWAITING_DATE = "awaiting_date"
    AWAITING_TIME = "awaiting_time"
    AWAITING_CONFIRM = "awaiting_confirm"
    AWAITING_CANCEL_CONFIRM = "awaiting_cancel_confirm"
    AWAITING_RESCHEDULE_DATE = "awaiting_reschedule_date"
    AWAITING_RESCHEDULE_TIME = "awaiting_reschedule_time"


async def handle_incoming_message(
    tenant: Tenant,
    sender_number: str,
    message_text: str,
    message_id: str,
    db: AsyncSession,
):
    """
    Main entry point for processing an incoming WhatsApp message.
    Resolves or creates the customer, then dispatches by conversation state.
    """
    log = logger.bind(tenant=tenant.slug, sender=sender_number)

    # ── Get or create customer ───────────────────────────────────────────────
    result = await db.execute(
        select(Customer).where(
            Customer.tenant_id == tenant.id,
            Customer.whatsapp_number == sender_number,
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        detected_lang = detect_language(message_text)
        customer = Customer(
            tenant_id=tenant.id,
            whatsapp_number=sender_number,
            preferred_language=detected_lang,
            conversation_state=ConversationState.IDLE,
            conversation_context={},
        )
        db.add(customer)
        await db.flush()
        log.info("new_customer_created", lang=detected_lang)

    if customer.is_blocked:
        log.info("blocked_customer_ignored")
        return

    # ── Get WhatsApp client ──────────────────────────────────────────────────
    wa_config = tenant.whatsapp_config
    if not wa_config:
        log.error("no_whatsapp_config_for_tenant")
        return

    client = WhatsAppClient(wa_config.phone_number_id, wa_config.access_token)

    # Mark message as read
    await client.mark_as_read(message_id)

    lang = customer.preferred_language or tenant.language or "fr"

    # ── Update language detection dynamically ─────────────────────────────────
    detected = detect_language(message_text)
    if detected != lang:
        customer.preferred_language = detected
        lang = detected

    # ── Dispatch by state ────────────────────────────────────────────────────
    state = customer.conversation_state
    ctx = customer.conversation_context or {}

    log.info("message_received", state=state, text=message_text[:50])

    if state == ConversationState.AWAITING_CONFIRM:
        await _handle_confirm_state(customer, tenant, client, message_text, lang, db, ctx)
    elif state == ConversationState.AWAITING_CANCEL_CONFIRM:
        await _handle_cancel_confirm_state(customer, tenant, client, message_text, lang, db, ctx)
    elif state == ConversationState.AWAITING_SERVICE:
        await _handle_service_selection(customer, tenant, client, message_text, lang, db, ctx)
    elif state == ConversationState.AWAITING_DATE:
        await _handle_date_input(customer, tenant, client, message_text, lang, db, ctx)
    elif state == ConversationState.AWAITING_TIME:
        await _handle_time_input(customer, tenant, client, message_text, lang, db, ctx)
    else:
        # IDLE — parse full intent
        intent = parse_intent(message_text, lang)
        await _handle_idle_intent(customer, tenant, client, intent, lang, db, ctx)

    # Persist state changes
    await db.flush()


# ── State Handlers ─────────────────────────────────────────────────────────────

async def _handle_idle_intent(customer, tenant, client, intent, lang, db, ctx):
    """Handle messages when conversation is idle."""
    if intent.intent == "help" or intent.intent == "unknown":
        # Send welcome / menu
        tz = pytz.timezone(tenant.timezone or "Africa/Casablanca")
        await client.send_text(
            customer.whatsapp_number,
            t("greeting", lang, business_name=tenant.name) + "\n\n" +
            t("help_message", lang)
        )
        _set_state(customer, ConversationState.IDLE, {})

    elif intent.intent == "book":
        await _start_booking_flow(customer, tenant, client, intent, lang, db)

    elif intent.intent == "cancel":
        if intent.booking_ref:
            ctx = {"booking_ref": intent.booking_ref}
            await client.send_text(
                customer.whatsapp_number,
                t("cancel_confirm", lang, booking_ref=intent.booking_ref)
            )
            _set_state(customer, ConversationState.AWAITING_CANCEL_CONFIRM, ctx)
        else:
            # Ask for ref
            await client.send_text(
                customer.whatsapp_number,
                "Please provide your booking reference (e.g. BK-2024-000001)"
            )

    elif intent.intent == "status":
        await _handle_status(customer, tenant, client, intent, lang, db)

    else:
        # Try to start booking anyway
        if intent.service_hint or intent.date_obj or intent.time_obj:
            await _start_booking_flow(customer, tenant, client, intent, lang, db)
        else:
            await client.send_text(
                customer.whatsapp_number,
                t("error_not_understood", lang)
            )


async def _start_booking_flow(customer, tenant, client, intent, lang, db):
    """Begin the booking flow, skipping steps where info was already provided."""
    ctx = {}

    # Service
    if intent.service_hint:
        matched = match_service(intent.service_hint, tenant.services)
        if matched:
            ctx["service_id"] = str(matched.id)
            ctx["service_name"] = matched.name
        else:
            # Show service menu
            await _send_service_menu(customer, tenant, client, lang)
            _set_state(customer, ConversationState.AWAITING_SERVICE, ctx)
            return
    else:
        await _send_service_menu(customer, tenant, client, lang)
        _set_state(customer, ConversationState.AWAITING_SERVICE, ctx)
        return

    # Date
    if intent.date_obj:
        ctx["date"] = intent.date_obj.isoformat()
    else:
        await client.send_text(customer.whatsapp_number, t("ask_date", lang))
        _set_state(customer, ConversationState.AWAITING_DATE, ctx)
        return

    # Time
    if intent.time_obj:
        ctx["time"] = intent.time_obj.strftime("%H:%M")
    else:
        await client.send_text(customer.whatsapp_number, t("ask_time", lang))
        _set_state(customer, ConversationState.AWAITING_TIME, ctx)
        return

    # All info collected → confirm
    await _send_booking_confirmation(customer, client, ctx, lang)
    _set_state(customer, ConversationState.AWAITING_CONFIRM, ctx)


async def _send_service_menu(customer, tenant, client, lang):
    services = [s for s in tenant.services if s.is_active]
    if not services:
        await client.send_text(customer.whatsapp_number, "No services available at the moment.")
        return

    services_text = "\n".join(
        f"{i+1}. {s.name} ({s.duration_minutes} min) - {s.price} {s.currency}"
        for i, s in enumerate(services[:10])
    )
    await client.send_text(
        customer.whatsapp_number,
        t("booking_menu", lang, services_list=services_text)
    )


async def _handle_service_selection(customer, tenant, client, message_text, lang, db, ctx):
    services = [s for s in tenant.services if s.is_active]

    # Try numeric selection
    stripped = message_text.strip()
    if stripped.isdigit():
        idx = int(stripped) - 1
        if 0 <= idx < len(services):
            service = services[idx]
            ctx["service_id"] = str(service.id)
            ctx["service_name"] = service.name
            await client.send_text(customer.whatsapp_number, t("ask_date", lang))
            _set_state(customer, ConversationState.AWAITING_DATE, ctx)
            return

    # Try text matching
    matched = match_service(stripped, services)
    if matched:
        ctx["service_id"] = str(matched.id)
        ctx["service_name"] = matched.name
        await client.send_text(customer.whatsapp_number, t("ask_date", lang))
        _set_state(customer, ConversationState.AWAITING_DATE, ctx)
        return

    await _send_service_menu(customer, tenant, client, lang)


async def _handle_date_input(customer, tenant, client, message_text, lang, db, ctx):
    from app.whatsapp.intent_parser import _parse_date
    parsed = _parse_date(message_text)
    if not parsed:
        await client.send_text(customer.whatsapp_number, t("invalid_date", lang))
        return

    ctx["date"] = parsed.isoformat()
    await client.send_text(customer.whatsapp_number, t("ask_time", lang))
    _set_state(customer, ConversationState.AWAITING_TIME, ctx)


async def _handle_time_input(customer, tenant, client, message_text, lang, db, ctx):
    from app.whatsapp.intent_parser import _parse_time
    parsed = _parse_time(message_text)
    if not parsed:
        await client.send_text(customer.whatsapp_number, t("invalid_time", lang))
        return

    ctx["time"] = parsed.strftime("%H:%M")
    await _send_booking_confirmation(customer, client, ctx, lang)
    _set_state(customer, ConversationState.AWAITING_CONFIRM, ctx)


async def _send_booking_confirmation(customer, client, ctx, lang):
    await client.send_text(
        customer.whatsapp_number,
        t(
            "confirm_booking", lang,
            service=ctx.get("service_name", "?"),
            date=ctx.get("date", "?"),
            time=ctx.get("time", "?"),
        )
    )


async def _handle_confirm_state(customer, tenant, client, message_text, lang, db, ctx):
    from app.whatsapp.intent_parser import _CONFIRM_KEYWORDS, _DENY_KEYWORDS

    if _CONFIRM_KEYWORDS.match(message_text.strip()):
        # Create the booking
        booking_svc = BookingService(db)
        booking = await booking_svc.create_from_whatsapp(
            tenant=tenant,
            customer=customer,
            service_id=ctx.get("service_id"),
            date_str=ctx.get("date"),
            time_str=ctx.get("time"),
            raw_message=ctx.get("raw_text", ""),
        )
        await client.send_text(
            customer.whatsapp_number,
            t("booking_pending", lang, booking_ref=booking.booking_ref)
        )
        # Notify owner
        await _notify_owner(tenant, customer, booking, lang, db)
        _set_state(customer, ConversationState.IDLE, {})

    elif _DENY_KEYWORDS.match(message_text.strip()):
        await client.send_text(
            customer.whatsapp_number,
            t("booking_cancelled", lang, booking_ref="")
        )
        _set_state(customer, ConversationState.IDLE, {})
    else:
        await _send_booking_confirmation(customer, client, ctx, lang)


async def _handle_cancel_confirm_state(customer, tenant, client, message_text, lang, db, ctx):
    from app.whatsapp.intent_parser import _CONFIRM_KEYWORDS
    if _CONFIRM_KEYWORDS.match(message_text.strip()):
        ref = ctx.get("booking_ref")
        booking_svc = BookingService(db)
        success = await booking_svc.cancel_by_ref(ref, tenant.id)
        if success:
            await client.send_text(
                customer.whatsapp_number,
                t("cancel_success", lang, booking_ref=ref)
            )
        else:
            await client.send_text(customer.whatsapp_number, "Booking not found.")
        _set_state(customer, ConversationState.IDLE, {})
    else:
        await client.send_text(customer.whatsapp_number, t("help_message", lang))
        _set_state(customer, ConversationState.IDLE, {})


async def _handle_status(customer, tenant, client, intent, lang, db):
    booking_svc = BookingService(db)
    if intent.booking_ref:
        booking = await booking_svc.get_by_ref(intent.booking_ref, tenant.id)
        if booking:
            msg = f"📋 Booking {booking.booking_ref}\nStatus: {booking.status}\n📅 {booking.scheduled_at.strftime('%d/%m/%Y %H:%M')}"
            await client.send_text(customer.whatsapp_number, msg)
            return
    await client.send_text(customer.whatsapp_number, "Please provide your booking reference (e.g. BK-2024-000001)")


async def _notify_owner(tenant, customer, booking, lang, db):
    wa_config = tenant.whatsapp_config
    if not wa_config or not wa_config.owner_whatsapp:
        return

    client = WhatsAppClient(wa_config.phone_number_id, wa_config.access_token)
    dashboard_url = f"https://app.aintora.com/bookings/{booking.id}"

    await client.send_text(
        wa_config.owner_whatsapp,
        t(
            "owner_new_booking", lang,
            customer_name=customer.name or "Customer",
            customer_number=customer.whatsapp_number,
            service=booking.service.name if booking.service else "Service",
            date=booking.scheduled_at.strftime("%d/%m/%Y"),
            time=booking.scheduled_at.strftime("%H:%M"),
            dashboard_url=dashboard_url,
        )
    )


def _set_state(customer: Customer, state: str, ctx: dict):
    customer.conversation_state = state
    customer.conversation_context = ctx
