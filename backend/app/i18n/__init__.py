import json
import re
from pathlib import Path
from typing import Optional

_TRANSLATIONS: dict[str, dict] = {}
_I18N_DIR = Path(__file__).parent

SUPPORTED_LANGUAGES = ["en", "fr", "ar", "darija"]
DEFAULT_LANGUAGE = "fr"

# Language detection patterns
_LANG_PATTERNS = {
    "ar": re.compile(r"[\u0600-\u06FF]"),           # Arabic Unicode range
    "darija": re.compile(                             # Darija / Arabizi keywords
        r"\b(mrhba|wach|iyah|llah|ghda|3awdni|nta|nti|mghrb|bghit|bghitek|smhli|mzyan|had|dyal)\b",
        re.IGNORECASE,
    ),
    "fr": re.compile(
        r"\b(bonjour|bonsoir|merci|oui|non|réserver|annuler|demain|lundi|mardi|jeudi)\b",
        re.IGNORECASE,
    ),
    "en": re.compile(
        r"\b(hello|hi|book|cancel|appointment|tomorrow|monday|tuesday|please|yes|no)\b",
        re.IGNORECASE,
    ),
}


def _load_translations():
    for lang in SUPPORTED_LANGUAGES:
        path = _I18N_DIR / f"{lang}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _TRANSLATIONS[lang] = json.load(f)


_load_translations()


def t(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Translate a key to the given language with optional format variables.
    Falls back to French, then English.
    """
    lang = lang if lang in _TRANSLATIONS else DEFAULT_LANGUAGE
    translations = _TRANSLATIONS.get(lang, _TRANSLATIONS.get(DEFAULT_LANGUAGE, {}))
    fallback = _TRANSLATIONS.get("en", {})

    template = translations.get(key) or fallback.get(key) or key

    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template


def detect_language(text: str) -> str:
    """
    Detect language from incoming WhatsApp message text.
    Returns language code: en, fr, ar, darija
    """
    if not text:
        return DEFAULT_LANGUAGE

    # Arabic script is unambiguous
    if _LANG_PATTERNS["ar"].search(text):
        return "ar"

    # Darija / Arabizi before French (has overlap)
    if _LANG_PATTERNS["darija"].search(text):
        return "darija"

    if _LANG_PATTERNS["fr"].search(text):
        return "fr"

    if _LANG_PATTERNS["en"].search(text):
        return "en"

    return DEFAULT_LANGUAGE
