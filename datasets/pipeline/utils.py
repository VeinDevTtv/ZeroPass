import unicodedata


def normalize(s: str) -> str:
    return unicodedata.normalize("NFC", s).strip()


