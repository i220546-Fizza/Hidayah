"""
Parsers turn an uploaded file into plain records, or a list of readable errors.

Nothing here touches the database, and nothing here changes the text: whatever the file
holds after the field separators is kept exactly as written (only the line ending and a
leading byte-order mark are removed).
"""
import json
import re
from dataclasses import dataclass, field

MAX_BYTES = 50 * 1024 * 1024
MAX_ERRORS = 20
_PIPE_LINE = re.compile(r"^(\d+)\|(\d+)\|(.*)$", re.DOTALL)


@dataclass
class Parsed:
    records: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def error(self, line: int | None, message: str) -> None:
        if len(self.errors) < MAX_ERRORS:
            self.errors.append(f"line {line}: {message}" if line else message)
        elif len(self.errors) == MAX_ERRORS:
            self.errors.append("more errors not shown")


def decode(raw: bytes) -> str:
    if len(raw) > MAX_BYTES:
        raise ValueError("The file is larger than 50 MB.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"The file is not valid UTF-8 text (byte {exc.start}).") from None
    return text[1:] if text.startswith("﻿") else text


def _lines(text: str):
    for number, line in enumerate(text.split("\n"), start=1):
        yield number, line.rstrip("\r")


def parse_verse_lines(text: str) -> Parsed:
    """`surah|verse|text` per line, with `#` comment lines (the layout used by Tanzil files)."""
    out = Parsed()
    seen: set[tuple[int, int]] = set()
    for n, line in _lines(text):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _PIPE_LINE.match(line)
        if not m:
            out.error(n, "expected 'surah|verse|text'")
            continue
        surah, verse, body = int(m.group(1)), int(m.group(2)), m.group(3)
        if not 1 <= surah <= 114:
            out.error(n, f"surah {surah} is outside 1-114")
        elif verse < 1:
            out.error(n, "verse number must be 1 or more")
        elif not body.strip():
            out.error(n, "the text is empty")
        elif (surah, verse) in seen:
            out.error(n, f"{surah}:{verse} appears twice")
        else:
            seen.add((surah, verse))
            out.records.append({"surah_number": surah, "verse_number": verse, "text": body})
    if not out.records and not out.errors:
        out.error(None, "the file contains no verses")
    return out


def _json_lines(text: str, required: tuple[str, ...], optional: tuple[str, ...]) -> Parsed:
    out = Parsed()
    allowed = set(required) | set(optional)
    for n, line in _lines(text):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            out.error(n, "not valid JSON")
            continue
        if not isinstance(obj, dict):
            out.error(n, "each line must be a JSON object")
            continue
        missing = [k for k in required if not isinstance(obj.get(k), (str, int)) or str(obj.get(k)).strip() == ""]
        unknown = sorted(set(obj) - allowed)
        if missing:
            out.error(n, f"missing or empty: {', '.join(missing)}")
        elif unknown:
            out.error(n, f"unknown fields: {', '.join(unknown)}")
        else:
            out.records.append({k: obj.get(k) for k in allowed if k in obj})
    if not out.records and not out.errors:
        out.error(None, "the file contains no records")
    return out


def parse_surahs(text: str) -> Parsed:
    out = Parsed()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        out.error(None, "not valid JSON (expected a list of surahs)")
        return out
    if not isinstance(data, list) or not data:
        out.error(None, "expected a non-empty JSON list")
        return out
    seen: set[int] = set()
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            out.error(None, f"entry {i} is not an object")
            continue
        number, count = item.get("number"), item.get("verse_count")
        if not isinstance(number, int) or not 1 <= number <= 114:
            out.error(None, f"entry {i}: number must be 1-114")
        elif number in seen:
            out.error(None, f"entry {i}: surah {number} appears twice")
        elif not isinstance(count, int) or count < 1:
            out.error(None, f"entry {i}: verse_count must be 1 or more")
        elif not item.get("name_arabic") or not item.get("name_english"):
            out.error(None, f"entry {i}: name_arabic and name_english are required")
        else:
            seen.add(number)
            out.records.append({
                "number": number, "verse_count": count, "name_arabic": item["name_arabic"],
                "name_english": item["name_english"], "name_transliterated": item.get("name_transliterated"),
            })
    return out


def parse_tafsir(text: str) -> Parsed:
    out = _json_lines(text, ("surah_number", "verse_start", "verse_end", "language", "text"), ())
    for rec in list(out.records):
        s, a, b = rec["surah_number"], rec["verse_start"], rec["verse_end"]
        if not (isinstance(s, int) and isinstance(a, int) and isinstance(b, int)) or not 1 <= s <= 114 or a < 1 or b < a:
            out.records.remove(rec)
            out.error(None, f"invalid verse range {s}:{a}-{b}")
    return out


HADITH_REQUIRED = ("hadith_number",)
HADITH_OPTIONAL = ("book_number", "book_name", "arabic_text", "translation_text", "translation_language", "narrator")


def parse_hadith(text: str) -> Parsed:
    out = _json_lines(text, HADITH_REQUIRED, HADITH_OPTIONAL)
    seen: set[str] = set()
    for rec in list(out.records):
        rec["hadith_number"] = str(rec["hadith_number"])
        if not rec.get("arabic_text") and not rec.get("translation_text"):
            out.records.remove(rec)
            out.error(None, f"hadith {rec['hadith_number']} has neither Arabic nor translation text")
        elif rec.get("translation_text") and not rec.get("translation_language"):
            out.records.remove(rec)
            out.error(None, f"hadith {rec['hadith_number']} has a translation but no translation_language")
        elif rec["hadith_number"] in seen:
            out.records.remove(rec)
            out.error(None, f"hadith number {rec['hadith_number']} appears twice")
        else:
            seen.add(rec["hadith_number"])
            for k in ("book_number",):
                if rec.get(k) is not None:
                    rec[k] = str(rec[k])
    return out


DUA_REQUIRED = ("category_slug", "category_name_english", "title", "arabic_text", "reference_text")
DUA_OPTIONAL = ("transliteration", "translation_text", "translation_language")


def parse_duas(text: str) -> Parsed:
    """Imported duas are always 'sourced', so each one must carry its reference."""
    out = _json_lines(text, DUA_REQUIRED, DUA_OPTIONAL)
    for rec in list(out.records):
        if rec.get("translation_text") and not rec.get("translation_language"):
            out.records.remove(rec)
            out.error(None, f"dua '{rec['title']}' has a translation but no translation_language")
    return out
