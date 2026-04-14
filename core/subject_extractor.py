import io
import re
from typing import Any, Dict, Optional, Tuple

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


def _clean_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\x00": " ",
        "\u2122": " ",  # ™
        "\u00ae": " ",  # ®
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u00a0": " ",  # nbsp
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _collapse_ws(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    if not pdf_bytes or PdfReader is None:
        return ""

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        return _clean_text("\n".join(pages))
    except Exception:
        return ""


def _normalize_currency(value: str) -> Optional[float]:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_int(value: str) -> Optional[int]:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9]", "", value)
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _normalize_float(value: str) -> Optional[float]:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _search_currency_near_label(text: str, labels: list[str], lookahead: int = 120) -> Tuple[Optional[float], Optional[str]]:
    for label in labels:
        for match in re.finditer(label, text, flags=re.IGNORECASE):
            start = match.end()
            snippet = text[start:start + lookahead]
            money = re.search(r"[$]?\d[\d,]*", snippet)
            if money:
                raw = money.group(0)
                return _normalize_currency(raw), raw
    return None, None


def _search_range_near_label(text: str, labels: list[str], lookahead: int = 160) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    for label in labels:
        for match in re.finditer(label, text, flags=re.IGNORECASE):
            start = match.end()
            snippet = text[start:start + lookahead]
            rng = re.search(r"([$]?\d[\d,]*)\s*(?:-|to)\s*([$]?\d[\d,]*)", snippet, flags=re.IGNORECASE)
            if rng:
                low_raw, high_raw = rng.group(1), rng.group(2)
                return _normalize_currency(low_raw), _normalize_currency(high_raw), f"{low_raw} - {high_raw}"
    return None, None, None


def _search_number_near_label(text: str, labels: list[str], as_float: bool = False, lookahead: int = 60):
    for label in labels:
        for match in re.finditer(label, text, flags=re.IGNORECASE):
            start = match.end()
            snippet = text[start:start + lookahead]
            num = re.search(r"([\d,]+(?:\.\d+)?)", snippet)
            if num:
                raw = num.group(1)
                return _normalize_float(raw) if as_float else _normalize_int(raw)
    return None


def _extract_address(text: str) -> Optional[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:20]:
        if re.search(
            r"\d{3,6}\s+.+\b(?:Ave|Avenue|St|Street|Dr|Drive|Ct|Court|Ln|Lane|Rd|Road|Blvd|Boulevard|Cir|Circle|Way|Pl|Place|Ter|Terrace|Pkwy|Parkway)\b",
            line,
            flags=re.IGNORECASE,
        ):
            return re.sub(r"\s{2,}", " ", line)

    collapsed = _collapse_ws(text)
    match = re.search(
        r"(\d{3,6}\s+[A-Za-z0-9.#'\- ]+?\b(?:Ave|Avenue|St|Street|Dr|Drive|Ct|Court|Ln|Lane|Rd|Road|Blvd|Boulevard|Cir|Circle|Way|Pl|Place|Ter|Terrace|Pkwy|Parkway)\b(?:[A-Za-z0-9.#'\- ]*)?)",
        collapsed,
        flags=re.IGNORECASE,
    )
    if match:
        return re.sub(r"\s{2,}", " ", match.group(1).strip())
    return None


def _sum_floor_area(text: str) -> Optional[int]:
    first_floor = _search_number_near_label(
        text,
        [r"Bldg\s*Sq\s*Ft\s*-\s*1st\s*Floor", r"Building\s*Sq\s*Ft\s*-\s*1st\s*Floor", r"1st\s*Floor"],
    )
    second_floor = _search_number_near_label(
        text,
        [r"Bldg\s*Sq\s*Ft\s*-\s*2nd\s*Floor", r"Building\s*Sq\s*Ft\s*-\s*2nd\s*Floor", r"2nd\s*Floor"],
    )
    if first_floor is not None or second_floor is not None:
        return int((first_floor or 0) + (second_floor or 0))
    return None


def build_subject_profile(pdf_bytes: bytes) -> Dict[str, Any]:
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    collapsed = _collapse_ws(raw_text)

    search_spaces = [collapsed, raw_text]

    real_avm = None
    real_avm_raw = None
    for space in search_spaces:
        real_avm, real_avm_raw = _search_currency_near_label(
            space,
            labels=[
                r"Real\s*AVM",
                r"RealAVM",
                r"Estimated\s*Value",
                r"Estimated\s*Subject\s*Value",
            ],
        )
        if real_avm is not None:
            break

    real_avm_low = None
    real_avm_high = None
    real_avm_range_raw = None
    for space in search_spaces:
        real_avm_low, real_avm_high, real_avm_range_raw = _search_range_near_label(
            space,
            labels=[
                r"Real\s*AVM\s*Range",
                r"RealAVM\s*Range",
                r"Value\s*Range",
                r"Estimated\s*Value\s*Range",
            ],
        )
        if real_avm_range_raw is not None:
            break

    address = _extract_address(raw_text)

    above_grade_sqft = None
    for space in search_spaces:
        above_grade_sqft = _search_number_near_label(
            space,
            labels=[
                r"Above\s*Grade\s*Finished\s*Area",
                r"Above\s*Grade\s*SF",
                r"Living\s*Area",
                r"GLA",
                r"Finished\s*Area",
                r"Bldg\s*Sq\s*Ft",
                r"Building\s*Size",
            ],
            as_float=False,
        )
        if above_grade_sqft is not None:
            break
    if above_grade_sqft is None:
        above_grade_sqft = _sum_floor_area(collapsed)

    beds = None
    for space in search_spaces:
        beds = _search_number_near_label(
            space,
            labels=[
                r"MLS\s*Beds",
                r"Bedrooms",
                r"Beds",
                r"Bedrooms\s*Total",
            ],
            as_float=True,
        )
        if beds is not None:
            break

    baths = None
    for space in search_spaces:
        baths = _search_number_near_label(
            space,
            labels=[
                r"MLS\s*Total\s*Baths",
                r"MLS\s*-\s*Total\s*Baths",
                r"Baths\s*-\s*Total",
                r"Bathrooms",
                r"Baths",
                r"Bathrooms\s*Total",
                r"Baths\s*Total",
            ],
            as_float=True,
        )
        if baths is not None:
            break

    year_built = None
    for space in search_spaces:
        year_built = _search_number_near_label(space, [r"Year\s*Built", r"Built\s*in"], as_float=False)
        if year_built is not None:
            break

    lot_size_sqft = None
    for space in search_spaces:
        lot_size_sqft = _search_number_near_label(
            space,
            labels=[r"Lot\s*Size", r"Lot\s*Sq\.?\s*Ft\.?", r"Site\s*Area"],
            as_float=False,
        )
        if lot_size_sqft is not None:
            break

    warnings = []
    if not raw_text:
        warnings.append("No extractable PDF text was found.")
    if real_avm is None:
        warnings.append("RealAVM was not found in the PDF.")
    if real_avm_range_raw is None:
        warnings.append("RealAVM Range was not found in the PDF.")
    if address is None:
        warnings.append("Subject address was not found in the PDF.")
    if beds is None:
        warnings.append("Bed count was not found in the PDF.")
    if baths is None:
        warnings.append("Bath count was not found in the PDF.")
    if above_grade_sqft is None:
        warnings.append("Above-grade square footage was not found in the PDF.")

    return {
        "source": "subject_property_pdf",
        "subject_address": address,
        "real_avm": real_avm,
        "real_avm_raw": real_avm_raw,
        "real_avm_range_low": real_avm_low,
        "real_avm_range_high": real_avm_high,
        "real_avm_range_raw": real_avm_range_raw,
        "above_grade_sqft": above_grade_sqft,
        "beds": beds,
        "baths": baths,
        "year_built": year_built,
        "lot_size_sqft": lot_size_sqft,
        "extracted_text_available": bool(raw_text),
        "extracted_text_preview": raw_text[:5000] if raw_text else "",
        "warnings": warnings,
    }
