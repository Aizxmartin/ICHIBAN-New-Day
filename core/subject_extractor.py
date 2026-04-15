from __future__ import annotations

import io
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None


CANONICAL_FIELDS = {
    "address": None,
    "apn": None,
    "property_type": None,
    "style": None,
    "year_built": None,
    "beds": None,
    "full_baths": None,
    "half_baths": None,
    "above_grade_sqft": None,
    "total_sqft": None,
    "basement_total_sqft": None,
    "basement_finished_sqft": None,
    "basement_unfinished_sqft": None,
    "lot_sqft": None,
    "zoning": None,
    "last_sale_price": None,
    "last_sale_date": None,
    "realist_avm": None,
    "realist_avm_low": None,
    "realist_avm_high": None,
    "assessed_total_value": None,
}

ADDRESS_PATTERN = re.compile(
    r"\d{3,6}\s+[A-Za-z0-9.#'\- ]+?\b(?:Ave|Avenue|St|Street|Dr|Drive|Ct|Court|Ln|Lane|Rd|Road|Blvd|Boulevard|Cir|Circle|Way|Pl|Place|Ter|Terrace|Pkwy|Parkway)\b(?:[A-Za-z0-9.#'\-, ]*)",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")
MONEY_PATTERN = re.compile(r"[$]?\d[\d,]*")
INT_PATTERN = re.compile(r"\d[\d,]*")
RANGE_PATTERN = re.compile(r"([$]?\d[\d,]*)\s*(?:-|to)\s*([$]?\d[\d,]*)", re.IGNORECASE)


def _clean_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\x00": " ",
        "\u2122": " ",
        "\u00ae": " ",
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _normalize_int(value: str) -> Optional[int]:
    cleaned = re.sub(r"[^0-9]", "", value or "")
    return int(cleaned) if cleaned else None


def _normalize_string(value: str) -> Optional[str]:
    value = _collapse_ws(value)
    return value if value else None


def _extract_pdf_text(pdf_bytes: bytes) -> Dict[str, Any]:
    pages: List[Dict[str, Any]] = []

    if fitz is not None:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for idx, page in enumerate(doc):
                text = _clean_text(page.get_text("text") or "")
                pages.append({"page_num": idx + 1, "text": text, "method": "pymupdf"})
        except Exception:
            pages = []

    if not any(p["text"] for p in pages) and pdfplumber is not None:
        try:
            pages = []
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    text = _clean_text(page.extract_text() or "")
                    pages.append({"page_num": idx + 1, "text": text, "method": "pdfplumber"})
        except Exception:
            pages = []

    full_text = "\n\n".join(page["text"] for page in pages if page["text"])
    return {
        "pages": pages,
        "page_count": len(pages),
        "full_text": full_text,
        "has_extractable_text": bool(full_text.strip()),
        "extraction_method": pages[0]["method"] if pages else None,
    }


def _extract_address(text: str) -> Optional[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:30]:
        match = ADDRESS_PATTERN.search(line)
        if match:
            return _normalize_string(match.group(0))
    match = ADDRESS_PATTERN.search(_collapse_ws(text))
    return _normalize_string(match.group(0)) if match else None


def _find_line_value(lines: List[str], labels: Iterable[str], *, max_lookahead: int = 3) -> Optional[Tuple[str, int, str]]:
    for idx, line in enumerate(lines):
        low = line.lower().strip()
        for label in labels:
            if low == label.lower() or low.startswith(label.lower() + ":"):
                for step in range(1, max_lookahead + 1):
                    if idx + step >= len(lines):
                        break
                    candidate = lines[idx + step].strip()
                    if not candidate:
                        continue
                    # Skip obvious subsequent labels.
                    if candidate.endswith(":") or candidate.lower() in {l.lower() for l in labels}:
                        continue
                    return candidate, idx, label
    return None


def _find_line_value_regex(lines: List[str], patterns: Iterable[str], *, max_lookahead: int = 3) -> Optional[Tuple[str, int, str]]:
    compiled = [(p, re.compile(p, re.IGNORECASE)) for p in patterns]
    known_labels = {
        "beds", "full baths", "half baths", "sale price", "sale date", "bldg sq ft", "lot sq ft", "yr built", "type",
        "realavm", "realavm range", "zoning", "year built", "bedrooms", "baths - total", "mls total baths",
        "heat type", "garage type", "construction", "exterior", "foundation", "pool", "water", "sewer", "quality",
        "other impvs", "equipment", "feature type", "building description", "building size"
    }
    for idx, line in enumerate(lines):
        stripped = line.strip()
        for raw, pat in compiled:
            if pat.fullmatch(stripped) or pat.search(stripped):
                same_line = re.sub(pat, "", stripped, count=1).strip(" :-")
                if same_line:
                    return same_line, idx, raw
                for step in range(1, max_lookahead + 1):
                    if idx + step >= len(lines):
                        break
                    candidate = lines[idx + step].strip()
                    if not candidate:
                        continue
                    if len(candidate) < 50 and candidate.lower() in known_labels:
                        continue
                    return candidate, idx, raw
    return None


def _parse_money(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    match = MONEY_PATTERN.search(value)
    return _normalize_int(match.group(0)) if match else None


def _parse_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    upper = value.strip().upper()
    if upper in {"N/A", "NA", "NONE", "NULL"}:
        return None
    match = INT_PATTERN.search(value)
    return _normalize_int(match.group(0)) if match else None


def _parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    match = DATE_PATTERN.search(value)
    return match.group(0) if match else None


def _parse_range(value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not value:
        return None, None
    match = RANGE_PATTERN.search(value)
    if not match:
        return None, None
    return _normalize_int(match.group(1)), _normalize_int(match.group(2))


def _add_source(field_sources: Dict[str, Dict[str, Any]], field: str, page_num: Optional[int], label: str, method: Optional[str]) -> None:
    field_sources[field] = {"page": page_num, "label": label, "method": method}


def _looks_like_label(value: Optional[str]) -> bool:
    if not value:
        return False
    return value.strip().lower() in {
        "heat type", "garage type", "construction", "exterior", "foundation", "pool", "water", "sewer", "quality",
        "other impvs", "equipment", "feature type", "building description", "building size", "hot water"
    }


def _derive_fields(subject: Dict[str, Any], data_issues: List[str]) -> None:
    total_sqft = subject.get("total_sqft")
    basement_total = subject.get("basement_total_sqft")
    basement_finished = subject.get("basement_finished_sqft")

    if subject.get("above_grade_sqft") is None:
        if total_sqft and basement_total and total_sqft >= basement_total:
            subject["above_grade_sqft"] = total_sqft - basement_total
            data_issues.append("Above-grade square footage was inferred from total square footage minus basement square footage.")
        elif total_sqft and not basement_total:
            subject["above_grade_sqft"] = total_sqft
            data_issues.append("Above-grade square footage was not clearly identified; total square footage was used as a provisional substitute.")

    if subject.get("basement_unfinished_sqft") is None and basement_total is not None and basement_finished is not None and basement_total >= basement_finished:
        subject["basement_unfinished_sqft"] = basement_total - basement_finished


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def build_subject_profile(pdf_bytes: bytes) -> Dict[str, Any]:
    extraction = _extract_pdf_text(pdf_bytes)
    pages = extraction["pages"]
    full_text = extraction["full_text"]

    subject = dict(CANONICAL_FIELDS)
    field_sources: Dict[str, Dict[str, Any]] = {}
    data_issues: List[str] = []

    if not extraction["has_extractable_text"]:
        data_issues.append("This PDF appears to be image-based or text extraction failed. Manual verification may be required.")

    if full_text:
        address = _extract_address(full_text)
        if address:
            subject["address"] = address
            _add_source(field_sources, "address", 1, "address pattern", extraction["extraction_method"])

    for page in pages:
        lines = [ln.strip() for ln in page["text"].splitlines() if ln.strip()]
        if not lines:
            continue
        method = page.get("method")
        page_num = page["page_num"]

        mappings = {
            "apn": ([r"APN", r"parcel\s*id", r"schedule\s*number", r"PIN"], _normalize_string),
            "year_built": ([r"Yr\s*Built", r"Year\s*Built"], _parse_int),
            "beds": ([r"Beds", r"Bedrooms", r"Bedrooms\s*Total"], _parse_int),
            "full_baths": ([r"Full\s*Baths", r"Baths\s*-\s*Full"], _parse_int),
            "half_baths": ([r"Half\s*Baths", r"Baths\s*-\s*Half"], _parse_int),
            "total_sqft": ([r"Bldg\s*Sq\s*Ft", r"Bldg\s*Sq\s*Ft\s*-\s*Finished", r"Building\s*Size", r"Living\s*Area"], _parse_int),
            "above_grade_sqft": ([r"Bldg\s*Sq\s*Ft\s*-\s*Above\s*Ground", r"Above\s*Grade\s*Finished\s*Area", r"Above\s*Grade\s*SF"], _parse_int),
            "basement_total_sqft": ([r"Bldg\s*Sq\s*Ft\s*-\s*Basement", r"Basement\s*Sq\s*Ft"], _parse_int),
            "basement_finished_sqft": ([r"Bldg\s*Sq\s*Ft\s*-\s*Finished\s*Basement", r"Finished\s*Basement"], _parse_int),
            "basement_unfinished_sqft": ([r"Bldg\s*Sq\s*Ft\s*-\s*Unfinished\s*Basement", r"Unfinished\s*Basement"], _parse_int),
            "lot_sqft": ([r"Lot\s*Sq\s*Ft", r"Lot\s*Size"], _parse_int),
            "last_sale_price": ([r"Sale\s*Price"], _parse_money),
            "last_sale_date": ([r"Sale\s*Date"], _parse_date),
            "realist_avm": ([r"RealAVM", r"Real\s*AVM", r"Estimated\s*Value"], _parse_money),
            "assessed_total_value": ([r"Assessed\s*Value\s*-\s*Total", r"Actual\s*Value", r"Market\s*Value\s*-\s*Total"], _parse_money),
        }

        for field, (patterns, parser) in mappings.items():
            if subject[field] is not None:
                continue
            found = _find_line_value_regex(lines, patterns)
            if not found:
                continue
            raw_value, _, label = found
            value = parser(raw_value)
            if value is None:
                continue
            subject[field] = value
            _add_source(field_sources, field, page_num, label, method)

        if subject["realist_avm_low"] is None or subject["realist_avm_high"] is None:
            found = _find_line_value_regex(lines, [r"RealAVM\s*Range", r"Real\s*AVM\s*Range", r"Value\s*Range"])
            if found:
                raw_value, _, label = found
                low, high = _parse_range(raw_value)
                if low is not None and subject["realist_avm_low"] is None:
                    subject["realist_avm_low"] = low
                    _add_source(field_sources, "realist_avm_low", page_num, label, method)
                if high is not None and subject["realist_avm_high"] is None:
                    subject["realist_avm_high"] = high
                    _add_source(field_sources, "realist_avm_high", page_num, label, method)

        if subject["property_type"] is None:
            found = _find_line_value_regex(lines, [r"^Type$", r"Land\s*Use\s*-\s*County", r"Land\s*Use\s*-\s*CoreLogic", r"Class"])
            if found:
                raw_value, _, label = found
                value = _normalize_string(raw_value)
                if value and len(value) <= 40:
                    subject["property_type"] = value
                    _add_source(field_sources, "property_type", page_num, label, method)

        if subject["style"] is None:
            found = _find_line_value_regex(lines, [r"^Style$"])
            if found:
                raw_value, _, label = found
                value = _normalize_string(raw_value)
                if value and len(value) <= 40 and not _looks_like_label(value):
                    subject["style"] = value
                    _add_source(field_sources, "style", page_num, label, method)

        if subject["zoning"] is None:
            found = _find_line_value_regex(lines, [r"Zoning"])
            if found:
                raw_value, _, label = found
                value = _normalize_string(raw_value)
                if value:
                    subject["zoning"] = value
                    _add_source(field_sources, "zoning", page_num, label, method)

    _derive_fields(subject, data_issues)

    required_notes = {
        "address": "Subject address could not be confidently identified from the property report.",
        "above_grade_sqft": "Above-grade square footage could not be clearly confirmed from the property report.",
        "year_built": "Year built was not found in the property report.",
        "beds": "Bedroom count was not found in the property report.",
        "full_baths": "Full bath count was not found in the property report.",
        "realist_avm": "A reliable AVM value was not found in the property report.",
        "realist_avm_low": "An AVM low range value was not found in the property report.",
        "realist_avm_high": "An AVM high range value was not found in the property report.",
        "basement_total_sqft": "Basement information was not found in the property report.",
    }
    for field, message in required_notes.items():
        if subject.get(field) in (None, ""):
            data_issues.append(message)

    if subject.get("property_type") is None:
        data_issues.append("Property type was not clearly identified in the property report.")

    return {
        "source": "subject_property_pdf",
        "subject_property": subject,
        "data_issues": _dedupe(data_issues),
        "field_sources": field_sources,
        "document_meta": {
            "page_count": extraction["page_count"],
            "has_extractable_text": extraction["has_extractable_text"],
            "extraction_method": extraction.get("extraction_method"),
        },
        "debug": {
            "extracted_text_preview": full_text[:8000] if full_text else "",
        },
    }


def extract_subject_property(pdf_bytes: bytes, filename: str | None = None) -> Dict[str, Any]:
    """Compatibility wrapper for Module 2 page import."""
    result = build_subject_profile(pdf_bytes)
    if filename:
        result.setdefault("document_meta", {})
        result["document_meta"]["filename"] = filename
    # Keep top-level preview key expected by newer page
    debug = result.get("debug", {}) or {}
    if "raw_text_preview" not in result:
        result["raw_text_preview"] = debug.get("extracted_text_preview", "")
    return result
