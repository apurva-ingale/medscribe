import difflib
import re

from .schemas import SECTIONS, ClinicalNote, Flag

_NUM = re.compile(r"\d+(?:\.\d+)?")


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", s.lower()).split())


def _supported(quote: str, hay: str, words: list[str]) -> bool:
    q = _norm(quote)
    if not q:
        return False
    if q in hay:
        return True
    n = len(q.split())
    if n > len(words):
        return False
    for i in range(len(words) - n + 1):
        if difflib.SequenceMatcher(None, q, " ".join(words[i : i + n])).ratio() >= 0.85:
            return True
    return False


def validate_note(note: ClinicalNote, transcript: str) -> list[Flag]:
    hay = _norm(transcript)
    words = hay.split()
    nums = set(_NUM.findall(transcript))
    flags: list[Flag] = []
    if not note.chief_complaint:
        flags.append(Flag(section="chief_complaint", index=-1, reason="No chief complaint was identified"))
    for key in SECTIONS:
        for i, item in enumerate(getattr(note, key)):
            if not item.source_quote.strip():
                flags.append(Flag(section=key, index=i, reason="No supporting quote from the transcript"))
            elif not _supported(item.source_quote, hay, words):
                flags.append(Flag(section=key, index=i, reason="Supporting quote not found in the transcript"))
            missing = [n for n in _NUM.findall(item.text) if n not in nums]
            if missing:
                flags.append(Flag(section=key, index=i, reason="Number not in transcript: " + ", ".join(missing)))
    return flags
