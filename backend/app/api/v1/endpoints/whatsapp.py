"""
WhatsApp Cloud API webhook endpoint.
- GET /webhook         : Global Meta verification (one for all businesses)
- POST /webhook        : Global incoming messages (routes by phone_number_id)
- GET /webhook/{slug}  : Per-tenant verification (legacy/testing)
- POST /webhook/{slug} : Per-tenant messages (legacy/testing)
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


# ─── GLOBAL WEBHOOK (Production — one URL for all businesses) ─────────────────

@router.get("")
@router.get("/")
async def verify_webhook_global(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Global Meta webhook verification — set this URL once in Meta.
    Verify token = META_VERIFY_TOKEN in .env
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("global_webhook_verified")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning("global_webhook_verify_failed", token=hub_verify_token)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
@router.post("/")
async def receive_message_global(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Global incoming messages — routes to correct tenant by phone_number_id.
    Meta sends ALL messages here. System finds the right business automatically.
    """
    try:
        data = await request.json()
    except Exception:
        return {"status": "ok"}

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        phone_number_id = value.get("metadata", {}).get("phone_number_id")
        messages = value.get("messages", [])
    except Exception:
        return {"status": "ok"}

    if not phone_number_id or not messages:
        return {"status": "ok"}

    # Find tenant by phone_number_id
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
        logger.warning("global_webhook_tenant_not_found", phone_number_id=phone_number_id)
        return {"status": "ok"}

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
            logger.info("global_message_received", tenant=tenant.slug, sender=sender)
            await handle_incoming_message(
                tenant=tenant,
                sender_number=sender,
                message_text=text,
                message_id=message_id,
                db=db,
            )

    return {"status": "ok"}


# ─── PER-TENANT WEBHOOK (for local testing with curl) ─────────────────────────

@router.get("/{tenant_slug}")
async def verify_webhook(
    tenant_slug: str,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_slug)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("tenant_webhook_verified", tenant=tenant_slug)
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/{tenant_slug}")
async def receive_message(
    tenant_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body_bytes = await request.body()

    # Signature verification (production only)
    if settings.META_APP_SECRET and settings.DEBUG is False:
        sig_header = request.headers.get("x-hub-signature-256", "")
        expected_sig = "sha256=" + hmac.new(
            settings.META_APP_SECRET.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected_sig):
            raise HTTPException(status_code=403, detail="Invalid signature")

    result = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"status": "ignored"}

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
    except Exception:
        return {"status": "ok"}

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
            logger.info("tenant_message_received", tenant=tenant_slug, sender=sender)
            await handle_incoming_message(
                tenant=tenant,
                sender_number=sender,
                message_text=text,
                message_id=message_id,
                db=db,
            )

    return {"status": "ok"}