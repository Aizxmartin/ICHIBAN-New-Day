from typing import Any, Dict, List, Optional


def _coerce_range(text_value: Optional[str]):
    if not text_value:
        return None, None

    cleaned = (
        str(text_value)
        .replace('$', '')
        .replace(',', '')
        .replace('–', '-')
        .replace('—', '-')
        .replace('to', '-')
        .strip()
    )

    parts = [p.strip() for p in cleaned.split('-') if p.strip()]
    if len(parts) >= 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return None, None
    return None, None


def _average(values: List[Optional[float]]):
    usable = [float(v) for v in values if v is not None]
    if not usable:
        return None
    return round(sum(usable) / len(usable), 2)


def build_subject_profile(parsed_subject: Dict[str, Any], session_state) -> Dict[str, Any]:
    zillow_value = session_state.get('zillow_value_num')
    redfin_value = session_state.get('redfin_value_num')

    zillow_low, zillow_high = _coerce_range(session_state.get('zillow_range_text'))
    redfin_low, redfin_high = _coerce_range(session_state.get('redfin_range_text'))

    online_average = _average([
        parsed_subject.get('realavm'),
        zillow_value,
        redfin_value,
    ])

    warnings = list(parsed_subject.get('warnings', []))
    if online_average is None:
        warnings.append('No online estimate average could be calculated yet.')

    return {
        'address': parsed_subject.get('address'),
        'realavm': parsed_subject.get('realavm'),
        'realavm_low': parsed_subject.get('realavm_low'),
        'realavm_high': parsed_subject.get('realavm_high'),
        'zillow': zillow_value,
        'zillow_low': zillow_low,
        'zillow_high': zillow_high,
        'redfin': redfin_value,
        'redfin_low': redfin_low,
        'redfin_high': redfin_high,
        'online_estimate_average': online_average,
        'beds': parsed_subject.get('beds'),
        'baths': parsed_subject.get('baths'),
        'above_grade_sf': parsed_subject.get('above_grade_sf'),
        'basement_sf': parsed_subject.get('basement_sf'),
        'year_built': parsed_subject.get('year_built'),
        'lot_size': parsed_subject.get('lot_size'),
        'property_type': parsed_subject.get('property_type'),
        'warnings': warnings,
    }
