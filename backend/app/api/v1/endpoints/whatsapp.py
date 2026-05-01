"""
WhatsApp Cloud API webhook endpoint.
- GET: Meta verification handshake
- POST: Incoming messages from customers
"""
import hmac
import hashlib
import structlog
from fastapi import APIRouter, Request, Response, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.whatsapp_config import WhatsAppConfig
from app.whatsapp.webhook_handler import handle_incoming_message

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])
logger = structlog.get_logger()

@router.get("/")
async def verify_webhook_global(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Single global webhook verification for Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/")
async def receive_message_global(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Single global webhook — routes to tenant by phone_number_id."""
    body_bytes = await request.body()
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        phone_number_id = value.get("metadata", {}).get("phone_number_id")
        messages = value.get("messages", [])
    except (IndexError, KeyError, AttributeError):
        return {"status": "no_messages"}

    if not phone_number_id or not messages:
        return {"status": "ok"}

    # Find tenant by phone_number_id
    from app.models.whatsapp_config import WhatsAppConfig
    result = await db.execute(
        select(Tenant)
        .join(WhatsAppConfig, WhatsAppConfig.tenant_id == Tenant.id)
        .where(
            WhatsAppConfig.phone_number_id == phone_number_id,
            Tenant.is_active == True,
        )
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"status": "tenant_not_found"}

    for msg in messages:
        msg_type = msg.get("type")
        sender = msg.get("from")
        message_id = msg.get("id")
        if not sender or not message_id:
            continue
        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text = interactive["button_reply"].get("title", "")
            elif interactive.get("type") == "list_reply":
                text = interactive["list_reply"].get("title", "")
            else:
                text = ""
        else:
            continue
        if text:
            await handle_incoming_message(
                tenant=tenant,
                sender_number=sender,
                message_text=text,
                message_id=message_id,
                db=db,
            )

    return {"status": "ok"}


@router.get("/{tenant_slug}")
async def verify_webhook(
    tenant_slug: str,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Meta webhook verification handshake.
    Meta sends GET with hub.challenge; we must echo it back.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_slug)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    wa_config = tenant.whatsapp_config
    expected_token = (
        wa_config.verify_token if wa_config else settings.META_VERIFY_TOKEN
    )

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("webhook_verified", tenant=tenant_slug)
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("webhook_verify_failed", tenant=tenant_slug, token=hub_verify_token)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/{tenant_slug}")
async def receive_message(
    tenant_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive incoming WhatsApp messages for a specific tenant.
    """
    body_bytes = await request.body()

    # ── Signature verification (only when META_APP_SECRET is set in production) ──
    if settings.META_APP_SECRET and settings.DEBUG is False:
        sig_header = request.headers.get("x-hub-signature-256", "")
        expected_sig = "sha256=" + hmac.new(
            settings.META_APP_SECRET.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected_sig):
            logger.warning("webhook_signature_invalid", tenant=tenant_slug)
            raise HTTPException(status_code=403, detail="Invalid signature")

    # ── Load tenant ──────────────────────────────────────────────────────────
    result = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        # Return 200 so Meta doesn't retry; just silently ignore
        return {"status": "ignored"}

    # ── Parse webhook payload ────────────────────────────────────────────────
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # ── Extract messages ─────────────────────────────────────────────────────
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
    except (IndexError, KeyError, AttributeError):
        return {"status": "no_messages"}

    for msg in messages:
        msg_type = msg.get("type")
        sender = msg.get("from")
        message_id = msg.get("id")

        if not sender or not message_id:
            continue

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
        elif msg_type == "interactive":
            # Button reply or list reply
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text = interactive["button_reply"].get("title", "")
            elif interactive.get("type") == "list_reply":
                text = interactive["list_reply"].get("title", "")
            else:
                text = ""
        else:
            # Unsupported message type (image, voice, etc.)
            logger.info("unsupported_message_type", type=msg_type, tenant=tenant_slug)
            continue

        if text:
            logger.info("processing_message", tenant=tenant_slug, sender=sender, type=msg_type)
            await handle_incoming_message(
                tenant=tenant,
                sender_number=sender,
                message_text=text,
                message_id=message_id,
                db=db,
            )

    # Always return 200 to Meta
    return {"status": "ok"}