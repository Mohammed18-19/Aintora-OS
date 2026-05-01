"""
Rule-based NLP intent parser for WhatsApp messages.
No paid AI required — works with regex + keyword matching.
Supports: English, French, Arabic, Darija, Arabizi
"""
import re
from datetime import date, datetime, timedelta, time
from typing import Optional
from dataclasses import dataclass, field
import pytz

CASABLANCA_TZ = pytz.timezone("Africa/Casablanca")


@dataclass
class ParsedIntent:
    intent: str = "unknown"            # book, cancel, reschedule, status, help, confirm, deny, greeting
    service_hint: Optional[str] = None # raw text hint for service matching
    date_obj: Optional[date] = None
    time_obj: Optional[time] = None
    booking_ref: Optional[str] = None
    language: Optional[str] = None
    confidence: float = 0.0
    raw_text: str = ""


# ─── Intent keyword maps ───────────────────────────────────────────────────────
_BOOK_KEYWORDS = re.compile(
    r"\b(book|réserver|reserver|حجز|nrdja3|nrdja|rendez.?vous|appointment|rdv|prendre|"
    r"résa|réservation|bghit|bghitek|nréserva|réserve|كيف|موعد|حابب|bghi|حجز)\b",
    re.IGNORECASE | re.UNICODE,
)

_CANCEL_KEYWORDS = re.compile(
    r"\b(cancel|annuler|إلغاء|lgha|tlghi|tlgha|lghi|annulation|إلغي|الغاء|annule|lghit)\b",
    re.IGNORECASE | re.UNICODE,
)

_RESCHEDULE_KEYWORDS = re.compile(
    r"\b(reschedule|reprogrammer|إعادة|3awd|t3awd|3awdni|changer|modifier|تغيير|جدولة|modifie|naqel)\b",
    re.IGNORECASE | re.UNICODE,
)

_STATUS_KEYWORDS = re.compile(
    r"\b(status|statut|حالة|wach|état|wach kayn|confirmation|confirm|infos?|détails?)\b",
    re.IGNORECASE | re.UNICODE,
)

_HELP_KEYWORDS = re.compile(
    r"\b(help|aide|مساعدة|mosa3da|3awdni|comment|kif|كيف|start|menu|options|bonjour|hello|مرحبا|مرحباً|salam|salut|hi)\b",
    re.IGNORECASE | re.UNICODE,
)

_CONFIRM_KEYWORDS = re.compile(
    r"^(yes|oui|نعم|iya|iwa|wah|okay|ok|confirm|d'accord|mzyan|iyah|ayeh|sim|نعم|yep|yup|absolument)[\s!.]*$",
    re.IGNORECASE | re.UNICODE,
)

_DENY_KEYWORDS = re.compile(
    r"^(no|non|لا|la|laa|nope|pas|cancel|annuler|lgha|nein|kher|lghi)[\s!.]*$",
    re.IGNORECASE | re.UNICODE,
)

_BOOKING_REF = re.compile(r"\bBK-\d{4}-\d+\b", re.IGNORECASE)


# ─── Date parsing ─────────────────────────────────────────────────────────────
_TODAY_PATTERN = re.compile(
    r"\b(today|aujourd'hui|اليوم|lyoum|ce soir|maintenant)\b", re.IGNORECASE | re.UNICODE
)
_TOMORROW_PATTERN = re.compile(
    r"\b(tomorrow|demain|غداً|غدا|ghda|gheda)\b", re.IGNORECASE | re.UNICODE
)
_DAY_AFTER_PATTERN = re.compile(
    r"\b(day after tomorrow|après-demain|بعد غد|b3d ghda)\b", re.IGNORECASE | re.UNICODE
)

_WEEKDAY_MAP = {
    # English
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    # French
    "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3,
    "vendredi": 4, "samedi": 5, "dimanche": 6,
    # Arabic
    "الاثنين": 0, "الثلاثاء": 1, "الأربعاء": 2, "الخميس": 3,
    "الجمعة": 4, "السبت": 5, "الأحد": 6,
    # Darija
    "ltnin": 0, "lhad": 6, "ljm3a": 4, "lkhmis": 3, "lkhmees": 3,
}

_DATE_FORMATS = [
    r"(\d{1,2})[/\-\.](\d{1,2})(?:[/\-\.](\d{2,4}))?",  # DD/MM or DD/MM/YYYY
]

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}

# ─── Time parsing ─────────────────────────────────────────────────────────────
_TIME_PATTERN = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(?:(am|pm|AM|PM|h|H))?"
)


def _parse_date(text: str) -> Optional[date]:
    today = datetime.now(CASABLANCA_TZ).date()

    if _TODAY_PATTERN.search(text):
        return today
    if _DAY_AFTER_PATTERN.search(text):
        return today + timedelta(days=2)
    if _TOMORROW_PATTERN.search(text):
        return today + timedelta(days=1)

    # Named weekdays
    for day_name, day_num in _WEEKDAY_MAP.items():
        if re.search(r"\b" + re.escape(day_name) + r"\b", text, re.IGNORECASE | re.UNICODE):
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

    # DD/MM or DD/MM/YYYY
    for pattern in _DATE_FORMATS:
        m = re.search(pattern, text)
        if m:
            try:
                day, month = int(m.group(1)), int(m.group(2))
                year = int(m.group(3)) if m.group(3) else today.year
                if year < 100:
                    year += 2000
                return date(year, month, day)
            except (ValueError, TypeError):
                continue

    return None


def _parse_time(text: str) -> Optional[time]:
    # Look for "at X", "à X", "f X", "f waqt X"
    for m in _TIME_PATTERN.finditer(text):
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)

        if ampm:
            if ampm.lower() == "pm" and hour != 12:
                hour += 12
            elif ampm.lower() == "am" and hour == 12:
                hour = 0

        # Sanity check
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            # Treat hours like 1-7 without AM/PM as afternoon in a salon context
            if not ampm and 1 <= hour <= 7:
                hour += 12
            return time(hour, minute)

    return None


def _extract_service_hint(text: str) -> Optional[str]:
    """Extract possible service name from the message."""
    # Remove intent keywords and date/time, return remainder as hint
    clean = text.lower()
    for pattern in [
        _BOOK_KEYWORDS, _CANCEL_KEYWORDS, _RESCHEDULE_KEYWORDS,
        _HELP_KEYWORDS, _STATUS_KEYWORDS,
        _TOMORROW_PATTERN, _TODAY_PATTERN, _TIME_PATTERN,
    ]:
        clean = pattern.sub("", clean)
    clean = re.sub(r"\b(for|pour|pour un|une|un|le|la|les|a|an|the|je veux|i want|bghit)\b", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean if len(clean) > 1 else None


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_intent(text: str, language: str = "fr") -> ParsedIntent:
    """
    Main entry point: parse a raw WhatsApp message into a structured intent.
    """
    result = ParsedIntent(raw_text=text, language=language)

    if not text or not text.strip():
        result.intent = "unknown"
        return result

    stripped = text.strip()

    # Booking ref extraction (works for any intent)
    ref_match = _BOOKING_REF.search(text)
    if ref_match:
        result.booking_ref = ref_match.group(0).upper()

    # Intent classification (order matters)
    if _CONFIRM_KEYWORDS.match(stripped):
        result.intent = "confirm"
        result.confidence = 0.95
    elif _DENY_KEYWORDS.match(stripped):
        result.intent = "deny"
        result.confidence = 0.95
    elif _CANCEL_KEYWORDS.search(text):
        result.intent = "cancel"
        result.confidence = 0.85
    elif _RESCHEDULE_KEYWORDS.search(text):
        result.intent = "reschedule"
        result.confidence = 0.85
    elif _STATUS_KEYWORDS.search(text):
        result.intent = "status"
        result.confidence = 0.80
    elif _HELP_KEYWORDS.search(text):
        result.intent = "help"
        result.confidence = 0.80
    elif _BOOK_KEYWORDS.search(text):
        result.intent = "book"
        result.confidence = 0.85
    else:
        # Fallback: if date or time is found, assume booking intent
        parsed_date = _parse_date(text)
        parsed_time = _parse_time(text)
        if parsed_date or parsed_time:
            result.intent = "book"
            result.confidence = 0.65
        else:
            result.intent = "unknown"
            result.confidence = 0.2

    # Extract date and time for booking-related intents
    if result.intent in ("book", "reschedule"):
        result.date_obj = _parse_date(text)
        result.time_obj = _parse_time(text)
        result.service_hint = _extract_service_hint(text)

    return result


def match_service(hint: Optional[str], services: list) -> Optional[object]:
    """
    Match a service hint to the closest service in the tenant's service list.
    `services` is a list of Service ORM objects.
    """
    if not hint or not services:
        return None

    hint_lower = hint.lower()

    for service in services:
        # Check main name
        if service.name.lower() in hint_lower or hint_lower in service.name.lower():
            return service
        # Check aliases from nlp_aliases field
        aliases = service.nlp_aliases or []
        for alias in aliases:
            if alias.lower() in hint_lower or hint_lower in alias.lower():
                return service
        # Check translated names
        translations = service.name_translations or {}
        for _, translated_name in translations.items():
            if translated_name.lower() in hint_lower or hint_lower in translated_name.lower():
                return service

    return None
