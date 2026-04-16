from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


PREFERRED_HEADER_KEYWORDS = [
    "close price",
    "above grade",
    "address",
    "street",
    "listing id",
    "status",
    "bed",
    "bath",
    "concess",
    "sold date",
    "closed date",
]

REQUIRED_COMP_COLUMN_GROUPS = {
    "price": ["close price", "sold price", "closed price"],
    "sqft": ["above grade", "above-grade", "building area", "finished area"],
    "address": ["address", "street name", "property address"],
}


def _clean_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _read_raw_market_data(file_bytes: bytes, filename: str, header: Optional[int]) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    file_obj = io.BytesIO(file_bytes)
    if suffix == ".csv":
        return pd.read_csv(file_obj, header=header)
    if suffix == ".xlsx":
        return pd.read_excel(file_obj, header=header)
    raise ValueError("Unsupported market data file type. Please upload a CSV or XLSX file.")


def _score_header_labels(labels: List[str]) -> int:
    score = 0
    lowered = [str(x).strip().lower() for x in labels]
    for label in lowered:
        if not label:
            continue
        if not label.startswith("unnamed"):
            score += 1
        for keyword in PREFERRED_HEADER_KEYWORDS:
            if keyword in label:
                score += 3
    return score


def load_market_data_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    candidates = []
    for header in [0, 1, 2, 3]:
        try:
            df = _read_raw_market_data(file_bytes, filename, header=header)
        except Exception:
            continue
        labels = [str(c) for c in df.columns]
        candidates.append((_score_header_labels(labels), header, df))

    if not candidates:
        raise ValueError("Market data file could not be read.")

    candidates.sort(key=lambda x: (x[0], -len(x[2].columns)), reverse=True)
    return candidates[0][2]


def normalize_market_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(c).strip() for c in cleaned.columns]

    unnamed_cols = [c for c in cleaned.columns if str(c).strip().lower().startswith("unnamed")]
    if len(unnamed_cols) >= max(1, len(cleaned.columns) // 2) and len(cleaned) > 0:
        first_row = [str(v).strip() for v in cleaned.iloc[0].tolist()]
        if _score_header_labels(first_row) > _score_header_labels(list(cleaned.columns)):
            cleaned.columns = first_row
            cleaned = cleaned.iloc[1:].reset_index(drop=True)

    cleaned.columns = [str(c).strip() for c in cleaned.columns]
    drop_cols = [c for c in cleaned.columns if str(c).strip().lower() in {"unnamed: 0", ""}]
    if drop_cols:
        cleaned = cleaned.drop(columns=drop_cols, errors="ignore")

    return cleaned


def derive_online_estimate_inputs(
    subject_property: Dict[str, Any],
    zillow_value: Any = None,
    redfin_value: Any = None,
) -> Dict[str, Optional[float]]:
    return {
        "realist_avm": _clean_number(subject_property.get("realist_avm")),
        "zillow": _clean_number(zillow_value),
        "redfin": _clean_number(redfin_value),
    }


def _has_address(subject_property: Dict[str, Any]) -> bool:
    address = subject_property.get("address")
    return bool(address and str(address).strip())


def _has_usable_square_footage(subject_property: Dict[str, Any]) -> bool:
    for key in ("above_grade_sqft", "total_sqft"):
        value = subject_property.get(key)
        if value not in (None, "", 0):
            return True
    return False


def _has_property_type(subject_property: Dict[str, Any]) -> bool:
    value = subject_property.get("property_type")
    return bool(value and str(value).strip())


def _has_online_support(online_inputs: Dict[str, Optional[float]]) -> bool:
    return any(v is not None for v in online_inputs.values())


def _market_data_ready(df: Optional[pd.DataFrame]) -> bool:
    return df is not None and not df.empty


def _market_headers_usable(df: Optional[pd.DataFrame]) -> bool:
    if df is None or df.empty:
        return False
    labels = [str(c).strip() for c in df.columns]
    if not labels:
        return False
    unnamed_count = sum(1 for c in labels if c.lower().startswith("unnamed"))
    if unnamed_count >= max(1, len(labels) // 2):
        return False
    return _score_header_labels(labels) > 3


def _missing_required_comp_groups(df: Optional[pd.DataFrame]) -> List[str]:
    if df is None or df.empty:
        return list(REQUIRED_COMP_COLUMN_GROUPS.keys())
    labels = [str(c).strip().lower() for c in df.columns]
    missing = []
    for group, options in REQUIRED_COMP_COLUMN_GROUPS.items():
        found = any(any(opt in label for opt in options) for label in labels)
        if not found:
            missing.append(group)
    return missing


def evaluate_readiness(
    subject_property: Dict[str, Any],
    data_issues: List[str],
    market_df: Optional[pd.DataFrame],
    zillow_value: Any = None,
    redfin_value: Any = None,
) -> Dict[str, Any]:
    online_inputs = derive_online_estimate_inputs(subject_property, zillow_value, redfin_value)

    address_ready = _has_address(subject_property)
    sqft_ready = _has_usable_square_footage(subject_property)
    property_type_ready = _has_property_type(subject_property)
    comps_loaded = _market_data_ready(market_df)
    headers_usable = _market_headers_usable(market_df)
    missing_comp_groups = _missing_required_comp_groups(market_df)
    comps_ready = comps_loaded and headers_usable and not missing_comp_groups
    online_ready = _has_online_support(online_inputs)

    limitations: List[str] = []
    if not address_ready:
        limitations.append("Subject address could not be confidently identified.")
    if not sqft_ready:
        limitations.append("Usable subject square footage could not be confidently identified.")
    if not property_type_ready:
        limitations.append("Property type could not be clearly identified.")
    if not comps_loaded:
        limitations.append("MLS market data is missing or empty.")
    if comps_loaded and not headers_usable:
        limitations.append("MLS market data headers could not be normalized into usable field names.")
    if missing_comp_groups:
        limitations.append(
            "MLS market data is missing required comp fields: " + ", ".join(missing_comp_groups) + "."
        )
    if not online_ready:
        limitations.append("No AVM, Zillow, or Redfin support value is available.")

    if address_ready and sqft_ready and property_type_ready and comps_ready:
        status = "full_report_ready"
        next_step = "comp_filtering"
    elif address_ready and comps_loaded and online_ready:
        status = "limited_scope_only"
        next_step = "limited_scope_valuation"
    else:
        status = "insufficient_data"
        next_step = "stop"

    return {
        "status": status,
        "subject_ready": address_ready and sqft_ready and property_type_ready,
        "comps_ready": comps_ready,
        "comps_loaded": comps_loaded,
        "market_headers_usable": headers_usable,
        "missing_comp_field_groups": missing_comp_groups,
        "online_estimate_available": online_ready,
        "address_ready": address_ready,
        "square_footage_ready": sqft_ready,
        "property_type_ready": property_type_ready,
        "limitations": _dedupe_strings(list(data_issues) + limitations),
        "next_step": next_step,
        "online_estimate_inputs": online_inputs,
        "market_data_summary": summarize_market_dataframe(market_df),
    }


def summarize_market_dataframe(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if df is None:
        return {"loaded": False, "rows": 0, "columns": 0, "column_names": []}
    return {
        "loaded": True,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(c) for c in df.columns],
    }


def _dedupe_strings(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        key = str(item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(str(item).strip())
    return out
