from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


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


def load_market_data_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    file_obj = io.BytesIO(file_bytes)
    if suffix == ".csv":
        return pd.read_csv(file_obj)
    if suffix == ".xlsx":
        return pd.read_excel(file_obj)
    raise ValueError("Unsupported market data file type. Please upload a CSV or XLSX file.")


def normalize_market_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(c).strip() for c in cleaned.columns]
    if "Unnamed: 0" in cleaned.columns:
        cleaned = cleaned.drop(columns=["Unnamed: 0"])
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
    comps_ready = _market_data_ready(market_df)
    online_ready = _has_online_support(online_inputs)

    limitations: List[str] = []
    if not address_ready:
        limitations.append("Subject address could not be confidently identified.")
    if not sqft_ready:
        limitations.append("Usable subject square footage could not be confidently identified.")
    if not property_type_ready:
        limitations.append("Property type could not be clearly identified.")
    if not comps_ready:
        limitations.append("MLS market data is missing or empty.")
    if not online_ready:
        limitations.append("No AVM, Zillow, or Redfin support value is available.")

    if address_ready and sqft_ready and property_type_ready and comps_ready:
        status = "full_report_ready"
        next_step = "comp_filtering"
    elif address_ready and comps_ready and online_ready:
        status = "limited_scope_only"
        next_step = "limited_scope_valuation"
    else:
        status = "insufficient_data"
        next_step = "stop"

    return {
        "status": status,
        "subject_ready": address_ready and sqft_ready and property_type_ready,
        "comps_ready": comps_ready,
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
