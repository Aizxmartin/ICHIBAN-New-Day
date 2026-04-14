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
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


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


def _extract_currency_after_label(text: str, labels: list[str]) -> Tuple[Optional[float], Optional[str]]:
    for label in labels:
        pattern = rf"{label}[^$\n\r]*([$]?[\d,]+(?:\.\d{{1,2}})?)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1)
            return _normalize_currency(raw), raw
    return None, None


def _extract_range(text: str, labels: list[str]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    for label in labels:
        pattern = rf"{label}[^\n\r]*?([$]?[\d,]+)\s*(?:-|–|—|to)\s*([$]?[\d,]+)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            low_raw, high_raw = match.group(1), match.group(2)
            return _normalize_currency(low_raw), _normalize_currency(high_raw), f"{low_raw} - {high_raw}"
    return None, None, None


def _extract_int_after_label(text: str, labels: list[str]) -> Optional[int]:
    for label in labels:
        pattern = rf"{label}[^\d\n\r]*([\d,]+)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return None


def _extract_float_after_label(text: str, labels: list[str]) -> Optional[float]:
    for label in labels:
        pattern = rf"{label}[^\d\n\r]*([\d]+(?:\.\d+)?)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def _extract_address(text: str) -> Optional[str]:
    address_patterns = [
        r"(\d{3,6}\s+[A-Za-z0-9.#'\- ]+\s(?:Ave|Avenue|St|Street|Dr|Drive|Ct|Court|Ln|Lane|Rd|Road|Blvd|Boulevard|Cir|Circle|Way|Pl|Place|Ter|Terrace|Pkwy|Parkway)\b(?:[\w\s.#\-]*)?)",
        r"Property Address[^\n\r:]*[:\s]+(.+)",
        r"Subject Address[^\n\r:]*[:\s]+(.+)",
        r"Address[^\n\r:]*[:\s]+(.+)",
    ]
    for pattern in address_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            address = re.sub(r"\s{2,}", " ", address)
            address = address.split("\n")[0].strip(" :-")
            if len(address) >= 8:
                return address
    return None


def build_subject_profile(pdf_bytes: bytes) -> Dict[str, Any]:
    text = extract_text_from_pdf_bytes(pdf_bytes)

    real_avm, real_avm_raw = _extract_currency_after_label(
        text,
        labels=[r"Real\s*AVM", r"RealAVM", r"Estimated\s+Value", r"Estimated\s+Subject\s+Value"],
    )

    real_avm_low, real_avm_high, real_avm_range_raw = _extract_range(
        text,
        labels=[r"Real\s*AVM\s*Range", r"RealAVM\s*Range", r"Value\s*Range", r"Estimated\s+Value\s*Range"],
    )

    above_grade_sqft = _extract_int_after_label(
        text,
        labels=[r"Above\s+Grade\s+Finished\s+Area", r"Above\s+Grade\s+SF", r"Living\s+Area", r"GLA", r"Finished\s+Area"],
    )
    beds = _extract_float_after_label(text, labels=[r"Bedrooms", r"Beds", r"Bedrooms\s+Total"])
    baths = _extract_float_after_label(text, labels=[r"Bathrooms", r"Baths", r"Bathrooms\s+Total", r"Baths\s+Total"])
    year_built = _extract_int_after_label(text, labels=[r"Year\s+Built", r"Built\s+in"])
    lot_size_sqft = _extract_int_after_label(text, labels=[r"Lot\s+Size", r"Lot\s+Sq\.?\s*Ft\.?", r"Site\s+Area"])
    address = _extract_address(text)

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
        "extracted_text_available": bool(text),
        "extracted_text_preview": text[:2500] if text else "",
    }
