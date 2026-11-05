import re
import unicodedata

DRIVER_FOLIO_PREFIX = "CD"
DRIVER_FOLIO_NUMBER_DIGITS = 4
_FILLER = "X"
# Particles that are not part of a name/surname for the initials ("Ana de la Cruz" -> C, not D).
_PARTICLES = frozenset({"de", "del", "la", "las", "los", "y", "e"})


def _words(text: str) -> list[str]:
    """Split into ASCII-letter-only words (accents stripped, Ñ -> N), dropping empty results."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return [w for w in (re.sub(r"[^A-Za-z]", "", part) for part in ascii_text.split()) if w]


def _significant(words: list[str]) -> list[str]:
    """Drop particles; keep the original words if nothing else would remain."""
    kept = [w for w in words if w.lower() not in _PARTICLES]
    return kept or words


def driver_initials(name: str, surnames: str) -> str:
    """Return exactly 3 uppercase letters: first given name + first and second surname.

    With a single surname the second letter is its 2nd character; missing data is padded with ``X`` so the folio
    always has the same length.
    """
    given = _significant(_words(name))
    family = _significant(_words(surnames))

    first = given[0][0] if given else _FILLER
    second = family[0][0] if family else _FILLER
    if len(family) >= 2:
        third = family[1][0]
    elif family and len(family[0]) >= 2:
        third = family[0][1]
    else:
        third = _FILLER
    return f"{first}{second}{third}".upper()


def build_driver_folio(name: str, surnames: str, number: int) -> str:
    """Compose ``CD-{III}-{NNNN}`` (11 chars; the number only grows past 9999 drivers)."""
    return f"{DRIVER_FOLIO_PREFIX}-{driver_initials(name, surnames)}-{str(number).zfill(DRIVER_FOLIO_NUMBER_DIGITS)}"
